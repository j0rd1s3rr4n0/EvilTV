import requests
import json

# API URL
url = 'https://vdapi.samsung.com/tvs/tvpersonalize/api/tvapps/appserver/list'

def get_tv_apps(country_code='US', language_code='en', size=100, offset=0):
    """Fetches the complete list of Samsung TV Store apps, accumulating the offset."""
    all_apps = []
    seen_app_ids = set()  # To avoid duplicate apps

    while True:
        params = {
            'country_code': country_code,
            'language_code': language_code,
            'offset': offset,
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
            response = requests.get(url, params=params, headers=headers)
            response.raise_for_status()  # Raises an error for HTTP status codes other than 200
            apps_data = response.json()

            # Check if the response contains 'tvApp'
            if 'data' in apps_data and 'tvApp' in apps_data['data']:
                apps = apps_data['data']['tvApp']
                app_count = apps_data['data']['allCount']

                if not apps:
                    print("No more apps found.")
                    break

                # Add only the apps we haven't seen before (using appId)
                for app in apps:
                    app_id = app.get('appId')
                    if app_id not in seen_app_ids:
                        seen_app_ids.add(app_id)
                        all_apps.append(app)

                # If fewer apps are returned than requested, we have no more apps
                if len(apps) < size:
                    break

                # Increase the offset for the next request
                offset += size
            else:
                print("No apps found in the response.")
                break

        except requests.RequestException as e:
            print(f"Error fetching the app list: {e}")
            break

    return all_apps

def print_apps(apps_data):
    """Prints all the fetched app data."""
    if apps_data:
        print(f"Total apps fetched: {len(apps_data)}")
        print("Available apps in Samsung TV Store:")
        print("-" * 50)
        for app in apps_data:
            app_id = app.get('appId', 'Unknown')
            app_name = app.get('appName', 'Unknown')
            app_category = app.get('appCategoryName', 'Unknown')
            app_language = app.get('appLanguage', 'Unknown')

            # Print the app information
            print(f"App ID: {app_id}, Name: {app_name}, Category: {app_category}, Language: {app_language}")
        print("-" * 50)
    else:
        print("No apps found.")

if __name__ == '__main__':
    country = input("Enter country code (default US): ") or 'US'
    language = input("Enter language code (default en): ") or 'en'

    apps = get_tv_apps(country_code=country, language_code=language)
    if apps:
        print_apps(apps)
    else:
        print("Error fetching the apps or no data available.")
