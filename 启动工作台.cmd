@echo off
chcp 65001 >nul
title LBW 破甲工作台 · 本地版
cd /d "%~dp0"

where node >nul 2>nul
if errorlevel 1 (
  echo.
  echo   没有找到 Node.js。请先安装 Node.js 18 或更高版本：
  echo   https://nodejs.org/
  echo.
  pause
  exit /b 1
)

echo.
echo   正在启动本地工作台，浏览器会自动打开...
echo   关闭这个窗口即停止服务。
echo.
node server.js --open
pause
