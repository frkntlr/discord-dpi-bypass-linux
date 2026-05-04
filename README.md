🚀 discord-dpi-bypass-linux

discord-dpi-bypass-linux is an automated DPI Bypass and DNS-over-HTTPS (DoH) solution specifically designed for Linux (optimized for Arch and CachyOS) to overcome Discord access restrictions and connection issues without affecting overall system performance.
✨ Features

    DPI Bypass: Fragments data packets in a randomized manner to prevent Deep Packet Inspection (DPI) by ISPs, effectively bypassing censorship walls.

    Secure DNS (DoH): Tunnels DNS queries through HTTPS to prevent DNS poisoning and redirection.

    Automated Dependency Management: The script automatically detects and installs missing system packages like tk, curl, and psmisc.

    Persistent Background Service: Integrates with systemd to create a user-level service that starts automatically on boot.

    Isolated Routing: Instead of slowing down your entire internet connection via a VPN, it selectively tunnels only Discord traffic.

🛠️ Installation

Open your terminal and follow these steps:

    Clone the Repository:
    Bash

    git clone https://github.com/frkntlr/discord-dpi-bypass-linux.git
    cd discord-dpi-bypass-linux

    Run the Script:
    Bash

    python cachyos_discord_dpi.py

    Use the Interface:

        Click the "▶ Activate DPI Bypass" button in the window.

        Once completed, you can launch Discord from your application menu.

📖 Development Story

This project was born out of frustration with existing Linux solutions (VPNs, complex iptables rules, etc.) that either slowed down the system or broke after every update.

Challenges & Solutions:

    DNS Blockades: Since ISPs block standard DNS queries, I implemented a DoH (--dns-mode=https) structure.

    Request Blocked Errors: Aggressive packet splitting often caused Cloudflare to block requests. I fine-tuned the random split mode to find the perfect balance between bypassing DPI and maintaining stable server connections.

    User Experience: To avoid constant terminal usage, I developed a Python-based GUI that handles its own dependencies and system persistence.

⚠️ Important Notes

    Connection Test: The built-in connection test might sometimes show warnings due to tracker filtering. If your Discord app opens and functions correctly, you can safely ignore these logs.

    Deactivation: You can revert all changes at any time by clicking the "⏹ Completely Remove" button in the interface.

👤 Developer

    Name: Furkan Atalar

    Location: Istanbul, Türkiye

    Interests: Software Development, PC Gaming, and Automation

📜 License

This project is licensed under the MIT License. It is intended for educational and personal use only.
