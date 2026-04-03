import os
import sys
import subprocess
import shutil
import psutil
import customtkinter as ctk
import threading
import time
import ctypes
import platform

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
    except:
        return False

# Elevate privileges if not admin
if not is_admin() and platform.system() == "Windows":
    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
    sys.exit()

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("green")

class NitroApp(ctk.CTk):
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
        self.boost_frame = ctk.CTkFrame(self.tab_boost)
        self.boost_frame.pack(fill="both", expand=True, padx=20, pady=20)

        self.boost_label = ctk.CTkLabel(self.boost_frame, text="System Turbo Boost", font=ctk.CTkFont(size=24, weight="bold"))
        self.boost_label.pack(pady=20)

        self.boost_desc = ctk.CTkLabel(self.boost_frame, text="Disable unnecessary services, optimize power plan, and clear standby RAM.", text_color="gray")
        self.boost_desc.pack(pady=10)

        self.boost_button = ctk.CTkButton(self.boost_frame, text="TURBO BOOST", font=ctk.CTkFont(size=20, weight="bold"), fg_color="#39FF14", hover_color="#32CD32", text_color="black", height=60, width=200, command=self.run_turbo_boost)
        self.boost_button.pack(pady=40)

        self.boost_status = ctk.CTkLabel(self.boost_frame, text="Status: Ready", font=ctk.CTkFont(size=14))
        self.boost_status.pack(pady=10)

        self.blink_state = False
        self.blink_running = True
        threading.Thread(target=self._blink_button, daemon=True).start()

    def _blink_button(self):
        while self.blink_running:
            try:
                if self.boost_button.cget("state") != "disabled":
                    if self.blink_state:
                        self.boost_button.configure(fg_color="#39FF14")
                    else:
                        self.boost_button.configure(fg_color="#2eb80f")
                    self.blink_state = not self.blink_state
            except Exception:
                pass
            time.sleep(1)

    def run_turbo_boost(self):
        self.boost_button.configure(state="disabled")
        self.boost_status.configure(text="Status: Boosting...", text_color="yellow")
        threading.Thread(target=self._turbo_boost_thread, daemon=True).start()

    def _turbo_boost_thread(self):
        try:
            if platform.system() == "Windows":
                # Power plan: High Performance
                subprocess.run(["powercfg", "-setactive", "8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c"], shell=True, capture_output=True)

                # Disable services using pywin32
                services_to_disable = [
                    "Spooler", "XblAuthManager", "XblGameSave", "XboxNetApiSvc",
                    "WSearch", "DiagTrack", "OneDriveStandaloneUpdater",
                    "OneSyncSvc", "wuauserv", "SysMain"
                ]

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
                    except Exception:
                        pass # Ignore if service doesn't exist

                # Visual Effects (minimizing)
                try:
                    key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Explorer\VisualEffects", 0, winreg.KEY_SET_VALUE)
                    winreg.SetValueEx(key, "VisualFXSetting", 0, winreg.REG_DWORD, 2) # Adjust for best performance
                    winreg.CloseKey(key)
                except Exception:
                    pass

                # Attempt to kill OneDrive and Cortana processes
                for proc in psutil.process_iter(['name']):
                    try:
                        if proc.info['name'] in ['OneDrive.exe', 'SearchUI.exe', 'Cortana.exe']:
                            proc.kill()
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass

                # Clear Standby RAM Cache using SetSystemFileCacheSize
                try:
                    # To clear standby list, we need SE_INCREASE_QUOTA_NAME privilege
                    # and then call SetSystemFileCacheSize(-1, -1, 0)
                    if win32api:
                        flags = win32con.TOKEN_ADJUST_PRIVILEGES | win32con.TOKEN_QUERY
                        htoken = win32security.OpenProcessToken(win32api.GetCurrentProcess(), flags)
                        id = win32security.LookupPrivilegeValue(None, win32security.SE_INCREASE_QUOTA_NAME)
                        newPrivileges = [(id, win32security.SE_PRIVILEGE_ENABLED)]
                        win32security.AdjustTokenPrivileges(htoken, 0, newPrivileges)

                        ctypes.windll.kernel32.SetSystemFileCacheSize(-1, -1, 0)
                except Exception:
                    pass

            elif platform.system() == "Linux":
                # Linux fallback: sync and drop caches, set governor to performance
                os.system("sync; echo 3 > /proc/sys/vm/drop_caches" if os.getuid() == 0 else "")
                os.system("cpufreq-set -r -g performance" if os.getuid() == 0 else "")

            self.boost_status.configure(text="Status: Boost Completed!", text_color="#39FF14")
        except Exception as e:
            self.boost_status.configure(text=f"Status: Error - {str(e)}", text_color="red")
        finally:
            self.boost_button.configure(state="normal")

    def setup_startup_tab(self):
        self.startup_frame = ctk.CTkFrame(self.tab_startup)
        self.startup_frame.pack(fill="both", expand=True, padx=20, pady=20)

        self.startup_label = ctk.CTkLabel(self.startup_frame, text="Startup Optimizer", font=ctk.CTkFont(size=24, weight="bold"))
        self.startup_label.pack(pady=10)

        self.startup_scroll = ctk.CTkScrollableFrame(self.startup_frame, width=700, height=300)
        self.startup_scroll.pack(pady=10, fill="both", expand=True)

        self.refresh_startup_btn = ctk.CTkButton(self.startup_frame, text="Refresh List", command=self.load_startup_items)
        self.refresh_startup_btn.pack(pady=10)

        self.load_startup_items()

    def load_startup_items(self):
        # Clear existing
        for widget in self.startup_scroll.winfo_children():
            widget.destroy()

        if platform.system() != "Windows":
            lbl = ctk.CTkLabel(self.startup_scroll, text="Startup Optimizer is only available on Windows.", text_color="gray")
            lbl.pack(pady=20)
            return

        try:
            # Read from Run registry and our custom backup registry
            startup_items = []
            paths = [
                (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run"),
                (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\Run")
            ]

            # Helper to safely open or create backup key
            def get_backup_key_path(original_path):
                return original_path + "_NitroDisabled"

            for hkey, path in paths:
                # Read active items
                try:
                    key = winreg.OpenKey(hkey, path, 0, winreg.KEY_READ)
                    for i in range(1024):
                        try:
                            name, value, _ = winreg.EnumValue(key, i)
                            startup_items.append({"name": name, "value": value, "hkey": hkey, "path": path, "is_disabled": False})
                        except OSError:
                            break
                    winreg.CloseKey(key)
                except Exception:
                    pass

                # Read disabled items
                backup_path = get_backup_key_path(path)
                try:
                    key = winreg.OpenKey(hkey, backup_path, 0, winreg.KEY_READ)
                    for i in range(1024):
                        try:
                            name, value, _ = winreg.EnumValue(key, i)
                            startup_items.append({"name": name, "value": value, "hkey": hkey, "path": path, "is_disabled": True})
                        except OSError:
                            break
                    winreg.CloseKey(key)
                except Exception:
                    pass

            if not startup_items:
                lbl = ctk.CTkLabel(self.startup_scroll, text="No startup items found.", text_color="gray")
                lbl.pack(pady=20)
                return

            for item in startup_items:
                frame = ctk.CTkFrame(self.startup_scroll)
                frame.pack(fill="x", pady=5, padx=5)

                lbl_name = ctk.CTkLabel(frame, text=item["name"], font=ctk.CTkFont(weight="bold"), width=200, anchor="w")
                lbl_name.pack(side="left", padx=10, pady=5)

                # Use a checkbox for toggle functionality
                is_disabled = item.get("is_disabled", False)
                toggle_var = ctk.BooleanVar(value=not is_disabled)
                cb = ctk.CTkCheckBox(frame, text="Enabled", variable=toggle_var,
                                     command=lambda i=item, v=toggle_var: self.toggle_startup_item(i, v.get()))
                cb.pack(side="right", padx=10, pady=5)

        except Exception as e:
            lbl = ctk.CTkLabel(self.startup_scroll, text=f"Error loading startup items: {str(e)}", text_color="red")
            lbl.pack(pady=20)

    def toggle_startup_item(self, item, is_enabled):
        try:
            active_path = item["path"]
            backup_path = active_path + "_NitroDisabled"

            name = item["name"]
            value = item["value"]

            if is_enabled:
                # Move from Backup to Active
                try:
                    bk_key = winreg.OpenKey(item["hkey"], backup_path, 0, winreg.KEY_ALL_ACCESS)
                    winreg.DeleteValue(bk_key, name)
                    winreg.CloseKey(bk_key)
                except Exception:
                    pass

                ac_key = winreg.CreateKey(item["hkey"], active_path)
                winreg.SetValueEx(ac_key, name, 0, winreg.REG_SZ, value)
                winreg.CloseKey(ac_key)
            else:
                # Move from Active to Backup
                try:
                    ac_key = winreg.OpenKey(item["hkey"], active_path, 0, winreg.KEY_ALL_ACCESS)
                    winreg.DeleteValue(ac_key, name)
                    winreg.CloseKey(ac_key)
                except Exception:
                    pass

                bk_key = winreg.CreateKey(item["hkey"], backup_path)
                winreg.SetValueEx(bk_key, name, 0, winreg.REG_SZ, value)
                winreg.CloseKey(bk_key)

            # Reload to reflect changes
            self.load_startup_items()

        except Exception as e:
            print(f"Failed to toggle startup item: {e}")

    def setup_cleaner_tab(self):
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

    def run_cleaner(self):
        self.clean_button.configure(state="disabled")
        self.clean_status.configure(text="Status: Cleaning...", text_color="yellow")
        threading.Thread(target=self._cleaner_thread, daemon=True).start()

    def _cleaner_thread(self):
        try:
            cleaned_size = 0
            if platform.system() == "Windows":
                # Temp Folders
                if self.clean_temp_cb.get():
                    temp_paths = [os.environ.get('TEMP'), os.environ.get('TMP'), r"C:\Windows\Temp"]
                    for path in temp_paths:
                        if path and os.path.exists(path):
                            for item in os.listdir(path):
                                item_path = os.path.join(path, item)
                                try:
                                    size = os.path.getsize(item_path) if os.path.isfile(item_path) else 0
                                    if os.path.isfile(item_path):
                                        os.remove(item_path)
                                    elif os.path.isdir(item_path):
                                        shutil.rmtree(item_path)
                                    cleaned_size += size
                                except Exception:
                                    pass

                # Prefetch
                if self.clean_prefetch_cb.get():
                    prefetch_path = r"C:\Windows\Prefetch"
                    if os.path.exists(prefetch_path):
                        for item in os.listdir(prefetch_path):
                            item_path = os.path.join(prefetch_path, item)
                            try:
                                size = os.path.getsize(item_path) if os.path.isfile(item_path) else 0
                                if os.path.isfile(item_path):
                                    os.remove(item_path)
                                cleaned_size += size
                            except Exception:
                                pass

                # Windows Update Cache
                if self.clean_windows_update_cb.get():
                    wu_path = r"C:\Windows\SoftwareDistribution\Download"
                    if os.path.exists(wu_path):
                        for item in os.listdir(wu_path):
                            item_path = os.path.join(wu_path, item)
                            try:
                                size = os.path.getsize(item_path) if os.path.isfile(item_path) else 0
                                if os.path.isfile(item_path):
                                    os.remove(item_path)
                                elif os.path.isdir(item_path):
                                    shutil.rmtree(item_path)
                                cleaned_size += size
                            except Exception:
                                pass

                # Thumbnail Cache
                thumb_path = os.path.join(os.environ.get('LOCALAPPDATA', ''), r"Microsoft\Windows\Explorer")
                if os.path.exists(thumb_path):
                    for item in os.listdir(thumb_path):
                        if item.startswith("thumbcache_"):
                            item_path = os.path.join(thumb_path, item)
                            try:
                                size = os.path.getsize(item_path) if os.path.isfile(item_path) else 0
                                os.remove(item_path)
                                cleaned_size += size
                            except Exception:
                                pass

                # Browser Caches
                if self.clean_browser_cb.get():
                    localappdata = os.environ.get('LOCALAPPDATA', '')
                    appdata = os.environ.get('APPDATA', '')

                    caches = [
                        os.path.join(localappdata, r"Google\Chrome\User Data\Default\Cache"),
                        os.path.join(localappdata, r"Microsoft\Edge\User Data\Default\Cache"),
                    ]

                    # Firefox cache is trickier due to random profiles
                    ff_profiles = os.path.join(localappdata, r"Mozilla\Firefox\Profiles")
                    if os.path.exists(ff_profiles):
                        for profile in os.listdir(ff_profiles):
                            caches.append(os.path.join(ff_profiles, profile, "cache2"))

                    for cache_dir in caches:
                        if os.path.exists(cache_dir):
                            for item in os.listdir(cache_dir):
                                item_path = os.path.join(cache_dir, item)
                                try:
                                    size = os.path.getsize(item_path) if os.path.isfile(item_path) else 0
                                    if os.path.isfile(item_path):
                                        os.remove(item_path)
                                    elif os.path.isdir(item_path):
                                        shutil.rmtree(item_path)
                                    cleaned_size += size
                                except Exception:
                                    pass

                # Recycle Bin
                if self.clean_recycle_cb.get():
                    try:
                        # SHERB_NOCONFIRMATION = 1, SHERB_NOPROGRESSUI = 2, SHERB_NOSOUND = 4
                        ctypes.windll.shell32.SHEmptyRecycleBinW(None, None, 7)
                    except Exception:
                        pass

            elif platform.system() == "Linux":
                if self.clean_temp_cb.get():
                    os.system("rm -rf /tmp/* /var/tmp/*")

            mb_cleaned = cleaned_size / (1024 * 1024)
            self.clean_status.configure(text=f"Status: Cleaned {mb_cleaned:.2f} MB!", text_color="#39FF14")
        except Exception as e:
            self.clean_status.configure(text=f"Status: Error - {str(e)}", text_color="red")
        finally:
            self.clean_button.configure(state="normal")

    def setup_monitor(self):
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

        threading.Thread(target=self._monitor_thread, daemon=True).start()

    def _monitor_thread(self):
        while self.monitor_running:
            try:
                cpu_percent = psutil.cpu_percent(interval=1)
                ram_percent = psutil.virtual_memory().percent

                # Disk I/O calculation
                current_disk_io = psutil.disk_io_counters()
                if self.last_disk_io and current_disk_io:
                    read_bytes = current_disk_io.read_bytes - self.last_disk_io.read_bytes
                    write_bytes = current_disk_io.write_bytes - self.last_disk_io.write_bytes
                    total_kb_s = (read_bytes + write_bytes) / 1024.0
                    self.disk_label.configure(text=f"Disk I/O: {total_kb_s:.1f} KB/s")
                self.last_disk_io = current_disk_io

                self.cpu_label.configure(text=f"CPU: {cpu_percent}%")
                self.cpu_progress.set(cpu_percent / 100.0)

                self.ram_label.configure(text=f"RAM: {ram_percent}%")
                self.ram_progress.set(ram_percent / 100.0)

                if ram_percent > 90:
                    self.recommend_label.configure(text="RAM > 90% - click Boost to clear standby!", text_color="red")
                elif cpu_percent > 90:
                    self.recommend_label.configure(text="CPU is stressed. Close heavy apps.", text_color="orange")
                else:
                    self.recommend_label.configure(text="System is optimal.", text_color="#39FF14")
            except Exception:
                pass
            time.sleep(1)

    def on_closing(self):
        self.monitor_running = False
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
# pyinstaller --noconsole --onefile --icon=NONE Nitro-o-PC.py
# (Requires admin rights to run the final exe on Windows)
