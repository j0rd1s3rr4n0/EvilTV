import unittest
from unittest.mock import patch, MagicMock

from getSamsungTVStoreAppList import get_tv_apps, search_tv_apps, print_apps, AppList


class TestStoreApps(unittest.TestCase):
    def test_app_list_class(self):
        apps = AppList([{"appId": "1"}, {"appId": "2"}], total_count=100)
        self.assertEqual(len(apps), 2)
        self.assertEqual(apps.total_count, 100)
        self.assertIsInstance(apps, list)

    @patch('requests.get')
    def test_get_tv_apps_single_page(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": {
                "allCount": 50,
                "tvApp": [
                    {"appId": "1001", "appName": "App One", "appCategoryName": "Video", "appLanguage": "en"},
                    {"appId": "1002", "appName": "App Two", "appCategoryName": "Game", "appLanguage": "en"}
                ]
            }
        }
        mock_get.return_value = mock_response

        apps = get_tv_apps(size=2, offset=0, paginate=False)
        self.assertEqual(len(apps), 2)
        self.assertEqual(apps.total_count, 50)
        self.assertEqual(apps[0]['appId'], "1001")
        self.assertEqual(apps[1]['appName'], "App Two")
        # Verify single request was made
        self.assertEqual(mock_get.call_count, 1)

    @patch('requests.get')
    def test_get_tv_apps_network_error(self, mock_get):
        import requests
        mock_get.side_effect = requests.RequestException("Timeout")

        apps = get_tv_apps()
        self.assertEqual(len(apps), 0)
        self.assertEqual(apps.total_count, 0)

    @patch('getSamsungTVStoreAppList.get_tv_apps')
    def test_search_tv_apps(self, mock_get_tv_apps):
        mock_get_tv_apps.return_value = AppList([
            {"appId": "1", "appName": "Super Mario"},
            {"appId": "2", "appName": "Netflix"},
            {"appId": "3", "appName": "Mario Kart"}
        ], total_count=3)

        results = search_tv_apps("Mario")
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]["appName"], "Super Mario")
        self.assertEqual(results[1]["appName"], "Mario Kart")

    def test_print_apps_no_exception(self):
        apps = AppList([
            {"appId": "1", "appName": "Test", "appCategoryName": "Cat", "appLanguage": "en"}
        ], total_count=1)
        try:
            print_apps(apps)
            print_apps([])
        except Exception as e:
            self.fail(f"print_apps raised {e}")


if __name__ == '__main__':
    unittest.main()
