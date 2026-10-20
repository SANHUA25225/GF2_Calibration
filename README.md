# GF-2 辐射定标工具（Radiometric Calibration）

将 GF-2（兼容 GF-1 等国产高分系列）PMS 多光谱影像的原始 **DN 值**定标为**辐射亮度（Radiance）**，
输出 **BIP（Band Interleaved by Pixel）** 存储方式的 GeoTIFF（LZW 压缩），
ENVI / ArcGIS / QGIS 均可直接读取。

定标公式：

```text
Radiance = Gain × DN + Offset
```

- Gain / Offset **自动**从影像配套的 XML 元数据中读取（GF-2 的系数位于 `<AbsCeof>` 标签），
  免去手动查表、手动输入系数
- 换一景影像只需修改一个文本文件（`输入配置.txt`），无需改动代码

## 文件说明

| 文件 | 说明 |
| --- | --- |
| `运行定标.bat` | 一键运行（自动激活 conda 环境 `gf2obia`），推荐方式 |
| `输入配置.txt` | 输入/输出路径配置，换影像时只改这个文件 |
| `gf2_radiometric_calibration_fixed.py` | 定标程序本体 |
| `操作指南.html` | 图文版详细操作手册（含常见问题排查） |

## 快速开始

### 环境要求

- Windows + Miniconda / Anaconda
- Python 环境中安装依赖（本机使用环境名 `gf2obia`，Python 3.11）：

```bash
pip install rasterio numpy
```

### 运行步骤

1. 打开 `输入配置.txt`，填写 3 个路径：

   ```text
   INPUT_IMAGE  = 新影像的 ...-MSS1.tiff 完整路径
   XML_PATH     = 同目录下配套的 ...-MSS1.xml 完整路径
   OUTPUT_IMAGE = 输出结果保存位置
   ```

2. 双击 `运行定标.bat`，等待 1～3 分钟
3. 看到 `[完成] 辐射定标结果已保存` 即成功

## 换一景影像怎么办

只修改 `输入配置.txt` 中 `=` 右边的路径（不要加引号，`#` 开头的注释行不用动），
保存后重新双击 `运行定标.bat` 即可。定标系数会自动从新影像的 XML 中读取。

## 注意事项

- **XML 必须与影像配套**：不同卫星（PMS1/PMS2）、不同时期的定标系数不同，
  换影像时 `XML_PATH` 必须一起换，否则结果错误
- GF-2 的 `<AbsCeof>` 只包含增益，无偏移项，Offset 按 0 处理
- GF-2 L1A 原始 TIFF 本身不带投影（无 CRS），输出影像同样无地理参考，
  需要配准/正射时请使用影像自带的 `.rpb` 文件在 ENVI/GDAL 中处理
- 输出为 float32 + LZW，单景 4 波段约 0.8～1 GB，请确保磁盘空间充足
- 若输入影像为分块存储或条带存储，程序会清理源文件的 block 设置，
  使用 GDAL 默认条带方式写出

## 已验证环境

Windows 11 · Miniconda3 · Python 3.11 · rasterio 1.4.4 · numpy 2.4.6

## License

仅供学习与科研使用。
