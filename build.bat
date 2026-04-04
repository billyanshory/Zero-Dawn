@echo off
echo Memulai proses build Nitro-o-PC...

if exist "assets\icon.ico" (
    set ICON_FLAG=--icon="assets\icon.ico"
) else (
    echo Peringatan: assets\icon.ico tidak ditemukan, menggunakan default icon.
    set ICON_FLAG=--icon=NONE
)

set VER_FLAG=
if exist "version_info.txt" (
    set VER_FLAG=--version-file "version_info.txt"
)

pyinstaller --noconsole --onedir --uac-admin --name "Nitro-o-PC" %ICON_FLAG% %VER_FLAG% ^
    --collect-all customtkinter --collect-all pywin32 ^
    --hidden-import win32api --hidden-import win32con --hidden-import win32serviceutil ^
    --hidden-import win32service --hidden-import win32security --hidden-import winreg ^
    --add-data "README.md;." "Nitro-o-PC 2 ( dekstop - Second Layer of Quality Control - 9 Critical Bug ).py"

echo Build selesai! Cek folder dist\Nitro-o-PC\
pause
