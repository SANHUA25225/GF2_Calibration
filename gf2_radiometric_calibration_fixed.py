# -*- coding: utf-8 -*-
"""
GF-2 多光谱影像辐射定标脚本 (修复版)

公式: Radiance = Gain * DN + Offset
Gain/Offset 优先自动读取影像配套 XML (GF-2 的系数在 <AbsCeof> 标签中)

输出格式由 DRIVER 决定:
  "GTiff" -> GeoTIFF, interleave='pixel' (即 BIP 存储组织) + LZW 压缩
  "ENVI"  -> ENVI 标准格式 (.dat + .hdr), interleave='bip'
两种格式 ENVI / ArcGIS / QGIS 都能正常读取, 差别只在硬盘上的存储组织方式。
"""
import os
import re
import xml.etree.ElementTree as ET

import numpy as np
import rasterio


def read_gf2_coeffs_from_xml(xml_path):
    """扫描 GF 系列元数据 XML, 自动提取各波段定标系数.

    兼容两种写法:
      <AbsCeof>0.1374,0.1784,0.1723,0.1894</AbsCeof>   (GF-2 常见)
      <Gain>0.1374</Gain> / <Offset>0</Offset> 逐波段   (部分产品)
    返回 (gains, offsets); XML 中没有 Offset 时返回空列表。
    """
    gains, offsets = [], []
    for elem in ET.parse(xml_path).getroot().iter():
        text = (elem.text or '').strip()
        if not text:
            continue
        tag = elem.tag.lower()
        try:
            nums = [float(v) for v in re.split(r'[,\s;]+', text)]
        except ValueError:
            continue  # 非数值标签, 例如 <GainMode>G2,G1,G1,G2</GainMode>
        if 'offset' in tag:
            offsets.extend(nums)
        elif 'gain' in tag or 'ceof' in tag or 'coefficient' in tag:
            gains.extend(nums)
    return gains, offsets


def radiometric_calibration_bip(input_path, output_path, gains, offsets=None,
                                driver='GTiff'):
    """执行辐射定标并保存 (默认 GTiff+BIP 存储, 可选 ENVI 标准 BIP)。"""
    gains = np.asarray(gains, dtype=np.float32)
    offsets = (np.zeros_like(gains) if offsets is None
               else np.asarray(offsets, dtype=np.float32))

    with rasterio.open(input_path) as src:
        if len(gains) != src.count or len(offsets) != src.count:
            raise ValueError(
                f"系数个数 (Gain {len(gains)} / Offset {len(offsets)}) 与"
                f"影像波段数 {src.count} 不一致, 请核对定标系数!")

        profile = src.profile.copy()
        profile.update(dtype='float32', driver=driver)

        if driver.upper() == 'GTIFF':
            # GTiff 的交错方式只有 BAND(按波段) / PIXEL(按像素=BIP) 两种
            profile.update(compress='lzw', interleave='pixel',
                           tiled=False, BIGTIFF='IF_SAFER')
            # 关键修复: 源影像虽非分块存储, 但 profile 带 blockxsize/
            # blockysize (条带大小), 不删掉的话写出时会报
            # "Tiled must be set to True if blockxsize..." 错误
            profile.pop('blockxsize', None)
            profile.pop('blockysize', None)
        else:
            # ENVI 标准 BIP 格式
            profile.update(interleave='bip')
            for k in ('compress', 'tiled', 'blockxsize', 'blockysize'):
                profile.pop(k, None)

        print(f"  影像: {src.width} x {src.height}, {src.count} 波段, "
              f"原始数据类型 {src.dtypes[0]}")
        dn = src.read().astype(np.float32)  # 整景读入约 0.8 GB 内存

    dn *= gains[:, None, None]
    dn += offsets[:, None, None]

    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    with rasterio.open(output_path, 'w', **profile) as dst:
        dst.write(dn)

    print(f"\n[完成] 辐射定标结果已保存: {output_path}")
    print("       交错方式: BIP (Band Interleaved by Pixel)")


def load_config_txt(script_dir):
    """读取脚本同目录的 输入配置.txt (UTF-8 或 GBK 均可), 返回 {名称: 路径}."""
    cfg_path = os.path.join(script_dir, '输入配置.txt')
    if not os.path.exists(cfg_path):
        return {}
    try:
        with open(cfg_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except UnicodeDecodeError:
        with open(cfg_path, 'r', encoding='gbk') as f:
            lines = f.readlines()
    cfg = {}
    for line in lines:
        line = line.strip()
        if not line or line.startswith('#') or '=' not in line:
            continue
        key, _, value = line.partition('=')
        value = value.strip().strip('"').strip("'")
        if value:
            cfg[key.strip().upper()] = value
    return cfg


if __name__ == "__main__":
    # ================= 配置区(默认值) =================
    # 平时换影像只需编辑同目录的 输入配置.txt, 不用改这里;
    # 若存在 输入配置.txt, 下面 3 个路径以它为准。
    INPUT_IMAGE  = (r"D:\aaaJZ\GF2_PMS1_E108.4_N23.3_20250402_L1A14547890001"
                    r"\GF2_PMS1_E108.4_N23.3_20250402_L1A14547890001-MSS1.tiff")
    OUTPUT_IMAGE = r"D:\gf2\GF2_MSS_Radiance_BIP.tif"
    XML_PATH     = (r"D:\aaaJZ\GF2_PMS1_E108.4_N23.3_20250402_L1A14547890001"
                    r"\GF2_PMS1_E108.4_N23.3_20250402_L1A14547890001-MSS1.xml")
    DRIVER       = "GTiff"   # "GTiff"=BIP 存储的 GeoTIFF; "ENVI"=标准 ENVI BIP(此时输出名建议改为 .dat)

    # 手动兜底系数 (顺序: B, G, R, NIR), 与本景影像 XML 的 AbsCeof 一致
    GAINS   = [0.1374, 0.1784, 0.1723, 0.1894]
    OFFSETS = [0.0, 0.0, 0.0, 0.0]
    # ==========================================

    cfg = load_config_txt(script_dir)
    if cfg:
        print("[配置] 检测到 输入配置.txt, 采用其中的路径")
        INPUT_IMAGE  = cfg.get('INPUT_IMAGE', '')
        XML_PATH     = cfg.get('XML_PATH', '')
        OUTPUT_IMAGE = cfg.get('OUTPUT_IMAGE', OUTPUT_IMAGE)

    gains, offsets = GAINS, OFFSETS
    if XML_PATH and os.path.exists(XML_PATH):
        xg, xo = read_gf2_coeffs_from_xml(XML_PATH)
        print(f"XML 中解析到 Gain : {xg}")
        print(f"XML 中解析到 Offset: {xo if xo else '(无, 按 0 处理)'}")
        if len(xg) == len(GAINS):
            gains = xg
            offsets = xo if len(xo) == len(xg) else [0.0] * len(xg)
        else:
            print("[警告] XML 系数个数与预期不符, 改用内置兜底系数, 请人工核对!")
    else:
        print("[提示] 未提供/未找到 XML, 使用内置兜底系数 —— 换影像后务必核对!")

    if not INPUT_IMAGE:
        print("[错误] 请在 输入配置.txt 中填写 INPUT_IMAGE (输入影像路径)")
    elif not os.path.exists(INPUT_IMAGE):
        print(f"[错误] 找不到输入文件: {INPUT_IMAGE}")
    else:
        radiometric_calibration_bip(INPUT_IMAGE, OUTPUT_IMAGE, gains,
                                    offsets, DRIVER)
