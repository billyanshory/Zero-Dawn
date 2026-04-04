__version__ = "5.0.0"
__author__ = "Nitro-o-PC Dev"
__app_name__ = "Nitro-o-PC Ultimate Optimizer"

import sys
if sys.version_info < (3, 8):
    raise RuntimeError(f"Nitro-o-PC memerlukan Python 3.8+. Anda menggunakan Python {sys.version_info.major}.{sys.version_info.minor}.")

import os
import subprocess
import shutil
import psutil
import customtkinter as ctk
import threading
import time
import ctypes
import platform
import logging
import logging.handlers
from tkinter import messagebox
from pathlib import Path

WINDIR = Path(os.environ.get('WINDIR', r'C:\Windows'))
PREFETCH_PATH = WINDIR / 'Prefetch'
WU_CACHE_PATH = WINDIR / 'SoftwareDistribution' / 'Download'
SYSTEM_TEMP_PATH = WINDIR / 'Temp'

if getattr(sys, 'frozen', False):
    LOG_DIR = Path(sys.executable).parent
else:
    LOG_DIR = Path(__file__).parent

log_file_path = LOG_DIR / 'nitro_pc.log'

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.handlers.RotatingFileHandler(log_file_path, maxBytes=2*1024*1024, backupCount=3)
formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(funcName)s:%(lineno)d — %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

# Conditional import for Windows API
if platform.system() == "Windows":
    import win32api
    import win32con
    import win32serviceutil
    import win32service
    import win32security
    import winreg
else:
    win32api = None
    win32con = None
    win32serviceutil = None
    win32service = None
    win32security = None
    winreg = None

def is_admin():
    try:
        if platform.system() == "Windows":
            return ctypes.windll.shell32.IsUserAnAdmin()
        else:
            return os.getuid() == 0
    except Exception:
        return False

# Elevate privileges if not admin
if not is_admin() and platform.system() == "Windows":
    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, subprocess.list2cmdline(sys.argv[1:]), None, 1)
    sys.exit()

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("green")

class NitroApp(ctk.CTk):
    BALANCED_GUID = "381b4222-f694-41f0-9685-ff5bb260df2e"
    NITRO_BACKUP_SUFFIX = "_NitroDisabled"
    COLOR_NEON_GREEN = "#39FF14"
    COLOR_DARK_GREEN = "#2eb80f"

    def __init__(self):
        super().__init__()

        self.title("Nitro-o-PC - Ultimate Optimizer")
        self.geometry("800x600")
        self.minsize(800, 600)

        # Tabview
        self.tabview = ctk.CTkTabview(self, width=780, height=580)
        self.tabview.pack(padx=10, pady=10, fill="both", expand=True)

        self.tab_boost = self.tabview.add("Turbo Boost")
        self.tab_startup = self.tabview.add("Startup Optimizer")
        self.tab_cleaner = self.tabview.add("Smart Cleaner")

        self.setup_turbo_boost_tab()
        self.setup_startup_tab()
        self.setup_cleaner_tab()
        self.setup_monitor()

    def setup_turbo_boost_tab(self):
        """Initializes the Turbo Boost tab containing service disabling and visual tweaking features."""
        self.boost_frame = ctk.CTkFrame(self.tab_boost)
        self.boost_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        self.boost_label = ctk.CTkLabel(self.boost_frame, text="System Turbo Boost", font=ctk.CTkFont(size=24, weight="bold"))
        self.boost_label.pack(pady=20)

        self.boost_desc = ctk.CTkLabel(self.boost_frame, text="Disable unnecessary services, optimize power plan, and clear standby RAM.", text_color="gray")
        self.boost_desc.pack(pady=10)

        self.disable_wsearch_var = ctk.BooleanVar(value=False)
        self.wsearch_cb = ctk.CTkCheckBox(
            self.boost_frame,
            text="Disable Windows Search (WSearch) - Advanced/Risky",
            variable=self.disable_wsearch_var,
            command=self._wsearch_warning,
            text_color="orange"
        )
        self.wsearch_cb.pack(pady=10)

        self.boost_button = ctk.CTkButton(self.boost_frame, text="TURBO BOOST", font=ctk.CTkFont(size=20, weight="bold"), fg_color=self.COLOR_NEON_GREEN, hover_color="#32CD32", text_color="black", height=60, width=200, command=self.run_turbo_boost)
        self.boost_button.pack(pady=20)

        self.restore_boost_button = ctk.CTkButton(self.boost_frame, text="Undo / Restore Boost", font=ctk.CTkFont(size=14, weight="bold"), fg_color="gray", hover_color="darkgray", text_color="white", height=40, width=150, command=self.restore_boost)
        self.restore_boost_button.pack(pady=10)

        self.boost_status = ctk.CTkLabel(self.boost_frame, text="Status: Ready", font=ctk.CTkFont(size=14))
        self.boost_status.pack(pady=10)
        
        self.blink_state = False
        self.blink_running = True
        self._start_blink()

    def _start_blink(self):
        if not self.blink_running:
            return
        try:
            color = self.COLOR_NEON_GREEN if self.blink_state else self.COLOR_DARK_GREEN
            self.boost_button.configure(fg_color=color)
            self.blink_state = not self.blink_state
        except Exception as e:
            logger.warning("Blink button error: %s", str(e), exc_info=True)
        self._blink_after_id = self.after(1000, self._start_blink)

    def _wsearch_warning(self):
        """Displays a confirmation dialog before allowing the user to select the WSearch disable option."""
        if self.disable_wsearch_var.get():
            confirm = messagebox.askyesno(
                "Critical Warning",
                "Mematikan Windows Search service secara permanen akan merusak fungsi pencarian Start Menu, membuat Windows Explorer search tidak berfungsi, dan di Windows 10 bisa menyebabkan SearchUI.exe masuk ke crash loop. Yakin ingin melanjutkan?"
            )
            if not confirm:
                self.disable_wsearch_var.set(False)

    def run_turbo_boost(self):
        """Runs the Turbo Boost optimization in a separate thread."""
        self.boost_button.configure(state="disabled")
        self.boost_status.configure(text="Status: Boosting...", text_color="yellow")
        threading.Thread(target=self._turbo_boost_thread, daemon=True).start()

    def restore_boost(self):
        """Restores the services disabled by Turbo Boost to their default states."""
        self.restore_boost_button.configure(state="disabled")
        self.boost_status.configure(text="Status: Restoring...", text_color="yellow")
        threading.Thread(target=self._restore_boost_thread, daemon=True).start()

    def _restore_boost_thread(self):
        try:
            changes = getattr(self, '_boost_applied_changes', None)
            if not changes:
                self.after(0, lambda: messagebox.showinfo("Info", "Tidak ada perubahan Boost yang tercatat untuk di-restore."))
                self.after(0, lambda: self.boost_status.configure(text="Status: Ready", text_color="white"))
                return

            if platform.system() == "Windows":
                svc_defaults = {
                    "XblAuthManager": win32service.SERVICE_DEMAND_START,
                    "XblGameSave": win32service.SERVICE_DEMAND_START,
                    "XboxNetApiSvc": win32service.SERVICE_DEMAND_START,
                    "DiagTrack": win32service.SERVICE_AUTO_START,
                    "OneDriveStandaloneUpdater": win32service.SERVICE_DEMAND_START,
                    "OneSyncSvc": win32service.SERVICE_AUTO_START,
                    "WSearch": win32service.SERVICE_AUTO_START
                }
                
                for svc in changes.get("services_disabled", []):
                    start_type = svc_defaults.get(svc, win32service.SERVICE_DEMAND_START)
                    try:
                        hscm = win32service.OpenSCManager(None, None, win32service.SC_MANAGER_ALL_ACCESS)
                        hs = win32service.OpenService(hscm, svc, win32service.SERVICE_ALL_ACCESS)
                        win32service.ChangeServiceConfig(
                            hs,
                            win32service.SERVICE_NO_CHANGE,
                            start_type,
                            win32service.SERVICE_NO_CHANGE,
                            None, None, 0, None, None, None, None
                        )
                        win32service.CloseServiceHandle(hs)
                        win32service.CloseServiceHandle(hscm)
                        # Optionally try to start auto-start services
                        if start_type == win32service.SERVICE_AUTO_START:
                            try:
                                win32serviceutil.StartService(svc)
                                logger.info("Service %s berhasil distart kembali.", svc)
                            except Exception as e:
                                logger.warning("Gagal start ulang service %s (mungkin perlu restart PC): %s", svc, e, exc_info=True)
                    except Exception as e:
                        logger.warning("Failed to restore service %s: %s", svc, str(e), exc_info=True)

                for val_name, (hkey, subkey, orig_val, reg_type) in changes.get("visual_tweaks_original", {}).items():
                    try:
                        key = winreg.OpenKey(hkey, subkey, 0, winreg.KEY_SET_VALUE)
                        winreg.SetValueEx(key, val_name, 0, reg_type, orig_val)
                        winreg.CloseKey(key)
                    except Exception as e:
                        logger.warning("Failed to restore visual effect %s: %s", val_name, str(e), exc_info=True)

            # Reset state
            del self._boost_applied_changes
            self.after(0, lambda: self.boost_status.configure(text="Status: Restore Completed!", text_color=self.COLOR_NEON_GREEN))
        except Exception as e:
            logger.error("Restore boost failed: %s", str(e), exc_info=True)
            self.after(0, lambda: self.boost_status.configure(text=f"Status: Error - {str(e)}", text_color="red"))
        finally:
            self.after(0, lambda: self.restore_boost_button.configure(state="normal"))

    def _turbo_boost_thread(self):
        try:
            self._boost_applied_changes = {
                "services_disabled": [],
                "visual_tweaks_original": {}
            }
            if platform.system() == "Windows":
                # Power plan: Balanced
                subprocess.run(["powercfg", "-setactive", self.BALANCED_GUID], shell=False, timeout=15, creationflags=subprocess.CREATE_NO_WINDOW, capture_output=True)
                
                # Disable services using pywin32
                services_to_disable = [
                    "XblAuthManager", "XblGameSave", "XboxNetApiSvc", 
                    "DiagTrack", "OneDriveStandaloneUpdater", 
                    "OneSyncSvc"
                ]
                if getattr(self, 'disable_wsearch_var', None) and self.disable_wsearch_var.get():
                    services_to_disable.append("WSearch")
                
                for svc in services_to_disable:
                    try:
                        # Stop the service if it's running
                        if win32serviceutil.QueryServiceStatus(svc)[1] == win32service.SERVICE_RUNNING:
                            win32serviceutil.StopService(svc)
                        
                        # Change start type to disabled
                        hscm = win32service.OpenSCManager(None, None, win32service.SC_MANAGER_ALL_ACCESS)
                        hs = win32service.OpenService(hscm, svc, win32service.SERVICE_ALL_ACCESS)
                        win32service.ChangeServiceConfig(
                            hs,
                            win32service.SERVICE_NO_CHANGE,
                            win32service.SERVICE_DISABLED,
                            win32service.SERVICE_NO_CHANGE,
                            None, None, 0, None, None, None, None
                        )
                        win32service.CloseServiceHandle(hs)
                        win32service.CloseServiceHandle(hscm)
                        self._boost_applied_changes["services_disabled"].append(svc)
                    except Exception as e:
                        logger.warning("Failed to disable service %s: %s", svc, str(e), exc_info=True)
                
                # Visual Effects (minimizing)
                visual_tweaks = [
                    (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Explorer\VisualEffects", "VisualFXSetting", 2),
                    (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\DWM", "EnableAeroPeek", 0),
                    (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize", "EnableTransparency", 0)
                ]
                for hkey, subkey, val_name, val_data in visual_tweaks:
                    try:
                        # Save original value
                        try:
                            orig_key = winreg.OpenKey(hkey, subkey, 0, winreg.KEY_READ)
                            orig_val, reg_type = winreg.QueryValueEx(orig_key, val_name)
                            winreg.CloseKey(orig_key)
                            self._boost_applied_changes["visual_tweaks_original"][val_name] = (hkey, subkey, orig_val, reg_type)
                        except FileNotFoundError:
                            logger.debug("Registry key %s\\%s tidak ditemukan, skip backup.", subkey, val_name)

                        key = winreg.OpenKey(hkey, subkey, 0, winreg.KEY_SET_VALUE)
                        winreg.SetValueEx(key, val_name, 0, winreg.REG_DWORD, val_data)
                        winreg.CloseKey(key)
                    except Exception as e:
                        logger.warning("Failed to minimize visual effect %s: %s", val_name, str(e), exc_info=True)
                    
                # Attempt to kill OneDrive and Cortana processes
                for proc in psutil.process_iter(['name']):
                    try:
                        if proc.info['name'] in ['OneDrive.exe', 'Cortana.exe']:
                            proc.kill()
                    except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
                        logger.warning("Failed to kill process %s: %s", proc.info.get('name'), str(e), exc_info=True)

                # Clear Standby RAM Cache using NtSetSystemInformation
                try:
                    # To clear standby list, we need SE_PROF_SINGLE_PROCESS_NAME privilege
                    # and then call NtSetSystemInformation with MemoryPurgeStandbyList = 4
                    if win32api:
                        htoken = None
                        try:
                            flags = win32con.TOKEN_ADJUST_PRIVILEGES | win32con.TOKEN_QUERY
                            htoken = win32security.OpenProcessToken(win32api.GetCurrentProcess(), flags)
                            priv_luid = win32security.LookupPrivilegeValue(None, win32security.SE_PROF_SINGLE_PROCESS_NAME)
                            newPrivileges = [(priv_luid, win32security.SE_PRIVILEGE_ENABLED)]
                            win32security.AdjustTokenPrivileges(htoken, 0, newPrivileges)
                            
                            SYSTEM_MEMORY_LIST_COMMAND = ctypes.c_int(4) # MemoryPurgeStandbyList
                            ctypes.windll.ntdll.NtSetSystemInformation(
                                80, # SystemMemoryListInformation
                                ctypes.byref(SYSTEM_MEMORY_LIST_COMMAND),
                                ctypes.sizeof(SYSTEM_MEMORY_LIST_COMMAND)
                            )
                        finally:
                            if htoken:
                                win32api.CloseHandle(htoken)
                except Exception as e:
                    logger.error("Failed to clear standby RAM: %s", str(e), exc_info=True)

            elif platform.system() == "Linux":
                # Linux fallback: sync and drop caches, set governor to performance
                if os.getuid() == 0:
                    subprocess.run(["sh", "-c", "sync; echo 3 > /proc/sys/vm/drop_caches"], capture_output=True)
                    for gov_file in Path("/sys/devices/system/cpu").glob("cpu*/cpufreq/scaling_governor"):
                        try:
                            gov_file.write_text("performance")
                        except Exception as e:
                            logger.warning("Failed to set performance governor on %s: %s", gov_file, e, exc_info=True)
                
            self.after(0, lambda: self.boost_status.configure(text="Status: Boost Completed!", text_color=self.COLOR_NEON_GREEN))
        except Exception as e:
            logger.error("Turbo boost failed: %s", str(e), exc_info=True)
            self.after(0, lambda: self.boost_status.configure(text=f"Status: Error - {str(e)}", text_color="red"))
        finally:
            self.after(0, lambda: self.boost_button.configure(state="normal"))

    def setup_startup_tab(self):
        """Initializes the Startup Optimizer tab containing the list of active/disabled startup items."""
        self.startup_frame = ctk.CTkFrame(self.tab_startup)
        self.startup_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        self.startup_label = ctk.CTkLabel(self.startup_frame, text="Startup Optimizer", font=ctk.CTkFont(size=24, weight="bold"))
        self.startup_label.pack(pady=10)

        self.startup_scroll = ctk.CTkScrollableFrame(self.startup_frame, width=700, height=300)
        self.startup_scroll.pack(pady=10, fill="both", expand=True)
        
        self.refresh_startup_btn = ctk.CTkButton(self.startup_frame, text="Refresh List", command=self.load_startup_items)
        self.refresh_startup_btn.pack(pady=10)
        
        self.after(300, self.load_startup_items)

    def load_startup_items(self):
        """Loads startup items and their states, executing the registry scan in a background thread."""
        for widget in self.startup_scroll.winfo_children():
            widget.destroy()

        if platform.system() != "Windows":
            lbl = ctk.CTkLabel(self.startup_scroll, text="Startup Optimizer is only available on Windows.", text_color="gray")
            lbl.pack(pady=20)
            return
            
        self.refresh_startup_btn.configure(text="Loading...", state="disabled")
        threading.Thread(target=self._load_startup_thread, daemon=True).start()

    def _load_startup_thread(self):
        try:
            startup_items = []
            paths = [
                (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run"),
                (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\Run")
            ]

            for hkey, path in paths:
                try:
                    key = winreg.OpenKey(hkey, path, 0, winreg.KEY_READ)
                    for i in range(1024):
                        try:
                            name, value, _ = winreg.EnumValue(key, i)
                            startup_items.append({"name": name, "value": value, "hkey": hkey, "path": path, "is_disabled": False})
                        except OSError:
                            break
                    winreg.CloseKey(key)
                except Exception as e:
                    logger.warning("Failed to read active startup key %s: %s", path, str(e), exc_info=True)
                    
                backup_path = path + self.NITRO_BACKUP_SUFFIX
                try:
                    key = winreg.OpenKey(hkey, backup_path, 0, winreg.KEY_READ)
                    for i in range(1024):
                        try:
                            name, value, _ = winreg.EnumValue(key, i)
                            startup_items.append({"name": name, "value": value, "hkey": hkey, "path": path, "is_disabled": True})
                        except OSError:
                            break
                    winreg.CloseKey(key)
                except (FileNotFoundError, OSError) as e:
                    logger.debug("Backup key '%s' belum ada — normal jika startup belum pernah dinonaktifkan.", backup_path)
                except Exception as e:
                    logger.warning("Gagal baca backup startup key %s: %s", backup_path, e, exc_info=True)
            self.after(0, lambda: self._render_startup_items(startup_items))
        except Exception as e:
            logger.error("Error in startup thread: %s", str(e), exc_info=True)
            self.after(0, lambda text=f"Error loading startup items: {str(e)}": self._render_startup_error(text))
            
    def _render_startup_error(self, text):
        lbl = ctk.CTkLabel(self.startup_scroll, text=text, text_color="red")
        lbl.pack(pady=20)
        self.refresh_startup_btn.configure(text="Refresh List", state="normal")

    def _render_startup_items(self, startup_items):
        self.refresh_startup_btn.configure(text="Refresh List", state="normal")
        if not startup_items:
            lbl = ctk.CTkLabel(self.startup_scroll, text="No startup items found.", text_color="gray")
            lbl.pack(pady=20)
            return

        for item in startup_items:
            frame = ctk.CTkFrame(self.startup_scroll)
            frame.pack(fill="x", pady=5, padx=5)
            
            lbl_name = ctk.CTkLabel(frame, text=item["name"], font=ctk.CTkFont(weight="bold"), width=200, anchor="w")
            lbl_name.pack(side="left", padx=10, pady=5)
            
            is_disabled = item.get("is_disabled", False)
            toggle_var = ctk.BooleanVar(value=not is_disabled)
            cb = ctk.CTkCheckBox(frame, text="Enabled", variable=toggle_var, 
                                 command=lambda i=item, v=toggle_var: self.toggle_startup_item(i, v.get()))
            cb.pack(side="right", padx=10, pady=5)

    def toggle_startup_item(self, item, is_enabled):
        """Launches a background thread to toggle a startup item."""
        threading.Thread(target=self._toggle_startup_thread, args=(item, is_enabled), daemon=True).start()

    def _toggle_startup_thread(self, item, is_enabled):
        try:
            active_path = item["path"]
            backup_path = active_path + self.NITRO_BACKUP_SUFFIX
            
            name = item["name"]
            value = item["value"]
            
            if is_enabled:
                # Move from Backup to Active (Write first, then delete)
                ac_key = winreg.CreateKey(item["hkey"], active_path)
                winreg.SetValueEx(ac_key, name, 0, winreg.REG_SZ, value)
                winreg.CloseKey(ac_key)
                
                try:
                    bk_key = winreg.OpenKey(item["hkey"], backup_path, 0, winreg.KEY_ALL_ACCESS)
                    winreg.DeleteValue(bk_key, name)
                    winreg.CloseKey(bk_key)
                except Exception as e:
                    logger.debug("Entry tidak ditemukan di lokasi asal (normal): %s", e)
            else:
                # Move from Active to Backup (Write first, then delete)
                bk_key = winreg.CreateKey(item["hkey"], backup_path)
                winreg.SetValueEx(bk_key, name, 0, winreg.REG_SZ, value)
                winreg.CloseKey(bk_key)
                
                try:
                    ac_key = winreg.OpenKey(item["hkey"], active_path, 0, winreg.KEY_ALL_ACCESS)
                    winreg.DeleteValue(ac_key, name)
                    winreg.CloseKey(ac_key)
                except Exception as e:
                    logger.debug("Entry tidak ditemukan di lokasi asal (normal): %s", e)
            
            # Reload to reflect changes
            self.after(0, self.load_startup_items)
            
        except Exception as e:
            logger.error("Gagal toggle startup item: %s", e, exc_info=True)
            self.after(0, lambda: messagebox.showerror("Error", f"Gagal mengubah startup item: {e}"))

    def _detect_storage_type(self) -> str:
        if platform.system() != "Windows":
            return "unknown"

        # Method 1: PowerShell
        try:
            result = subprocess.run(
                ["powershell", "-NoProfile", "-NonInteractive", "-Command", "(Get-PhysicalDisk | Where-Object {$_.DeviceId -eq '0'}).MediaType"],
                capture_output=True, text=True, timeout=8, creationflags=subprocess.CREATE_NO_WINDOW
            )
            out = result.stdout.lower().strip()
            if "hdd" in out or "hard disk drive" in out:
                return "hdd"
            elif "ssd" in out or "solid state drive" in out:
                return "ssd"
        except Exception as e:
            logger.debug("PowerShell detect storage failed: %s", e)

        # Method 2: WMIC Fallback
        try:
            result = subprocess.run(
                ["wmic", "diskdrive", "get", "MediaType"],
                capture_output=True, text=True, timeout=8, creationflags=subprocess.CREATE_NO_WINDOW
            )
            out = result.stdout.lower()
            if "fixed hard disk" in out:
                return "hdd"
            elif "ssd" in out or "solid state drive" in out:
                return "ssd"
        except Exception as e:
            logger.debug("WMIC detect storage failed: %s", e)

        return "unknown"

    def setup_cleaner_tab(self):
        """Initializes the smart cleaner tab and its widgets, adding HDD warnings if needed."""
        self.cleaner_frame = ctk.CTkFrame(self.tab_cleaner)
        self.cleaner_frame.pack(fill="both", expand=True, padx=20, pady=20)

        self.cleaner_label = ctk.CTkLabel(self.cleaner_frame, text="Smart Cleaner", font=ctk.CTkFont(size=24, weight="bold"))
        self.cleaner_label.pack(pady=20)

        self.clean_temp_cb = ctk.CTkCheckBox(self.cleaner_frame, text="Clean Temp Folders")
        self.clean_temp_cb.pack(pady=10)
        self.clean_temp_cb.select()

        self.clean_prefetch_cb = ctk.CTkCheckBox(self.cleaner_frame, text="Clean Prefetch")
        self.clean_prefetch_cb.pack(pady=10)
        self.clean_prefetch_cb.select()

        self.clean_browser_cb = ctk.CTkCheckBox(self.cleaner_frame, text="Clean Browser Caches (Chrome/Edge/Firefox)")
        self.clean_browser_cb.pack(pady=10)
        self.clean_browser_cb.select()

        self.clean_windows_update_cb = ctk.CTkCheckBox(self.cleaner_frame, text="Clean Windows Update Cache")
        self.clean_windows_update_cb.pack(pady=10)
        self.clean_windows_update_cb.select()
        
        self.clean_recycle_cb = ctk.CTkCheckBox(self.cleaner_frame, text="Empty Recycle Bin")
        self.clean_recycle_cb.pack(pady=10)
        self.clean_recycle_cb.select()

        self.clean_button = ctk.CTkButton(self.cleaner_frame, text="CLEAN NOW", font=ctk.CTkFont(size=16, weight="bold"), command=self.run_cleaner)
        self.clean_button.pack(pady=40)

        self.clean_status = ctk.CTkLabel(self.cleaner_frame, text="Status: Ready")
        self.clean_status.pack(pady=10)

        # Storage type detection via background thread
        self._storage_warn_lbl = ctk.CTkLabel(
            self.cleaner_frame,
            text="🔍 Mendeteksi tipe storage...",
            text_color="gray"
        )
        self._storage_warn_lbl.pack(pady=5)
        threading.Thread(target=self._detect_and_warn_storage, daemon=True).start()

    def _detect_and_warn_storage(self):
        storage_type = self._detect_storage_type()
        self.after(0, lambda: self._apply_storage_warning(storage_type))

    def _apply_storage_warning(self, storage_type):
        if storage_type == "hdd":
            self._storage_warn_lbl.configure(
                text="⚠️ HDD Terdeteksi: Disarankan untuk TIDAK membersihkan Prefetch karena akan memperlambat cold-start aplikasi.",
                text_color="orange"
            )
            self.clean_prefetch_cb.deselect()
        elif storage_type == "ssd":
            self._storage_warn_lbl.configure(
                text="✅ SSD Terdeteksi: Aman membersihkan Prefetch.",
                text_color="green"
            )
        else:
            self._storage_warn_lbl.configure(
                text="❔ Tipe storage tidak diketahui: Harap berhati-hati membersihkan Prefetch.",
                text_color="gray"
            )

    def run_cleaner(self):
        """Runs the smart cleaner operations in a separate thread to avoid UI freezing."""
        if self.clean_recycle_cb.get():
            if not messagebox.askyesno("Confirm", "Are you sure you want to empty the Recycle Bin?"):
                self.clean_recycle_cb.deselect()

        self.clean_button.configure(state="disabled")
        self.clean_status.configure(text="Status: Cleaning...", text_color="yellow")
        threading.Thread(target=self._cleaner_thread, daemon=True).start()

    def _delete_directory_contents(self, path, match_prefix=None):
        """Recursively deletes contents of a given directory path and returns the freed space in bytes."""
        freed = 0
        if not path or not os.path.exists(path):
            return freed
        try:
            with os.scandir(path) as it:
                for entry in it:
                    if match_prefix and not entry.name.startswith(match_prefix):
                        continue
                    try:
                        size = entry.stat().st_size if entry.is_file() else 0
                        if entry.is_file():
                            os.remove(entry.path)
                        elif entry.is_dir():
                            shutil.rmtree(entry.path)
                        freed += size
                    except Exception as e:
                        logger.warning("Failed to delete %s: %s", entry.path, str(e))
        except Exception as e:
            logger.error("Failed to scan directory %s: %s", path, str(e), exc_info=True)
        return freed

    def _stop_service_temporarily(self, svc_name: str, timeout: int = 10) -> bool:
        """Stops a service temporarily with a timeout polling loop, returns True if successfully stopped."""
        try:
            if win32serviceutil.QueryServiceStatus(svc_name)[1] == win32service.SERVICE_RUNNING:
                win32serviceutil.StopService(svc_name)
                deadline = time.time() + timeout
                while time.time() < deadline:
                    time.sleep(0.5)
                    if win32serviceutil.QueryServiceStatus(svc_name)[1] == win32service.SERVICE_STOPPED:
                        logger.info("Service %s berhasil dihentikan.", svc_name)
                        return True
                logger.warning("Timeout saat menunggu service %s untuk berhenti.", svc_name)
                return False
        except Exception as e:
            logger.warning("Failed to stop service temporarily %s: %s", svc_name, e, exc_info=True)
        return False

    def _cleaner_thread(self):
        try:
            cleaned_size = 0
            if platform.system() == "Windows":
                # Temp Folders
                if self.clean_temp_cb.get():
                    temp_paths = list({os.environ.get('TEMP', ''), os.environ.get('TMP', ''), str(SYSTEM_TEMP_PATH)} - {''})
                    for path in temp_paths:
                        cleaned_size += self._delete_directory_contents(path)
                
                # Prefetch
                if self.clean_prefetch_cb.get():
                    cleaned_size += self._delete_directory_contents(str(PREFETCH_PATH))
                
                # Windows Update Cache
                if self.clean_windows_update_cb.get():
                    re_start_wu = self._stop_service_temporarily("wuauserv")
                    cleaned_size += self._delete_directory_contents(str(WU_CACHE_PATH))
                    if re_start_wu:
                        try:
                            win32serviceutil.StartService("wuauserv")
                        except Exception as e:
                            logger.warning("Failed to restart wuauserv: %s", e, exc_info=True)
                                
                # Thumbnail Cache
                _localappdata = os.environ.get('LOCALAPPDATA')
                if _localappdata:
                    thumb_path = os.path.join(_localappdata, r"Microsoft\Windows\Explorer")
                    cleaned_size += self._delete_directory_contents(thumb_path, match_prefix="thumbcache_")

                # Browser Caches
                if self.clean_browser_cb.get():
                    if not _localappdata:
                        logger.warning("LOCALAPPDATA tidak ditemukan, browser cache dilewati.")
                    else:
                        caches = [
                            os.path.join(_localappdata, r"Google\Chrome\User Data\Default\Cache"),
                            os.path.join(_localappdata, r"Microsoft\Edge\User Data\Default\Cache"),
                        ]
                        
                        # Firefox cache is trickier due to random profiles
                        ff_profiles = os.path.join(_localappdata, r"Mozilla\Firefox\Profiles")
                        if os.path.exists(ff_profiles):
                            for profile in os.listdir(ff_profiles):
                                caches.append(os.path.join(ff_profiles, profile, "cache2"))
                                
                        for cache_dir in caches:
                            cleaned_size += self._delete_directory_contents(cache_dir)
                                    
                # Recycle Bin
                if self.clean_recycle_cb.get():
                    try:
                        # SHERB_NOCONFIRMATION = 1, SHERB_NOPROGRESSUI = 2, SHERB_NOSOUND = 4
                        ctypes.windll.shell32.SHEmptyRecycleBinW(None, None, 7)
                    except Exception as e:
                        logger.error("Failed to empty recycle bin: %s", str(e), exc_info=True)
                        
            elif platform.system() == "Linux":
                if self.clean_temp_cb.get():
                    if os.getuid() == 0:
                        for tmp_dir in ["/tmp", "/var/tmp"]:
                            freed = self._delete_directory_contents(tmp_dir)
                            cleaned_size += freed
                            logger.info("Linux /tmp cleanup: freed %d bytes", freed)
                    else:
                        logger.warning("Linux cleanup memerlukan root, dilewati.")
            
            mb_cleaned = cleaned_size / (1024 * 1024)
            self.after(0, lambda text=f"Status: Cleaned {mb_cleaned:.2f} MB!": self.clean_status.configure(text=text, text_color=self.COLOR_NEON_GREEN))
        except Exception as e:
            logger.error("Cleaner thread error: %s", str(e), exc_info=True)
            self.after(0, lambda text=f"Status: Error - {str(e)}": self.clean_status.configure(text=text, text_color="red"))
        finally:
            self.after(0, lambda: self.clean_button.configure(state="normal"))

    def setup_monitor(self):
        """Initializes the bottom monitor bar and starts the monitoring loop for CPU/RAM/Disk."""
        # Bottom monitor bar attached to main window
        self.monitor_frame = ctk.CTkFrame(self, height=60, corner_radius=0)
        self.monitor_frame.pack(side="bottom", fill="x")

        self.cpu_label = ctk.CTkLabel(self.monitor_frame, text="CPU: 0%", font=ctk.CTkFont(weight="bold"))
        self.cpu_label.pack(side="left", padx=20, pady=15)

        self.cpu_progress = ctk.CTkProgressBar(self.monitor_frame, width=150)
        self.cpu_progress.pack(side="left", padx=10, pady=15)
        self.cpu_progress.set(0)

        self.ram_label = ctk.CTkLabel(self.monitor_frame, text="RAM: 0%", font=ctk.CTkFont(weight="bold"))
        self.ram_label.pack(side="left", padx=20, pady=15)

        self.ram_progress = ctk.CTkProgressBar(self.monitor_frame, width=150)
        self.ram_progress.pack(side="left", padx=10, pady=15)
        self.ram_progress.set(0)
        
        self.disk_label = ctk.CTkLabel(self.monitor_frame, text="Disk I/O: 0 KB/s", font=ctk.CTkFont(weight="bold"))
        self.disk_label.pack(side="left", padx=20, pady=15)
        
        self.recommend_label = ctk.CTkLabel(self.monitor_frame, text="", text_color="yellow")
        self.recommend_label.pack(side="right", padx=20, pady=15)
        
        self.monitor_running = True
        
        # Initialize disk io counters
        self.last_disk_io = psutil.disk_io_counters()
        
        # Initialize CPU percent
        psutil.cpu_percent(interval=None)

        threading.Thread(target=self._monitor_thread, daemon=True).start()

    def _monitor_thread(self):
        """Runs as a daemon thread, updating the UI labels for CPU, RAM, and Disk I/O every second."""
        while self.monitor_running:
            try:
                cpu_percent = psutil.cpu_percent(interval=None)
                ram_percent = psutil.virtual_memory().percent
                
                # Disk I/O calculation
                current_disk_io = psutil.disk_io_counters()
                if self.last_disk_io and current_disk_io:
                    read_bytes = current_disk_io.read_bytes - self.last_disk_io.read_bytes
                    write_bytes = current_disk_io.write_bytes - self.last_disk_io.write_bytes
                    total_kb_s = (read_bytes + write_bytes) / 1024.0
                    self.after(0, lambda text=f"Disk I/O: {total_kb_s:.1f} KB/s": self.disk_label.configure(text=text))
                self.last_disk_io = current_disk_io
                
                self.after(0, lambda text=f"CPU: {cpu_percent}%": self.cpu_label.configure(text=text))
                self.after(0, lambda val=cpu_percent / 100.0: self.cpu_progress.set(val))
                
                self.after(0, lambda text=f"RAM: {ram_percent}%": self.ram_label.configure(text=text))
                self.after(0, lambda val=ram_percent / 100.0: self.ram_progress.set(val))
                
                if ram_percent > 90:
                    self.after(0, lambda: self.recommend_label.configure(text="RAM > 90% - click Boost to clear standby!", text_color="red"))
                elif cpu_percent > 90:
                    self.after(0, lambda: self.recommend_label.configure(text="CPU is stressed. Close heavy apps.", text_color="orange"))
                else:
                    self.after(0, lambda: self.recommend_label.configure(text="System is optimal.", text_color=self.COLOR_NEON_GREEN))
            except Exception as e:
                logger.error("Monitor thread error: %s", str(e), exc_info=True)
            time.sleep(1)

    def on_closing(self):
        """Cleans up running threads and timers before gracefully destroying the main window."""
        self.monitor_running = False
        self.blink_running = False
        if hasattr(self, '_blink_after_id'):
            self.after_cancel(self._blink_after_id)
        self.destroy()

if __name__ == "__main__":
    app = NitroApp()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()

# -------------------------------------------------------------
# PYINSTALLER BUILD INSTRUCTIONS
# -------------------------------------------------------------
# To compile this application into a single executable, use:
# pip install pyinstaller
# pyinstaller --noconsole --onedir --uac-admin --collect-all customtkinter --collect-all pywin32 --icon=NONE Nitro-o-PC.py
# (Requires admin rights to run the final exe on Windows)
