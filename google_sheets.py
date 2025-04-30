from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials

# Настройка Google Sheets
SPREADSHEET_ID = '17vAx26XcUJEJ8POW6zwJ-oUHGK0uoNF5PlYuXwFgdsU'
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

try:
    credentials = Credentials.from_service_account_file('credentials.json', scopes=SCOPES)
    service = build('sheets', 'v4', credentials=credentials)
    print("Успешная аутентификация с Google API.")
except Exception as e:
    print(f"Ошибка аутентификации: {e}")
    raise

def get_sheets_data(range_name):
    """Получает данные из Google Sheets."""
    try:
        print(f"Попытка получить данные из диапазона: {range_name}")
        sheet = service.spreadsheets()
        response = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range=range_name).execute()
        values = response.get('values', [])
        if not values:
            print("Данные из Google Таблицы отсутствуют или диапазон пуст.")
        else:
            print(f"Полученные данные: {values}")
        return values
    except Exception as e:
        print(f"Ошибка при получении данных из Google Таблицы: {e}")
        raise

def update_sheets_data(range_name, values):
    """Обновляет данные в Google Sheets."""
    try:
        print(f"Попытка обновить данные в диапазоне: {range_name} значениями: {values}")
        sheet = service.spreadsheets()
        body = {'values': values}
        result = sheet.values().update(
            spreadsheetId=SPREADSHEET_ID,
            range=range_name,
            valueInputOption='RAW',
            body=body
        ).execute()
        print(f"Обновление выполнено успешно: {result}")
    except Exception as e:
        print(f"Ошибка при обновлении данных в Google Таблице: {e}")
        raise