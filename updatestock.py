from flask import Blueprint, jsonify, request
from googleapiclient.discovery import build

# Настройка Google Sheets
SPREADSHEET_ID = '17vAx26XcUJEJ8POW6zwJ-oUHGK0uoNF5PlYuXwFgdsU'  # Идентификатор таблицы
RANGE = 'Sheet1!A2:H'  # Диапазон данных
API_KEY = 'AIzaSyAmdSOhE9WOqh75rFdRE9lZdzZRyXhNWCc'  # Ваш API-ключ

# Создаём Blueprint
update_stock_bp = Blueprint('update_stock', __name__)

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

def update_sheets_data_with_api_key(spreadsheet_id, range_name, values, api_key):
    """Обновляет данные в Google Sheets через API-ключ."""
    try:
        service = build('sheets', 'v4', developerKey=api_key)
        body = {'values': values}
        result = service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range=range_name,
            valueInputOption='USER_ENTERED',
            body=body
        ).execute()
        return result
    except Exception as e:
        print(f"Ошибка при обновлении данных в Google Таблице через API-ключ: {e}")
        return None

@update_stock_bp.route('/api/update_stock', methods=['POST'])
def update_stock():
    try:
        data = request.json
        if not data or 'updates' not in data:
            return jsonify({'error': 'Некорректные данные'}), 400
        
        updates = data['updates']
        print("Полученные данные для обновления:", updates)  # Ожидается список вида [{'id': 1, 'ordered': 2}, ...]

        # Получаем текущие данные из таблицы
        rows = get_sheets_data_with_api_key(SPREADSHEET_ID, RANGE, API_KEY)
        if not rows:
            return jsonify({'error': 'Не удалось получить данные из Google Таблицы'}), 500

        # Обновляем остатки
        updated_values = []
        for row in rows:
            if len(row) >= 8 and row[0].isdigit():
                product_id = int(row[0])
                for update in updates:
                    if update['id'] == product_id:
                        current_stock = int(row[7]) if row[7].isdigit() else 0
                        new_stock = max(current_stock - update['ordered'], 0)  # Не допускаем отрицательных остатков
                        row[7] = str(new_stock)  # Обновляем остаток в строке
            updated_values.append(row)

        # Записываем обновлённые данные обратно в таблицу
        result = update_sheets_data_with_api_key(SPREADSHEET_ID, RANGE, updated_values, API_KEY)
        if not result:
            return jsonify({'error': 'Не удалось обновить данные в Google Таблице'}), 500

        return jsonify({'message': 'Данные успешно обновлены'}), 200

    except Exception as e:
        print(f"Ошибка: {e}")
        return jsonify({'error': 'Произошла ошибка на сервере'}), 500