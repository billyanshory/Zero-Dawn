import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import os
import shutil
import threading
import time
import sys

# Application: EXE to APK Project Generator
# Purpose: Generates a Buildozer/Kivy project structure that bundles a Windows EXE.
# Note: Actual execution of EXE on Android requires emulation layers (Wine/Box64).

class ExeToApkGenerator:
    def __init__(self, root):
        self.root = root
        self.root.title("EXE to Android Project Generator")
        self.root.geometry("700x550")
        self.root.configure(bg="#1a1a1a")

        # UI Styling
        style = ttk.Style()
        style.theme_use('default')
        style.configure("TFrame", background="#1a1a1a")
        style.configure("TLabel", background="#1a1a1a", foreground="#ffffff", font=("Segoe UI", 10))
        style.configure("Header.TLabel", font=("Segoe UI", 16, "bold"), foreground="#00ccff")
        style.configure("TButton", background="#333333", foreground="#ffffff", borderwidth=1)
        style.map("TButton", background=[("active", "#444444")])
        style.configure("Horizontal.TProgressbar", background="#00ccff", troughcolor="#333333")

        self.exe_path = tk.StringVar()
        self.output_dir = tk.StringVar()
        self.status = tk.StringVar(value="Ready.")
        self.progress = tk.DoubleVar(value=0)

        self.setup_ui()

    def setup_ui(self):
        main = ttk.Frame(self.root, padding=20)
        main.pack(fill=tk.BOTH, expand=True)

        ttk.Label(main, text="EXE -> ANDROID PROJECT", style="Header.TLabel").pack(pady=(0, 20))

        # Input
        ttk.Label(main, text="Source Executable (.exe):").pack(anchor="w")
        row1 = ttk.Frame(main)
        row1.pack(fill=tk.X, pady=5)
        ttk.Entry(row1, textvariable=self.exe_path).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        ttk.Button(row1, text="Browse", command=self.load_exe).pack(side=tk.RIGHT)

        # Output
        ttk.Label(main, text="Project Output Directory:").pack(anchor="w", pady=(15, 0))
        row2 = ttk.Frame(main)
        row2.pack(fill=tk.X, pady=5)
        ttk.Entry(row2, textvariable=self.output_dir).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        ttk.Button(row2, text="Browse", command=self.select_dir).pack(side=tk.RIGHT)

        # Logs
        self.console = tk.Text(main, height=10, bg="#000000", fg="#00ccff", font=("Consolas", 9), bd=0)
        self.console.pack(fill=tk.BOTH, expand=True, pady=15)

        # Progress
        ttk.Progressbar(main, variable=self.progress, maximum=100, style="Horizontal.TProgressbar").pack(fill=tk.X, pady=(0, 10))

        # Action
        self.btn_generate = ttk.Button(main, text="GENERATE PROJECT", command=self.start_generation)
        self.btn_generate.pack(fill=tk.X, ipady=10)

    def safe_log(self, msg):
        self.root.after(0, lambda: self._log_impl(msg))

    def _log_impl(self, msg):
        self.console.insert(tk.END, f"> {msg}\n")
        self.console.see(tk.END)

    def safe_progress(self, val):
        self.root.after(0, lambda: self.progress.set(val))

    def load_exe(self):
        f = filedialog.askopenfilename(filetypes=[("Executables", "*.exe")])
        if f: self.exe_path.set(f)

    def select_dir(self):
        d = filedialog.askdirectory()
        if d: self.output_dir.set(d)

    def start_generation(self):
        if not self.exe_path.get() or not self.output_dir.get():
            messagebox.showerror("Error", "Please select source and output.")
            return

        self.btn_generate.configure(state=tk.DISABLED)
        threading.Thread(target=self.generate).start()

    def generate(self):
        try:
            exe = self.exe_path.get()
            out_root = self.output_dir.get()
            name = os.path.splitext(os.path.basename(exe))[0]
            # Sanitize name
            clean_name = "".join(x for x in name if x.isalnum() or x in (' ', '-', '_')).strip()
            project_dir = os.path.join(out_root, clean_name + "_AndroidProject")

            self.safe_progress(10)
            self.safe_log("Initializing project structure...")
            time.sleep(0.2)

            if os.path.exists(project_dir):
                shutil.rmtree(project_dir)
            os.makedirs(project_dir)

            self.safe_progress(30)
            self.safe_log("Copying executable binary...")
            shutil.copy2(exe, os.path.join(project_dir, "payload.exe"))

            self.safe_progress(50)
            self.safe_log("Creating Python wrapper (main.py)...")
            with open(os.path.join(project_dir, "main.py"), "w") as f:
                f.write(self.get_main_py_content(clean_name))

            self.safe_progress(70)
            self.safe_log("Generating Buildozer configuration...")
            with open(os.path.join(project_dir, "buildozer.spec"), "w") as f:
                f.write(self.get_buildozer_spec(clean_name))

            self.safe_progress(90)
            self.safe_log("Writing instructions...")
            with open(os.path.join(project_dir, "README.txt"), "w") as f:
                f.write(self.get_readme_content())

            self.safe_progress(100)
            self.safe_log("Generation Complete.")
            self.safe_log(f"Project located at: {project_dir}")

            self.root.after(0, lambda: messagebox.showinfo("Success", "Project Generated Successfully.\nSee README.txt in the output folder for compilation instructions."))

        except Exception as e:
            self.safe_log(f"ERROR: {e}")
        finally:
            self.root.after(0, lambda: self.btn_generate.configure(state=tk.NORMAL))

    def get_main_py_content(self, name):
        return f'''
import os
from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout

class WrapperApp(App):
    def build(self):
        layout = BoxLayout(orientation='vertical', padding=20)
        layout.add_widget(Label(text="Wrapper for: {name}", font_size='20sp'))
        layout.add_widget(Label(text="Binary 'payload.exe' is bundled.", font_size='16sp'))
        layout.add_widget(Label(text="To execute, this app requires a Wine environment.", color=(1,0,0,1)))
        return layout

if __name__ == '__main__':
    WrapperApp().run()
'''

    def get_buildozer_spec(self, name):
        safe_pkg_name = "".join(c.lower() for c in name if c.isalnum())
        if not safe_pkg_name: safe_pkg_name = "app"
        return f'''[app]
title = {name}
package.name = {safe_pkg_name}
package.domain = org.test
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,exe
version = 0.1
requirements = python3,kivy
orientation = portrait
osx.python_version = 3
osx.kivy_version = 1.9.1
fullscreen = 0
android.permissions = INTERNET
android.archs = arm64-v8a
'''

    def get_readme_content(self):
        return """
ANDROID PROJECT GENERATED
=========================

This folder contains a Kivy/Python project that wraps your Windows Executable (.exe).

INSTRUCTIONS:
1. Ensure 'buildozer' is installed: pip install buildozer
2. If on Windows, you must use WSL (Windows Subsystem for Linux). Buildozer does not support Windows CMD/Powershell natively.
3. Open a terminal in this directory.
4. Run: buildozer android debug
5. The resulting APK will be in the 'bin/' folder.

LIMITATIONS:
- Android runs on Linux kernels and ARM architecture.
- Windows EXEs are for Windows NT kernels and x86 architecture.
- This APK contains your EXE as a file, but CANNOT run it natively.
- To run the EXE, you would need to integrate an emulator like 'Wine' or 'Box64' into this project.
"""

if __name__ == "__main__":
    root = tk.Tk()
    app = ExeToApkGenerator(root)
    root.mainloop()
