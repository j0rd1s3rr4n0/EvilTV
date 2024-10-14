import requests
import json

# URL de la API
url = 'https://vdapi.samsung.com/tvs/tvpersonalize/api/tvapps/appserver/list'

# Parámetros base de la consulta
params = {
    'country_code': 'US',
    'language_code': 'en',
    'offset': 0,  # Comienza desde el offset 0
    'size': 100,  # Cambia esto según lo que la API permita
    'order': 'asc'
}

# Encabezados de la consulta
headers = {
    'Accept': '*/*',
    'Accept-Language': 'es-ES,es;q=0.7',
    'Connection': 'keep-alive',
    'Content-Type': 'application/json',
    'Origin': 'https://www.samsung.com',
    'Referer': 'https://www.samsung.com/',
    'Sec-Fetch-Dest': 'empty',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Site': 'same-site',
    'Sec-GPC': '1',
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36',
    'sec-ch-ua': '"Brave";v="129", "Not=A?Brand";v="8", "Chromium";v="129"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Linux"'
}

# Inicializa una lista para almacenar todos los resultados
all_data = []
offset = 0

while True:
    # Actualiza el offset en los parámetros
    params['offset'] = offset
    
    # Realizar la solicitud GET
    response = requests.get(url, headers=headers, params=params)

    # Verificar si la solicitud fue exitosa
    if response.status_code == 200:
        # Procesar la respuesta JSON
        data = response.json()
        all_data.extend(data.get('apps', []))
        
        # Comprueba si hay más datos
        if len(data.get('apps', [])) < 1:
            break
        
        # Incrementa el offset
        offset += 100
    else:
        print(f"Error: {response.status_code}, {response.text}")
        break

# Ahora all_data contiene todos los resultados combinados
print(f"Total de aplicaciones obtenidas: {len(all_data)}")

# Guardar el JSON final en a.txt
with open('a.txt', 'w') as f:
    json.dump(all_data, f, indent=4)  # Guarda con una indentación de 4 espacios

print("Los datos han sido guardados en a.txt")
