import requests
import json
from prettytable import PrettyTable

# API URL for Samsung TV Store apps
URL = 'https://vdapi.samsung.com/tvs/tvpersonalize/api/tvapps/appserver/list'


class AppList(list):
    """List subclass that retains total count metadata from the server."""
    def __init__(self, items=None, total_count=0):
        super().__init__(items or [])
        self.total_count = total_count


def get_tv_apps(country_code='US', language_code='en', size=50, offset=0, paginate=False, max_apps=None):
    """
    Fetches Samsung TV Store apps from the official API.
    
    :param country_code: ISO 3166-1 alpha-2 country code (e.g., 'US', 'ES')
    :param language_code: ISO 639-1 language code (e.g., 'en', 'es')
    :param size: Number of apps per page/request
    :param offset: Starting offset for pagination
    :param paginate: If True, fetches all pages iteratively up to max_apps
    :param max_apps: Maximum total apps to fetch if paginate is True (None for all)
    :return: AppList (list of app dicts with .total_count attribute)
    """
    all_apps = []
    seen_app_ids = set()
    total_count = 0

    current_offset = offset

    while True:
        params = {
            'country_code': country_code,
            'language_code': language_code,
            'offset': current_offset,
            'size': size,
            'order': 'asc'
        }

        headers = {
            'Accept': '*/*',
            'Accept-Language': f'{language_code}-{country_code},{language_code};q=0.7',
            'Connection': 'keep-alive',
            'Content-Type': 'application/json'
        }

        try:
            response = requests.get(URL, params=params, headers=headers, timeout=10)
            response.raise_for_status()
            apps_data = response.json()

            if 'data' in apps_data and 'tvApp' in apps_data['data']:
                apps = apps_data['data']['tvApp']
                total_count = apps_data['data'].get('allCount', 0)

                if not apps:
                    break

                for app in apps:
                    app_id = app.get('appId')
                    if app_id not in seen_app_ids:
                        seen_app_ids.add(app_id)
                        all_apps.append(app)
                        if max_apps and len(all_apps) >= max_apps:
                            return AppList(all_apps, total_count=total_count)

                # Stop if single-page mode or no more items returned
                if not paginate or len(apps) < size:
                    break

                current_offset += size
            else:
                break

        except requests.RequestException as e:
            print(f"Error fetching the app list: {e}")
            break

    return AppList(all_apps, total_count=total_count)


def search_tv_apps(query, country_code='US', language_code='en', max_results=50):
    """
    Searches apps by name matching a query string.
    """
    # Fetch a larger batch to filter locally
    batch = get_tv_apps(country_code=country_code, language_code=language_code, size=100, paginate=False)
    query_lower = query.strip().lower()
    matches = [app for app in batch if query_lower in app.get('appName', '').lower()]
    return AppList(matches[:max_results], total_count=len(matches))


def print_apps(apps_data, title="Available apps in Samsung TV Store"):
    """Prints fetched app data in a clean formatted table."""
    if not apps_data:
        print("No apps found.")
        return

    total = getattr(apps_data, 'total_count', len(apps_data))
    print(f"\n{title} (Showing {len(apps_data)} of {total} available):")
    
    table = PrettyTable()
    table.field_names = ["#", "App ID", "Name", "Category", "Language"]
    table.align["Name"] = "l"
    table.align["Category"] = "l"

    for idx, app in enumerate(apps_data, 1):
        app_id = app.get('appId', 'Unknown')
        app_name = app.get('appName', 'Unknown')
        app_category = app.get('appCategoryName', 'Unknown')
        app_language = app.get('appLanguage', 'Unknown')
        table.add_row([idx, app_id, app_name, app_category, app_language])

    print(table)


def interactive_store_browser(country_code='US', language_code='en', page_size=25):
    """Provides an interactive terminal browser for Samsung TV Store apps."""
    offset = 0
    while True:
        apps = get_tv_apps(country_code=country_code, language_code=language_code, size=page_size, offset=offset)
        total = apps.total_count or len(apps)
        current_page = (offset // page_size) + 1
        total_pages = max(1, (total + page_size - 1) // page_size)

        print_apps(apps, title=f"Samsung TV Store - Page {current_page}/{total_pages}")
        
        print("\nOptions: [N]ext Page | [P]revious Page | [S]earch | [Q]uit to Main Menu")
        choice = input("> ").strip().lower()

        if choice == 'n':
            if offset + page_size < total:
                offset += page_size
            else:
                print("Already on the last page.")
        elif choice == 'p':
            if offset >= page_size:
                offset -= page_size
            else:
                print("Already on the first page.")
        elif choice == 's':
            query = input("Enter app name to search: ").strip()
            if query:
                results = search_tv_apps(query, country_code=country_code, language_code=language_code)
                print_apps(results, title=f"Search Results for '{query}'")
                input("\nPress Enter to return to browsing...")
        elif choice in ('q', 'exit', 'b', 'back'):
            break


if __name__ == '__main__':
    country = input("Enter country code (default US): ").strip().upper() or 'US'
    language = input("Enter language code (default en): ").strip().lower() or 'en'
    interactive_store_browser(country_code=country, language_code=language)
