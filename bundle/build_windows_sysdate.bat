rem run this script to TEST the build. The other script will be called by build.yml
@echo off
for /f "delims=" %%i in ('powershell get-date -format "{yyyy-MM-dd}"') do set output=%%i

build_windows.bat %output%