@echo off
title GF-2 Radiometric Calibration (gf2obia)
echo ==============================================
echo   GF-2 radiometric calibration  -  env: gf2obia
echo ==============================================
call "C:\Users\sanhua\miniconda3\Scripts\activate.bat" gf2obia
python "%~dp0gf2_radiometric_calibration_fixed.py"
echo.
echo ==============================================
echo   Output: D:\gf2\GF2_MSS_Radiance_BIP.tif
echo ==============================================
pause
