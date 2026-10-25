import os
import json
import time
import shutil
import tempfile
import unittest
from unittest.mock import MagicMock, patch

from remoteControl import SamsungTVController


class TestSamsungTVController(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.config_path = os.path.join(self.test_dir, "test_config.cfg")
        self.token_path = os.path.join(self.test_dir, "test_token.txt")
        self.controller = SamsungTVController(
            config_file=self.config_path,
            token_file=self.token_path
        )

    def tearDown(self):
        self.controller.stop_dos()
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_init_defaults(self):
        self.assertIsNone(self.controller.ip)
        self.assertEqual(self.controller.port, 8002)
        self.assertFalse(self.controller.dos_running)
        self.assertEqual(self.controller.name, "Desconocido")

    def test_save_and_load_config(self):
        self.controller.ip = "192.168.1.100"
        self.controller.port = 8001
        self.controller.wifi_mac = "AA:BB:CC:DD:EE:FF"
        self.controller.name = "[TV] Living Room"
        self.controller.model_name = "QE55Q80T"
        self.controller.os = "Tizen 6.0"

        # Save config
        saved = self.controller.save_config()
        self.assertTrue(saved)
        self.assertTrue(os.path.exists(self.controller.config_file))

        # Create new controller instance and load config
        new_controller = SamsungTVController(
            config_file=self.config_path,
            token_file=self.token_path
        )
        loaded = new_controller.load_config()
        self.assertTrue(loaded)
        self.assertEqual(new_controller.ip, "192.168.1.100")
        self.assertEqual(new_controller.port, 8001)
        self.assertEqual(new_controller.wifi_mac, "AA:BB:CC:DD:EE:FF")
        self.assertEqual(new_controller.name, "[TV] Living Room")
        self.assertEqual(new_controller.model_name, "QE55Q80T")
        self.assertEqual(new_controller.os, "Tizen 6.0")

    def test_reset_connection(self):
        # Create dummy config and token files
        with open(self.controller.config_file, "w") as f:
            f.write("{}")
        with open(self.controller.token_file, "w") as f:
            f.write("test_token")

        self.assertTrue(os.path.exists(self.controller.config_file))
        self.assertTrue(os.path.exists(self.controller.token_file))

        self.controller.ip = "192.168.1.50"
        self.controller.reset_connection()

        self.assertFalse(os.path.exists(self.controller.config_file))
        self.assertFalse(os.path.exists(self.controller.token_file))
        self.assertIsNone(self.controller.ip)

    def test_parse_device_info(self):
        mock_info = {
            "device": {
                "modelName": "Samsung QLED 65",
                "model": "QN65Q60A",
                "OS": "Tizen",
                "wifiMac": "00:11:22:33:44:55",
                "resolution": "3840x2160",
                "networkType": "wireless",
                "firmwareVersion": "T-KTM2DEUC-2111.1",
                "FrameTVSupport": "false",
                "GamePadSupport": "true",
                "VoiceSupport": "true",
                "TokenAuthSupport": "true",
                "duid": "uuid:12345678-abcd",
                "name": "My Samsung TV"
            }
        }
        self.controller.device_info = mock_info
        self.controller.parse_device_info()

        self.assertEqual(self.controller.model_name, "Samsung QLED 65")
        self.assertEqual(self.controller.wifi_mac, "00:11:22:33:44:55")
        self.assertEqual(self.controller.resolution, "3840x2160")
        self.assertEqual(self.controller.gamepad_support, "true")

    def test_display_device_info_output(self):
        self.controller.name = "Living Room TV"
        self.controller.ip = "192.168.1.50"
        # Verify method runs without error
        try:
            self.controller.display_device_info()
        except Exception as e:
            self.fail(f"display_device_info raised {e}")

    def test_display_apps_in_table(self):
        apps = [
            {"appId": "11101200001", "name": "Netflix", "is_lock": False},
            {"appId": "3201606009684", "name": "Spotify", "is_lock": True}
        ]
        try:
            self.controller.display_apps_in_table(apps)
            self.controller.display_apps_in_table([])
        except Exception as e:
            self.fail(f"display_apps_in_table raised {e}")

    def test_dos_worker_lifecycle_mode1(self):
        mock_tv = MagicMock()
        mock_tv.app_list.return_value = [{"appId": "123", "name": "TestApp"}]
        self.controller.tv = mock_tv

        # Start DoS mode 1
        with patch('builtins.input', return_value="1"):
            self.controller.start_dos()

        self.assertTrue(self.controller.dos_running)
        self.assertEqual(self.controller.dos_mode, 1)
        self.assertIsNotNone(self.controller.dos_thread)
        self.assertTrue(self.controller.dos_thread.is_alive())

        # Let it run briefly
        time.sleep(0.3)

        # Stop DoS
        self.controller.stop_dos()
        self.assertFalse(self.controller.dos_running)
        self.assertIsNone(self.controller.dos_thread)

    def test_dos_worker_lifecycle_mode2(self):
        mock_tv = MagicMock()
        self.controller.tv = mock_tv
        self.controller.wifi_mac = "AA:BB:CC:DD:EE:FF"

        with patch('builtins.input', return_value="2"), \
             patch('wakeonlan.send_magic_packet') as mock_wol:
            self.controller.start_dos()
            self.assertTrue(self.controller.dos_running)
            time.sleep(0.3)
            self.controller.stop_dos()
            self.assertFalse(self.controller.dos_running)

    def test_dos_worker_lifecycle_mode3(self):
        mock_tv = MagicMock()
        mock_tv.app_list.return_value = [{"appId": "123", "name": "App1"}, {"appId": "456", "name": "App2"}]
        self.controller.tv = mock_tv

        with patch('builtins.input', return_value="3"):
            self.controller.start_dos()
            self.assertTrue(self.controller.dos_running)
            time.sleep(0.3)
            self.controller.stop_dos()
            self.assertFalse(self.controller.dos_running)

    def test_send_wol(self):
        self.controller.wifi_mac = "AA:BB:CC:DD:EE:FF"
        with patch('wakeonlan.send_magic_packet') as mock_wol:
            self.controller.send_wol()
            mock_wol.assert_called_once_with("AA:BB:CC:DD:EE:FF")

    def test_remote_control_dispatch(self):
        mock_tv = MagicMock()
        self.controller.tv = mock_tv

        # Simulate user pressing '2' (Volume Up) then 'q' (Quit)
        with patch('builtins.input', side_effect=['2', 'q']):
            self.controller.interactive_remote_control()
            mock_tv.send_key.assert_called_with("KEY_VOLUP")


if __name__ == '__main__':
    unittest.main()
