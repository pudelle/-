from flask import Blueprint, jsonify
from googleapiclient.discovery import build

# Настройка Google Sheets
SPREADSHEET_ID = '17vAx26XcUJEJ8POW6zwJ-oUHGK0uoNF5PlYuXwFgdsU'  # Идентификатор таблицы
RANGE = 'Sheet1!A2:H'  # Диапазон данных
API_KEY = 'AIzaSyAmdSOhE9WOqh75rFdRE9lZdzZRyXhNWCc'  # Ваш API-ключ

# Создаём Blueprint
get_stock_bp = Blueprint('get_stock', __name__)

def get_sheets_data_with_api_key(spreadsheet_id, range_name, api_key):
    """Получает данные из Google Sheets через API-ключ."""
    try:
        service = build('sheets', 'v4', developerKey=api_key)
        sheet = service.spreadsheets()
        response = sheet.values().get(spreadsheetId=spreadsheet_id, range=range_name).execute()
        values = response.get('values', [])
        return values
    except Exception as e:
        print(f"Ошибка при получении данных из Google Таблицы через API-ключ: {e}")
        return None

@get_stock_bp.route('/api/getstock', methods=['GET'])
def get_stock():
    """Эндпоинт для получения данных из Google Таблицы."""
    try:
        rows = get_sheets_data_with_api_key(SPREADSHEET_ID, RANGE, API_KEY)
        if not rows:
            return jsonify({'error': 'Данные из Google Таблицы отсутствуют или диапазон пуст.'}), 500

        # Преобразуем данные в удобный формат {id: остаток}
        stock = {}
        for row in rows:
            if len(row) >= 8 and row[0].isdigit():
                product_id = int(row[0])
                try:
                    stock[product_id] = int(row[7]) if row[7].isdigit() else 0
                except ValueError:
                    stock[product_id] = 0

        return jsonify(stock), 200

    except Exception as e:
        print(f"Ошибка: {e}")
        return jsonify({'error': 'Произошла ошибка на сервере.'}), 500