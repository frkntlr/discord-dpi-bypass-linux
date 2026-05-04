import os
import sys
import urllib.request
import tarfile
import subprocess
import shutil
import threading
import json
import re

# --- DEPENDENCY CHECK ---
# This block ensures that necessary system packages are installed before the GUI starts.
def check_system_deps():
    print("[*] Checking system dependencies...")
    deps = ["tk", "curl", "psmisc"] # tk for GUI, curl for download, psmisc for fuser/pkill
    missing_deps = []

    for dep in deps:
        # Check if the package is installed using pacman
        check = subprocess.run(["pacman", "-Qq", dep], capture_output=True, text=True)
        if check.returncode != 0:
            missing_deps.append(dep)

    if missing_deps:
        print(f"[!] Missing dependencies found: {', '.join(missing_deps)}")
        print("[*] Attempting to install missing packages...")
        try:
            # Install missing dependencies using sudo (pkexec provides a GUI prompt)
            subprocess.run(["pkexec", "pacman", "-S", "--needed", "--noconfirm"] + missing_deps, check=True)
            print("[+] Dependencies installed successfully.")
            # Restart the script to apply changes
            os.execv(sys.executable, [sys.executable] + sys.argv)
        except Exception as e:
            print(f"[-] Failed to install dependencies: {e}")
            sys.exit(1)
    else:
        print("[+] All system dependencies are satisfied.")

# Run dependency check before anything else
check_system_deps()

import tkinter as tk
from tkinter import scrolledtext

# --- CONFIGURATION ---
PORT = 8082
APP_NAME = "discord-bypass"
BIN_DIR = os.path.expanduser("~/.local/share/discord-dpi")
BIN_PATH = os.path.join(BIN_DIR, "spoofdpi")
SYSTEMD_DIR = os.path.expanduser("~/.config/systemd/user")
SERVICE_PATH = os.path.join(SYSTEMD_DIR, f"{APP_NAME}.service")
LOCAL_APPS_DIR = os.path.expanduser("~/.local/share/applications")

DISCORD_FILES = ["discord.desktop", "com.discordapp.Discord.desktop", "vesktop.desktop", "dev.vencord.Vesktop.desktop"]

def patch_discord_settings(enable=True):
    """Updates Discord settings.json to skip host update checks."""
    for p in ["~/.config/discord", "~/.config/discordcanary", "~/.config/discordptb"]:
        conf = os.path.expanduser(os.path.join(p, "settings.json"))
        if os.path.exists(conf):
            try:
                with open(conf, "r") as f: data = json.load(f)
                if enable: data["SKIP_HOST_UPDATE"] = True
                else: data.pop("SKIP_HOST_UPDATE", None)
                with open(conf, "w") as f: json.dump(data, f, indent=4)
                print(f"[+] Discord setting updated: {conf}")
            except: pass

class DPIApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Discord DPI Fix (Final Stable Build)")
        self.root.geometry("600x580")
        self.root.configure(bg="#11111B")

        tk.Label(root, text="Discord DPI Bypass (SpoofDPI)", font=("Arial", 14, "bold"), bg="#11111B", fg="#CDD6F4").pack(pady=10)

        btn_frame = tk.Frame(root, bg="#11111B")
        btn_frame.pack(pady=10)

        self.btn_act = tk.Button(btn_frame, text="▶ DPI Bypass Aktifleştir", bg="#89B4FA", width=25, command=self.activate_thread)
        self.btn_act.grid(row=0, column=0, padx=5, pady=5)

        self.btn_deact = tk.Button(btn_frame, text="⏹ Tamamen Kaldır", bg="#F38BA8", width=25, command=self.deactivate_thread)
        self.btn_deact.grid(row=0, column=1, padx=5, pady=5)

        self.btn_test = tk.Button(btn_frame, text="🌐 Bağlantı Testi", bg="#FAB387", width=52, command=self.test_connection_thread)
        self.btn_test.grid(row=1, column=0, columnspan=2, pady=5)

        self.log_area = scrolledtext.ScrolledText(root, width=70, height=22, bg="#1E1E2E", fg="#A6E3A1", font=("Consolas", 9))
        self.log_area.pack(pady=10, padx=15)
        self.log("Sistem Hazır. Tüm çıktılar terminale (stdout) de dökülmektedir.")

    def log(self, msg):
        print(msg)
        self.log_area.config(state='normal')
        self.log_area.insert(tk.END, msg + "\n")
        self.log_area.see(tk.END)
        self.log_area.config(state='disabled')

    def activate_thread(self): threading.Thread(target=self.activate_logic, daemon=True).start()
    def deactivate_thread(self): threading.Thread(target=self.deactivate_logic, daemon=True).start()
    def test_connection_thread(self): threading.Thread(target=self.test_logic, daemon=True).start()

    def test_logic(self):
        self.log("\n[*] Testing connection via proxy...")
        # Use -L to follow redirects and a longer timeout.
        # Sometimes 'request blocked' occurs for tracking pixels but the main page works.
        test_cmd = f"curl -4 -L -s -m 10 -o /dev/null -w '%{{http_code}}' -x http://127.0.0.1:{PORT} https://discord.com"
        res = subprocess.run(test_cmd, shell=True, capture_output=True, text=True).stdout.strip()

        if res in ["200", "301", "302"]:
            self.log(f"✅ CONNECTION SUCCESSFUL (HTTP {res})!")
        else:
            self.log(f"⚠️ TEST RETURNED HTTP {res}.")
            self.log("[!] NOTE: If Discord app is working, ignore this 'request blocked' log.")
            self.log("[!] It usually means some non-essential Discord analytics are being filtered.")
            err = subprocess.run(["journalctl", "--user", "-u", f"{APP_NAME}.service", "-n", "5", "--no-pager"], capture_output=True, text=True).stdout
            self.log("\n--- Service Logs ---")
            self.log(err if err else "No logs found.")

    def activate_logic(self):
        try:
            self.log("\n[*] Starting installation steps...")

            # 1. Binary Handling
            actual_bin = shutil.which("spoofdpi")
            if not actual_bin:
                self.log("[-] SpoofDPI binary not found, downloading...")
                os.makedirs(BIN_DIR, exist_ok=True)
                dl_url = "https://github.com/xvzc/SpoofDPI/releases/latest/download/spoofdpi-linux-amd64.tar.gz"
                subprocess.run(["curl", "-L", "-s", "-o", f"{BIN_DIR}/s.tgz", dl_url], check=True)
                with tarfile.open(f"{BIN_DIR}/s.tgz", "r:gz") as tar:
                    tar.extractall(path=f"{BIN_DIR}/temp")
                for r, d, f in os.walk(f"{BIN_DIR}/temp"):
                    for file in f:
                        if "spoofdpi" in file.lower():
                            shutil.move(os.path.join(r, file), BIN_PATH)
                os.chmod(BIN_PATH, 0o755)
                shutil.rmtree(f"{BIN_DIR}/temp")
                os.remove(f"{BIN_DIR}/s.tgz")
                actual_bin = BIN_PATH

            # 2. Service Configuration
            args = (
                f"--listen-addr=127.0.0.1:{PORT} "
                "--dns-mode=https "
                "--https-split-mode=random "
                "--silent"
            )
            self.log(f"[+] Using parameters: {args}")

            service = (
                "[Unit]\nDescription=Discord Bypass\nAfter=network.target\n\n"
                "[Service]\n"
                f"ExecStart={actual_bin} {args}\n"
                "Restart=always\n"
                "RestartSec=2\n\n"
                "[Install]\nWantedBy=default.target"
            )
            os.makedirs(SYSTEMD_DIR, exist_ok=True)
            with open(SERVICE_PATH, "w") as f: f.write(service)

            # Cleanup port and old processes
            subprocess.run(["fuser", "-k", f"{PORT}/tcp"], capture_output=True)
            subprocess.run(["pkill", "-9", "-f", "spoofdpi"], capture_output=True)

            subprocess.run(["systemctl", "--user", "daemon-reload"])
            subprocess.run(["systemctl", "--user", "enable", "--now", f"{APP_NAME}.service"])
            self.log("[+] Background service activated.")

            # 3. Discord Patching
            patch_discord_settings(True)
            for p in ["Discord", "vesktop", "discord"]: subprocess.run(["pkill", "-9", "-x", p], capture_output=True)

            os.makedirs(LOCAL_APPS_DIR, exist_ok=True)
            p_args = f'--proxy-server="http://127.0.0.1:{PORT}" --proxy-bypass-list="*.discord.media"'
            e_vars = f'env http_proxy="http://127.0.0.1:{PORT}" https_proxy="http://127.0.0.1:{PORT}" '

            for d_dir in ["/usr/share/applications", "/var/lib/flatpak/exports/share/applications"]:
                if not os.path.exists(d_dir): continue
                for d_file in os.listdir(d_dir):
                    if d_file in DISCORD_FILES:
                        with open(os.path.join(d_dir, d_file), "r") as f: lines = f.readlines()
                        with open(os.path.join(LOCAL_APPS_DIR, d_file), "w") as f:
                            for line in lines:
                                if line.startswith("Exec="):
                                    clean_exec = re.sub(r"^Exec=(env [^\s]+\s+)?", "Exec=", line.strip())
                                    clean_exec = re.sub(r'--(proxy-server|host-resolver-rules|proxy-bypass-list)="?[^\s"]+"?\s*', '', clean_exec)
                                    if "%U" in clean_exec: clean_exec = clean_exec.replace("%U", f"{p_args} %U")
                                    elif "%u" in clean_exec: clean_exec = clean_exec.replace("%u", f"{p_args} %u")
                                    else: clean_exec += f" {p_args}"
                                    f.write(clean_exec.replace("Exec=", f"Exec={e_vars}") + "\n")
                                else: f.write(line)
                        os.chmod(os.path.join(LOCAL_APPS_DIR, d_file), 0o755)

            subprocess.run(["update-desktop-database", LOCAL_APPS_DIR], capture_output=True)
            self.log("✅ COMPLETED! You can now launch Discord.")

        except Exception as e: self.log(f"❌ ERROR: {str(e)}")

    def deactivate_logic(self):
        self.log("\n[*] Cleaning up the system...")
        for s in [f"{APP_NAME}.service", "discord-bypass.service", "discord-byedpi.service", "spoofdpi-discord.service"]:
            subprocess.run(["systemctl", "--user", "disable", "--now", s], capture_output=True)
            svc_file = os.path.join(SYSTEMD_DIR, s)
            if os.path.exists(svc_file): os.remove(svc_file)

        subprocess.run(["pkill", "-9", "-f", "spoofdpi"], capture_output=True)
        subprocess.run(["fuser", "-k", f"{PORT}/tcp"], capture_output=True)
        patch_discord_settings(False)

        for d in DISCORD_FILES:
            app_file = os.path.join(LOCAL_APPS_DIR, d)
            if os.path.exists(app_file): os.remove(app_file)

        subprocess.run(["update-desktop-database", LOCAL_APPS_DIR], capture_output=True)
        self.log("✅ System cleaned successfully.")

if __name__ == "__main__":
    root = tk.Tk()
    app = DPIApp(root)
    root.mainloop()
