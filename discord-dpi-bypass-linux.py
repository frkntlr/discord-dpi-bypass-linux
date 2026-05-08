import os
import sys
import urllib.request
import tarfile
import subprocess
import shutil
import threading
import json
import re
import time

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

def patch_discord_desktop_files(port, enable=True):
    """Patches Discord .desktop files to use the proxy."""
    os.makedirs(LOCAL_APPS_DIR, exist_ok=True)

    if not enable:
        for d in DISCORD_FILES:
            app_file = os.path.join(LOCAL_APPS_DIR, d)
            if os.path.exists(app_file): os.remove(app_file)
        subprocess.run(["update-desktop-database", LOCAL_APPS_DIR], capture_output=True)
        return

    p_args = f'--proxy-server="http://127.0.0.1:{port}" --proxy-bypass-list="*.discord.media"'
    e_vars = f'env http_proxy="http://127.0.0.1:{port}" https_proxy="http://127.0.0.1:{port}" '

    for d_dir in ["/usr/share/applications", "/var/lib/flatpak/exports/share/applications"]:
        if not os.path.exists(d_dir): continue
        for d_file in os.listdir(d_dir):
            if d_file in DISCORD_FILES:
                with open(os.path.join(d_dir, d_file), "r") as f: lines = f.readlines()
                with open(os.path.join(LOCAL_APPS_DIR, d_file), "w") as f:
                    for line in lines:
                        if line.startswith("Exec="):
                            clean_exec = re.sub(r"^Exec=(env [^\s]+\s+)?", "Exec=", line.strip())
                            clean_exec = re.sub(r'--(proxy-server|host-resolver-rules|proxy-bypass-list)="?[^\s"]+\"?\s*', '', clean_exec)
                            if "%U" in clean_exec: clean_exec = clean_exec.replace("%U", f"{p_args} %U")
                            elif "%u" in clean_exec: clean_exec = clean_exec.replace("%u", f"{p_args} %u")
                            else: clean_exec += f" {p_args}"
                            f.write(clean_exec.replace("Exec=", f"Exec={e_vars}") + "\n")
                        else: f.write(line)
                os.chmod(os.path.join(LOCAL_APPS_DIR, d_file), 0o755)

    subprocess.run(["update-desktop-database", LOCAL_APPS_DIR], capture_output=True)


class DPIApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Discord Bypass Tool (v2.0)")
        self.root.geometry("650x650")
        self.root.configure(bg="#11111B")

        tk.Label(root, text="Discord Erişim Aracı", font=("Arial", 14, "bold"), bg="#11111B", fg="#CDD6F4").pack(pady=5)
        tk.Label(root, text="SpoofDPI + Cloudflare WARP", font=("Arial", 10), bg="#11111B", fg="#6C7086").pack(pady=0)

        # --- SpoofDPI Section ---
        spoof_frame = tk.LabelFrame(root, text=" SpoofDPI (DPI Bypass) ", bg="#11111B", fg="#89B4FA", font=("Arial", 10, "bold"))
        spoof_frame.pack(pady=5, padx=15, fill="x")

        spoof_btns = tk.Frame(spoof_frame, bg="#11111B")
        spoof_btns.pack(pady=5, padx=5)

        self.btn_spoof_act = tk.Button(spoof_btns, text="▶ SpoofDPI Aktifleştir", bg="#89B4FA", width=25, command=lambda: self.run_thread(self.activate_spoofdpi))
        self.btn_spoof_act.grid(row=0, column=0, padx=5, pady=3)

        self.btn_spoof_deact = tk.Button(spoof_btns, text="⏹ SpoofDPI Kaldır", bg="#F38BA8", width=25, command=lambda: self.run_thread(self.deactivate_spoofdpi))
        self.btn_spoof_deact.grid(row=0, column=1, padx=5, pady=3)

        # --- WARP Section ---
        warp_frame = tk.LabelFrame(root, text=" Cloudflare WARP (VPN Tüneli) ", bg="#11111B", fg="#A6E3A1", font=("Arial", 10, "bold"))
        warp_frame.pack(pady=5, padx=15, fill="x")

        warp_btns = tk.Frame(warp_frame, bg="#11111B")
        warp_btns.pack(pady=5, padx=5)

        self.btn_warp_install = tk.Button(warp_btns, text="📦 WARP Kur", bg="#A6E3A1", fg="#11111B", width=16, command=lambda: self.run_thread(self.install_warp))
        self.btn_warp_install.grid(row=0, column=0, padx=3, pady=3)

        self.btn_warp_connect = tk.Button(warp_btns, text="🔗 WARP Bağlan", bg="#94E2D5", fg="#11111B", width=16, command=lambda: self.run_thread(self.connect_warp))
        self.btn_warp_connect.grid(row=0, column=1, padx=3, pady=3)

        self.btn_warp_disconnect = tk.Button(warp_btns, text="🔌 WARP Kes", bg="#F9E2AF", fg="#11111B", width=16, command=lambda: self.run_thread(self.disconnect_warp))
        self.btn_warp_disconnect.grid(row=0, column=2, padx=3, pady=3)

        # --- Common ---
        common_frame = tk.Frame(root, bg="#11111B")
        common_frame.pack(pady=5, padx=15, fill="x")

        self.btn_test = tk.Button(common_frame, text="🌐 Bağlantı Testi (Discord)", bg="#FAB387", fg="#11111B", command=lambda: self.run_thread(self.test_logic))
        self.btn_test.pack(fill="x", pady=3)

        self.btn_clean_all = tk.Button(common_frame, text="🗑 Tümünü Temizle (SpoofDPI + WARP)", bg="#F38BA8", fg="#11111B", command=lambda: self.run_thread(self.clean_all))
        self.btn_clean_all.pack(fill="x", pady=3)

        self.log_area = scrolledtext.ScrolledText(root, width=75, height=18, bg="#1E1E2E", fg="#A6E3A1", font=("Consolas", 9))
        self.log_area.pack(pady=10, padx=15)
        self.log("Sistem Hazır. İki yöntem mevcuttur:")
        self.log("  1) SpoofDPI — DPI paket manipülasyonu (ücretsiz, ISP'ye bağlı)")
        self.log("  2) Cloudflare WARP — VPN tüneli (ücretsiz, daha güvenilir)")
        self.log("─" * 60)

    def log(self, msg):
        print(msg)
        self.log_area.config(state='normal')
        self.log_area.insert(tk.END, msg + "\n")
        self.log_area.see(tk.END)
        self.log_area.config(state='disabled')

    def run_thread(self, func):
        threading.Thread(target=func, daemon=True).start()

    # ==========================================
    # CONNECTION TEST
    # ==========================================
    def test_logic(self):
        self.log("\n[*] Discord bağlantı testi yapılıyor...")

        # Test direct connection first
        self.log("[*] Doğrudan bağlantı deneniyor...")
        direct_cmd = "curl -4 -L -s -m 10 -o /dev/null -w '%{http_code}' https://discord.com"
        direct_res = subprocess.run(direct_cmd, shell=True, capture_output=True, text=True).stdout.strip()

        if direct_res in ["200", "301", "302"]:
            self.log(f"✅ DOĞRUDAN BAĞLANTI BAŞARILI (HTTP {direct_res})!")
            self.log("[+] Discord zaten erişilebilir durumda.")
            return

        self.log(f"[!] Doğrudan bağlantı: HTTP {direct_res} (engelli)")

        # Test via proxy
        self.log("[*] SpoofDPI proxy üzerinden deneniyor...")
        proxy_cmd = f"curl -4 -L -s -m 10 -o /dev/null -w '%{{http_code}}' -x http://127.0.0.1:{PORT} https://discord.com"
        proxy_res = subprocess.run(proxy_cmd, shell=True, capture_output=True, text=True).stdout.strip()

        if proxy_res in ["200", "301", "302"]:
            self.log(f"✅ SPOOFDPI PROXY BAŞARILI (HTTP {proxy_res})!")
        else:
            self.log(f"⚠️ SpoofDPI proxy: HTTP {proxy_res}")

        # Check WARP status
        warp_check = subprocess.run(["curl", "-s", "-m", "5", "https://www.cloudflare.com/cdn-cgi/trace/"],
                                     capture_output=True, text=True)
        if "warp=on" in warp_check.stdout:
            self.log("✅ Cloudflare WARP aktif ve çalışıyor!")
        elif "warp=off" in warp_check.stdout:
            self.log("[!] WARP kurulu ama bağlı değil. 'WARP Bağlan' butonunu deneyin.")
        else:
            self.log("[!] WARP durumu kontrol edilemedi.")

        # Show service logs if proxy failed
        if proxy_res not in ["200", "301", "302"]:
            err = subprocess.run(["journalctl", "--user", "-u", f"{APP_NAME}.service", "-n", "5", "--no-pager"],
                                 capture_output=True, text=True).stdout
            if err.strip():
                self.log("\n--- SpoofDPI Servis Logları ---")
                self.log(err)

    # ==========================================
    # SPOOFDPI METHODS
    # ==========================================
    def activate_spoofdpi(self):
        try:
            self.log("\n[*] SpoofDPI kurulumu başlatılıyor...")

            # 1. Find or download binary
            actual_bin = shutil.which("spoofdpi")
            if not actual_bin:
                self.log("[-] SpoofDPI binary bulunamadı, indiriliyor...")
                os.makedirs(BIN_DIR, exist_ok=True)
                dl_url = "https://github.com/xvzc/spoofdpi/releases/latest/download/spoofdpi-linux-amd64.tar.gz"
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

            # 2. Grant CAP_NET_RAW for fake packet features
            self.log("[*] Raw socket yetkisi kontrol ediliyor...")
            cap_check = subprocess.run(["getcap", actual_bin], capture_output=True, text=True)
            has_raw_cap = "cap_net_raw" in cap_check.stdout.lower()

            use_advanced = has_raw_cap
            if not has_raw_cap:
                self.log("[!] CAP_NET_RAW yetkisi gerekli (gelişmiş DPI bypass için).")
                self.log("[*] Yetki veriliyor (şifre sorulacak)...")
                try:
                    setcap_res = subprocess.run(
                        ["pkexec", "setcap", "cap_net_raw+ep", actual_bin],
                        capture_output=True, text=True, timeout=60
                    )
                    if setcap_res.returncode == 0:
                        self.log("[+] CAP_NET_RAW yetkisi verildi ✓")
                        use_advanced = True
                    else:
                        self.log(f"[!] Yetki verilemedi: {setcap_res.stderr.strip()}")
                        self.log("[*] Temel modda devam ediliyor (fake packet devre dışı)...")
                except subprocess.TimeoutExpired:
                    self.log("[!] Yetki zaman aşımı. Temel modda devam ediliyor...")
                except Exception as e:
                    self.log(f"[!] Yetki hatası: {e}. Temel modda devam ediliyor...")

            # 3. Build service configuration
            if use_advanced:
                args = (
                    f"--listen-addr=127.0.0.1:{PORT} "
                    "--no-tui "
                    "--log-level=error "
                    "--dns-mode=https "
                    "--dns-cache "
                    "--https-split-mode=random "
                    "--https-disorder "
                    "--https-fake-count=4 "
                    "--default-fake-ttl=8"
                )
                self.log("[+] Gelişmiş mod: fake packet + disorder aktif")
            else:
                args = (
                    f"--listen-addr=127.0.0.1:{PORT} "
                    "--no-tui "
                    "--log-level=error "
                    "--dns-mode=https "
                    "--dns-cache "
                    "--https-split-mode=random"
                )
                self.log("[+] Temel mod: sadece paket parçalama")

            self.log(f"[+] Parametreler: {args}")

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

            # 4. Cleanup and start
            subprocess.run(["fuser", "-k", f"{PORT}/tcp"], capture_output=True)
            subprocess.run(["pkill", "-9", "-f", "spoofdpi"], capture_output=True)
            subprocess.run(["systemctl", "--user", "daemon-reload"])
            subprocess.run(["systemctl", "--user", "enable", "--now", f"{APP_NAME}.service"])

            # 5. Wait and verify service started
            time.sleep(2)
            status = subprocess.run(
                ["systemctl", "--user", "is-active", f"{APP_NAME}.service"],
                capture_output=True, text=True
            ).stdout.strip()

            if status == "active":
                self.log("[+] SpoofDPI servisi başarıyla çalışıyor ✓")
            else:
                self.log(f"[!] Servis durumu: {status}")
                err = subprocess.run(
                    ["journalctl", "--user", "-u", f"{APP_NAME}.service", "-n", "3", "--no-pager"],
                    capture_output=True, text=True
                ).stdout
                self.log(f"[!] Son loglar:\n{err}")

                # If advanced mode failed, retry with basic mode
                if use_advanced:
                    self.log("[*] Gelişmiş mod başarısız, temel moda geçiliyor...")
                    args = (
                        f"--listen-addr=127.0.0.1:{PORT} "
                        "--no-tui "
                        "--log-level=error "
                        "--dns-mode=https "
                        "--dns-cache "
                        "--https-split-mode=random"
                    )
                    service = (
                        "[Unit]\nDescription=Discord Bypass\nAfter=network.target\n\n"
                        "[Service]\n"
                        f"ExecStart={actual_bin} {args}\n"
                        "Restart=always\n"
                        "RestartSec=2\n\n"
                        "[Install]\nWantedBy=default.target"
                    )
                    with open(SERVICE_PATH, "w") as f: f.write(service)
                    subprocess.run(["systemctl", "--user", "daemon-reload"])
                    subprocess.run(["systemctl", "--user", "restart", f"{APP_NAME}.service"])
                    time.sleep(2)
                    status2 = subprocess.run(
                        ["systemctl", "--user", "is-active", f"{APP_NAME}.service"],
                        capture_output=True, text=True
                    ).stdout.strip()
                    if status2 == "active":
                        self.log("[+] Temel modda SpoofDPI çalışıyor ✓")
                    else:
                        self.log("❌ SpoofDPI hiçbir modda başlatılamadı.")
                        self.log("[!] Cloudflare WARP kullanmayı deneyin.")
                        return

            # 6. Patch Discord
            patch_discord_settings(True)
            for p in ["Discord", "vesktop", "discord"]:
                subprocess.run(["pkill", "-9", "-x", p], capture_output=True)
            patch_discord_desktop_files(PORT, enable=True)

            self.log("✅ SpoofDPI KURULUMU TAMAMLANDI!")
            self.log("[*] Discord'u şimdi başlatabilirsiniz.")
            self.log("[*] Çalışmazsa 'Bağlantı Testi' yapın veya WARP deneyin.")

        except Exception as e:
            self.log(f"❌ HATA: {str(e)}")

    def deactivate_spoofdpi(self):
        self.log("\n[*] SpoofDPI temizleniyor...")
        for s in [f"{APP_NAME}.service", "discord-bypass.service", "discord-byedpi.service", "spoofdpi-discord.service"]:
            subprocess.run(["systemctl", "--user", "disable", "--now", s], capture_output=True)
            svc_file = os.path.join(SYSTEMD_DIR, s)
            if os.path.exists(svc_file): os.remove(svc_file)

        subprocess.run(["pkill", "-9", "-f", "spoofdpi"], capture_output=True)
        subprocess.run(["fuser", "-k", f"{PORT}/tcp"], capture_output=True)
        subprocess.run(["systemctl", "--user", "daemon-reload"], capture_output=True)
        patch_discord_settings(False)
        patch_discord_desktop_files(PORT, enable=False)
        self.log("✅ SpoofDPI temizlendi.")

    # ==========================================
    # CLOUDFLARE WARP METHODS
    # ==========================================
    def install_warp(self):
        self.log("\n[*] Cloudflare WARP kurulumu başlatılıyor...")

        # Check if already installed
        if shutil.which("warp-cli"):
            self.log("[+] WARP zaten kurulu ✓")
            self._setup_warp()
            return

        # Check for AUR helper
        aur_helper = None
        for helper in ["paru", "yay"]:
            if shutil.which(helper):
                aur_helper = helper
                break

        if not aur_helper:
            self.log("❌ AUR yardımcısı bulunamadı (paru/yay)!")
            self.log("[!] Lütfen önce bir AUR helper kurun:")
            self.log("    sudo pacman -S paru")
            return

        self.log(f"[+] AUR helper: {aur_helper}")
        self.log("[*] cloudflare-warp-bin kuruluyor (bu biraz sürebilir)...")

        try:
            result = subprocess.run(
                [aur_helper, "-S", "--noconfirm", "--needed", "cloudflare-warp-bin"],
                capture_output=True, text=True, timeout=300
            )
            if result.returncode == 0:
                self.log("[+] WARP paketi kuruldu ✓")
                self._setup_warp()
            else:
                self.log(f"❌ Kurulum hatası: {result.stderr[-500:] if result.stderr else 'bilinmeyen hata'}")
        except subprocess.TimeoutExpired:
            self.log("❌ Kurulum zaman aşımı (5 dakika)")
        except Exception as e:
            self.log(f"❌ Kurulum hatası: {e}")

    def _setup_warp(self):
        """Enable warp-svc and register if needed."""
        self.log("[*] WARP servisi etkinleştiriliyor...")

        # Enable and start warp-svc (system service, needs root)
        svc_status = subprocess.run(
            ["systemctl", "is-active", "warp-svc.service"],
            capture_output=True, text=True
        ).stdout.strip()

        if svc_status != "active":
            self.log("[*] warp-svc servisi başlatılıyor (şifre sorulacak)...")
            subprocess.run(["pkexec", "systemctl", "enable", "--now", "warp-svc.service"],
                           capture_output=True, text=True)
            time.sleep(2)

        # Check registration
        reg_check = subprocess.run(["warp-cli", "registration", "show"],
                                    capture_output=True, text=True)
        if reg_check.returncode != 0 or "No registration" in reg_check.stdout:
            self.log("[*] WARP kaydı yapılıyor...")
            reg_result = subprocess.run(["warp-cli", "registration", "new"],
                                         capture_output=True, text=True)
            if reg_result.returncode == 0:
                self.log("[+] WARP kaydı tamamlandı ✓")
            else:
                self.log(f"[!] Kayıt hatası: {reg_result.stderr.strip()}")
        else:
            self.log("[+] WARP zaten kayıtlı ✓")

        self.log("[+] WARP kurulumu tamamlandı! 'WARP Bağlan' butonunu kullanın.")

    def connect_warp(self):
        self.log("\n[*] Cloudflare WARP bağlantısı kuruluyor...")

        if not shutil.which("warp-cli"):
            self.log("❌ WARP kurulu değil! Önce '📦 WARP Kur' butonunu kullanın.")
            return

        # Make sure service is running
        svc_status = subprocess.run(
            ["systemctl", "is-active", "warp-svc.service"],
            capture_output=True, text=True
        ).stdout.strip()

        if svc_status != "active":
            self.log("[*] warp-svc başlatılıyor...")
            subprocess.run(["pkexec", "systemctl", "start", "warp-svc.service"],
                           capture_output=True, text=True)
            time.sleep(2)

        # Connect
        result = subprocess.run(["warp-cli", "connect"], capture_output=True, text=True)
        time.sleep(3)

        # Verify
        trace = subprocess.run(
            ["curl", "-s", "-m", "5", "https://www.cloudflare.com/cdn-cgi/trace/"],
            capture_output=True, text=True
        )

        if "warp=on" in trace.stdout:
            self.log("✅ WARP BAĞLANTISI BAŞARILI!")
            self.log("[+] Tüm trafik Cloudflare üzerinden yönlendiriliyor.")
            self.log("[+] Discord'u şimdi normal şekilde başlatabilirsiniz.")
            self.log("[!] NOT: WARP aktifken proxy ayarı gerekmez.")

            # Patch Discord settings but remove proxy (WARP handles everything)
            patch_discord_settings(True)
        else:
            self.log(f"⚠️ WARP bağlantı durumu belirsiz.")
            if result.stderr:
                self.log(f"[!] Hata: {result.stderr.strip()}")

            # Show warp-cli status
            status = subprocess.run(["warp-cli", "status"], capture_output=True, text=True)
            self.log(f"[*] WARP durumu: {status.stdout.strip()}")

    def disconnect_warp(self):
        self.log("\n[*] WARP bağlantısı kesiliyor...")

        if not shutil.which("warp-cli"):
            self.log("[!] WARP kurulu değil.")
            return

        subprocess.run(["warp-cli", "disconnect"], capture_output=True, text=True)
        self.log("✅ WARP bağlantısı kesildi.")

    # ==========================================
    # CLEAN ALL
    # ==========================================
    def clean_all(self):
        self.log("\n[*] Tüm sistem temizleniyor...")

        # Clean SpoofDPI
        self.deactivate_spoofdpi()

        # Disconnect WARP (but don't uninstall)
        if shutil.which("warp-cli"):
            subprocess.run(["warp-cli", "disconnect"], capture_output=True, text=True)
            self.log("[+] WARP bağlantısı kesildi.")

        self.log("✅ Tüm sistem temizlendi.")


if __name__ == "__main__":
    root = tk.Tk()
    app = DPIApp(root)
    root.mainloop()
