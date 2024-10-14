import os
import re

import sys
import json
import socket
import base64
import urllib3
import asyncio
import requests
import warnings
import wakeonlan
from subprocess import Popen, PIPE
from samsungtvws import SamsungTVWS
from prettytable import PrettyTable
from scapy.all import ARP, Ether, srp
from samsungtvws.remote import SendRemoteKey

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
    reset_color = "\033[0m"
    def __init__(self):
        self.device_info = {}
        self.ip = None
        self.tv = None

    def get_device_info(self, ip):
        """Gets the device information from the given endpoint."""
        try:
            url = f"http://{ip}:8001/api/v2/"
            response = requests.get(url)
            if response.status_code == 200:
                self.device_info = response.json()
                print("Device information obtained correctly.")
            else:
                print(f"Error obtaining device information. Status code: {response.status_code}")
        except Exception as e:
            print(f"Error when making the request: {e}")

    def parse_device_info(self):
        """Parse all device information into variables."""
        if not self.device_info:
            print("There is no device information to parse.")
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
        self.ip = device.get("ip", "Desconocido")
        self.model = device.get("model", "Desconocido")
        self.model_name = device.get("modelName", "Desconocido")
        self.name = device.get("name", "Desconocido")
        self.network_type = device.get("networkType", "Desconocido")
        self.resolution = device.get("resolution", "Desconocido")
        self.smart_hub_agreement = device.get("smartHubAgreement", "Desconocido")
        self.ssid = device.get("ssid", "Desconocido")
        self.type = device.get("type", "Desconocido")
        self.udn = device.get("udn", "Desconocido")
        self.wifi_mac = device.get("wifiMac", "Desconocido")
        
        self.is_support = self.device_info.get("isSupport", "Desconocido")
        self.version = self.device_info.get("version", "Desconocido")
        self.uri = self.device_info.get("uri", "Desconocido")
        self.remote = self.device_info.get("remote", "Desconocido")

    def save_config(self):
        """Saves all the device information in a config.cfg file."""
        config_data = {
            "frame_tv_support": self.frame_tv_support,
            "gamepad_support": self.gamepad_support,
            "ime_synced_support": self.ime_synced_support,
            "os": self.os,
            "token_auth_support": self.token_auth_support,
            "voice_support": self.voice_support,
            "country_code": self.country_code,
            "description": self.description,
            "developer_ip": self.developer_ip,
            "developer_mode": self.developer_mode,
            "duid": self.duid,
            "firmware_version": self.firmware_version,
            "id": self.id,
            "ip": self.ip,
            "model": self.model,
            "model_name": self.model_name,
            "name": self.name,
            "network_type": self.network_type,
            "resolution": self.resolution,
            "smart_hub_agreement": self.smart_hub_agreement,
            "ssid": self.ssid,
            "type": self.type,
            "udn": self.udn,
            "wifi_mac": self.wifi_mac,  # Guardando la Wi-Fi MAC
            "is_support": self.is_support,
            "version": self.version,
            "uri": self.uri,
            "remote": self.remote
        }
        with open("config.cfg", "w") as config_file:
            json.dump(config_data, config_file)

    def load_config(self):
        """Carga la configuración del archivo config.cfg si existe."""
        if os.path.exists("config.cfg"):
            with open("config.cfg", "r") as config_file:
                config_data = json.load(config_file)
                self.frame_tv_support = config_data.get("frame_tv_support")
                self.gamepad_support = config_data.get("gamepad_support")
                self.ime_synced_support = config_data.get("ime_synced_support")
                self.os = config_data.get("os")
                self.token_auth_support = config_data.get("token_auth_support")
                self.voice_support = config_data.get("voice_support")
                self.country_code = config_data.get("country_code")
                self.description = config_data.get("description")
                self.developer_ip = config_data.get("developer_ip")
                self.developer_mode = config_data.get("developer_mode")
                self.duid = config_data.get("duid")
                self.firmware_version = config_data.get("firmware_version")
                self.id = config_data.get("id")
                self.ip = config_data.get("ip")
                self.model = config_data.get("model")
                self.model_name = config_data.get("model_name")
                self.name = config_data.get("name")
                self.network_type = config_data.get("network_type")
                self.resolution = config_data.get("resolution")
                self.smart_hub_agreement = config_data.get("smart_hub_agreement")
                self.ssid = config_data.get("ssid")
                self.type = config_data.get("type")
                self.udn = config_data.get("udn")
                self.wifi_mac = config_data.get("wifi_mac")  # Cargando la Wi-Fi MAC
                self.is_support = config_data.get("is_support")
                self.version = config_data.get("version")
                self.uri = config_data.get("uri")
                self.remote = config_data.get("remote")
            return True
        else:
            return False

    def mostrar_aplicaciones_en_tabla(self,apps):
        tabla = PrettyTable()
        tabla.field_names = ["App ID", "Name", "Blocked"]
        for app in apps:
            app_id = app.get('appId', 'N/A')
            #app_type = app.get('app_type', 'N/A')
            name = app.get('name', 'N/A')
            #icon = app.get('icon', 'N/A')
            is_lock = "Yes" if app.get('is_lock') else "No"
            tabla.add_row([app_id, name, is_lock])
        print(tabla)
    async def sendCommand(self,algo,token_file):

        tv = SamsungTVWSAsyncRemote(host=self.ip, port=8001, token_file=token_file)
        await tv.start_listening()
        
        await tv.send_command(SendRemoteKey.click("KEY_POWER"))
        await tv.send_command(SendRemoteKey.hold_key("KEY_POWER", 3))

        await asyncio.sleep(15)
                
        await tv.close()

    def testConection(self,ip,port):
        try:
            socket.gethostbyname(ip)
        except socket.error:
            return False

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex((ip, port))

        if result == 0:
            print(f"El puerto {port} está abierto en la IP {ip}.")
            return True
        else:
            print(f"El puerto {port} está cerrado en la IP {ip}.")
            return False
        sock.close()
    
    def ipToMAC(self,ip):
        """
        pid = Popen(["arp", "-n", IP], stdout=PIPE)
        s = pid.communicate()[0]
        mac = re.search(r"(([a-f\\d]{1,2}\\:){5}[a-f\\d]{1,2})", s).groups()[0]
        return mac
        """
        arp_request = ARP(pdst=ip)
        broadcast = Ether(dst="ff:ff:ff:ff:ff:ff")
        arp_request_broadcast = broadcast / arp_request
        answered_list = srp(arp_request_broadcast, timeout=1, verbose=False)[0]
        
        if answered_list:
            # Obtener la dirección MAC de la respuesta
            return answered_list[0][1].hwsrc
        else:
            return -1

    def menu(self):
        banner64 = "4paR4paS4paT4paI4paI4paI4paI4paI4paI4paI4paI4paT4paS4paRICAgICAgICAgICAgICDilpHilpLilpPilojilpPilpLilpEgICDilpHilpLilpPilojilojilojilojilojilojilojilojilpPilpLilpHilpLilpPilojilpPilpLilpHilpHilpLilpPilojilpPilpLilpEgCuKWkeKWkuKWk+KWiOKWk+KWkuKWkSAgICAgICAgICAgICAgIOKWkeKWkuKWk+KWiOKWk+KWkuKWkeKWkuKWk+KWiOKWk+KWkuKWkSAgICAgIOKWkeKWkuKWk+KWiOKWk+KWkuKWkSAgIOKWkeKWkuKWk+KWiOKWk+KWkuKWkeKWkeKWkuKWk+KWiOKWk+KWkuKWkSAK4paR4paS4paT4paI4paT4paS4paRICAgIOKWkeKWkuKWk+KWiOKWk+KWkuKWkuKWk+KWiOKWk+KWkuKWkeKWkuKWk+KWiOKWk+KWkuKWkeKWkuKWk+KWiOKWk+KWkuKWkSAgICAgIOKWkeKWkuKWk+KWiOKWk+KWkuKWkSAgICDilpHilpLilpPilojilpPilpLilpLilpPilojilpPilpLilpEgIArilpHilpLilpPilojilojilojilojilojilojilpPilpLilpHilpLilpPilojilpPilpLilpLilpPilojilpPilpLilpEgICAgIOKWkeKWkuKWk+KWiOKWk+KWkuKWkSAgICAgIOKWkeKWkuKWk+KWiOKWk+KWkuKWkSAgICDilpHilpLilpPilojilpPilpLilpLilpPilojilpPilpLilpEgIArilpHilpLilpPilojilpPilpLilpEgICAgICDilpLilpPilojilpPilpPilojilpPilpLilpHilpHilpLilpPilojilpPilpLilpHilpLilpPilojilpPilpLilpEgICAgICDilpHilpLilpPilojilpPilpLilpEgICAgIOKWkeKWkuKWk+KWiOKWk+KWk+KWiOKWk+KWkuKWkSAgIArilpHilpLilpPilojilpPilpLilpEgICAgICDilpLilpPilojilpPilpPilojilpPilpLilpHilpHilpLilpPilojilpPilpLilpHilpLilpPilojilpPilpLilpEgICAgICDilpHilpLilpPilojilpPilpLilpEgICAgIOKWkeKWkuKWk+KWiOKWk+KWk+KWiOKWk+KWkuKWkSAgIArilpHilpLilpPilojilojilojilojilojilojilojilojilpPilpLilpHilpLilpPilojilojilpPilpLilpEg4paR4paS4paT4paI4paT4paS4paR4paS4paT4paI4paI4paI4paI4paI4paT4paS4paRICDilpHilpLilpPilojilpPilpLilpEgICAgICDilpHilpLilpPilojilojilpPilpLilpEgICAgCiAKICAgICAgICAgICAgICAgIEJ5OiBKb3JkaSBTZXJyYW5vIEBqMHJkMXMzcnI0bjAgICAgICAgICAgICAgICAgICA="
        banner = base64.b64decode(banner64).decode('utf-8', errors='ignore').split('\n')
        for i, line in enumerate(banner):
            rpl = int(240/len(banner))
            lvalue = i*rpl
            red,green,blue, = 255-lvalue,0,0
            if(i == len(banner)-1):
                red,green,blue = 128,53,3
                red2,green2,blue2 = 227,117,0

                dkljwb = self.reset_color+f"\033[38;2;{red2};{green2};{blue2}m"+base64.b64decode("QGowcmQxczNycjRuMA==").decode('utf-8', errors='ignore')
                line = line.replace(base64.b64decode("QGowcmQxczNycjRuMA==").decode('utf-8', errors='ignore'),str(dkljwb))
            print(f"\033[38;2;{red};{green};{blue}m" + line + self.reset_color)

        if not self.load_config():
            conectividad = False
            while(conectividad == False):
                self.ip = input("TV IP: ")
                if(self.testConection(self.ip,8002)):
                    conectividad = True
                self.wifi_mac = self.ipToMAC(self.ip)
                if(self.wifi_mac!=-1):
                    print("Sending Wake0nLAN Packet...")
                    wakeonlan.send_magic_packet(self.wifi_mac)
                    time.sleep(5)
                    print()



            self.get_device_info(self.ip)
            self.parse_device_info()
            self.save_config()

        sys.path.append('../')
        self.tv = SamsungTVWS(host=self.ip)
        token_file = os.path.dirname(os.path.realpath(__file__)) + '/tv-token.txt'
        self.tv = SamsungTVWS(host=self.ip, port=8002, token_file=token_file)
        #print(self.tv.shortcuts())
        while True: 
            print("01) Display Device Info\n02) Wake0nLAN \n03) Power 0n/0ff \n04) 0pen link\n05) Applications\n06) Send Command\n")
            print(f"\033[38;2;125;0;0m"+"98) Reset Conection\n99) Exit"+self.reset_color)
            opcion = str(int(input("> ")))

            if opcion == "1":
                tabla = PrettyTable()
                tabla.field_names = ["Name","Value"]
                tabla.add_row(["Model Name",self.model_name]) 
                tabla.add_row(["OS",self.os])
                tabla.add_row(["IP",self.ip])
                tabla.add_row(["Resolution",self.resolution])
                tabla.add_row(["Network Type",self.network_type])
                tabla.add_row(["Wifi MAC",self.wifi_mac])
                print(f"\033[38;2;140;172;0m")
                print(tabla)
                print(self.reset_color)
            
            elif opcion == "2":
                wakeonlan.send_magic_packet(self.wifi_mac)
            
            elif opcion == "3":
                wakeonlan.send_magic_packet(self.wifi_mac)
                self.tv.shortcuts().power()
            
            elif opcion == "4":
                while True:
                    url_to_open = input("URL:")
                    if("http" not in url_to_open):
                        url_to_open = f"http://{url_to_open}"
                    r = requests.get(url_to_open)
                    if(r.status_code != 200):
                        print(f"{r.status_code}- UNREACHABLE URL")
                    else:
                        self.tv.open_browser(url_to_open)
                        break
            
            elif opcion == "5":
                tv = self.tv
                apps = tv.app_list()
                self.mostrar_aplicaciones_en_tabla(apps)
                apps_id = list()
                for app in apps:
                    app_id = app.get('appId', 'N/A')
                    app_type = app.get('app_type', 'N/A')
                    name = app.get('name', 'N/A')
                    icon = app.get('icon', 'N/A')
                    is_lock = "Yes" if app.get('is_lock') else "No"
                    apps_id.append(app_id)
                while True:
                    print("What do you want to do?\n01) Run App\n02) Get App Status\n03) Open App\n04) Close App\n05) Open All\n06) Close All\n07) Install App\n08) Uninstall App\n99) Back to Menu")
                    option = str(int(input("> ")))
                    if option == "1":
                        while True:
                            appid = str(input("App ID: "))
                            if appid in apps_id:
                                self.tv.run_app(appid)
                            elif appid.lower() in ["!","exit"]:
                                break
                            else:
                                print("App Not Installed")
                    
                    elif option == "2":
                        while True:
                            appid = str(input("App ID: "))
                            if appid in apps_id:
                                self.tv.rest_app_status(appid)
                            elif appid.lower() in ["!","exit"]:
                                break
                            else:
                                print("App Not Installed")
                    
                    elif option == "3":
                        while True:
                            appid = str(input("App ID: "))
                            if appid in apps_id:
                                self.tv.rest_app_run(appid)
                            elif appid.lower() in ["!","exit"]:
                                break
                            else:
                                print("App Not Installed")
                    
                    elif option == "5":
                        for appid in apps_id:
                            self.tv.rest_app_run(appid)

                    elif option == "6":
                        for appid in apps_id:
                            self.tv.rest_app_run(appid)


                    elif option == "7":
                        appid = str(input("App ID: "))
                        if appid in apps_id:
                            self.tv.rest_app_install(appid)
                        elif appid.lower() in ["!","exit"]:
                            break
                        else:
                            print("App Installed Yet")
                    
                    elif option == "8":
                        #self.tv.rest_app_uninstall('')
                        pass
                    
                    elif option == "99":
                        print("Exiting...")
                        break
                    else:
                        print("No Valid Option")
        
            elif opcion == "6":
                # Si no funciona es el puerto 8002 y no el 8001
                token_file = os.path.dirname(os.path.realpath(__file__)) + '/tv-token.txt'
                self.sendCommand(algo,token_file)
            
            elif opcion == "A":
                pass
            
            elif opcion == "98":
                config_files = ['tv-token.txt','config.cfg']
                for file in config_files:
                    try:
                        os.remove(file)
                    except:
                        pass
                return
                
            
            elif opcion == "99":
                print("Exiting...")
                exit(1)
            else:
                print("No Valid Option")

if __name__ == "__main__":
    while True:
        controller = SamsungTVController()
        controller.menu()

