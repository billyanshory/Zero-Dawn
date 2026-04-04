@echo off
echo Memulai proses build...
set ICON_FLAG=
if exist assets\icon.ico (
    set ICON_FLAG=--icon=assets\icon.ico
)
pyinstaller --noconsole --onedir --uac-admin --name "Nitro-o-PC" %ICON_FLAG% --collect-all customtkinter --collect-all pywin32 --hidden-import win32api --hidden-import win32con --hidden-import win32serviceutil --hidden-import win32service --hidden-import win32security --hidden-import winreg --add-data "README.md;." "Nitro-o-PC 3 ( dekstop - Third Layer of Quality Control - 9 Critical Bug ).py"
echo Build selesai. Cek folder dist.
pause
