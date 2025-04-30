from flask import Blueprint, jsonify, request
from googleapiclient.discovery import build
from .google_sheets import get_sheets_data, update_sheets_data, get_sheets_service

# Создаем Blueprint для маршрутов
products_bp = Blueprint('products', __name__)

# Инициализация Google Sheets
SPREADSHEET_ID = '17vAx26XcUJEJ8POW6zwJ-oUHGK0uoNF5PlYuXwFgdsU'
RANGE = 'Sheet1!A2:H'

# Эндпоинт для получения списка всех продуктов
@products_bp.route('/products', methods=['GET'])
def get_products():
    try:
        rows = get_sheets_data(RANGE)
        products = []
        for i, row in enumerate(rows, start=2):
            id = int(row[0]) if len(row) > 0 and row[0].isdigit() else i
            name = row[1] if len(row) > 1 else ''
            description = row[2] if len(row) > 2 else ''
            quantity = int(row[3]) if len(row) > 3 and row[3].isdigit() else 0
            image_urls = row[4].split(',') if len(row) > 4 and row[4] else []
            category = row[5] if len(row) > 5 else ''
            quantity_available = int(row[7]) if len(row) > 7 and row[7].isdigit() else quantity

            products.append({
                'id': id,
                'name': name,
                'description': description,
                'quantity': quantity,
                'imageURLs': image_urls,
                'category': category,
                'quantityAvailable': quantity_available
            })

        return jsonify(products)
    except Exception as e:
        print(f'Ошибка при получении данных: {e}')
        return jsonify({'error': 'Не удалось получить данные из Google Sheets'}), 500

# Эндпоинт для получения подробной информации о продукте
@products_bp.route('/product/<int:product_id>', methods=['GET'])
def get_product(product_id):
    try:
        rows = get_sheets_data(RANGE)
        for row in rows:
            if int(row[0]) == product_id:
                return jsonify({
                    'id': product_id,
                    'name': row[1],
                    'description': row[2],
                    'imageURLs': row[4].split(',') if row[4] else []
                })
        return jsonify({'error': 'Товар не найден'}), 404
    except Exception as e:
        print(f'Ошибка при получении данных о продукте: {e}')
        return jsonify({'error': str(e)}), 500

# Эндпоинт для добавления товара в корзину
@products_bp.route('/cart', methods=['POST'])
def add_to_cart():
    try:
        data = request.json
        product_id = data.get('id')
        quantity = data.get('quantity', 1)

        # Здесь можно добавить логику для валидации и сохранения корзины
        return jsonify({'message': 'Товар добавлен в корзину', 'product_id': product_id, 'quantity': quantity}), 200
    except Exception as e:
        print(f'Ошибка при добавлении товара в корзину: {e}')
        return jsonify({'error': str(e)}), 500

# Эндпоинт для генерации PDF и обновления остатков
@products_bp.route('/generate-pdf', methods=['POST'])
def generate_pdf_and_update_stock():
    try:
        # Получаем данные корзины из запроса
        cart = request.json.get('cart', [])
        if not cart:
            return jsonify({'error': 'Корзина пуста'}), 400

        # Получаем текущие данные из Google Таблицы
        rows = get_sheets_data(RANGE)

        # Список для хранения обновлений
        updated_rows = rows.copy()  # Копируем текущие строки для обновления в памяти
        for item in cart:
            product_id = item['id']
            quantity_to_deduct = item['quantity']

            # Ищем строку в таблице по ID
            for i, row in enumerate(rows):
                if len(row) > 0 and int(row[0]) == product_id:
                    # Текущий остаток в колонке H
                    current_stock = int(row[7]) if len(row) > 7 and row[7].isdigit() else 0

                    # Вычитаем количество
                    new_stock = max(0, current_stock - quantity_to_deduct)

                    # Обновляем строку в памяти
                    updated_rows[i][7] = str(new_stock)
                    break

        # Завершаем обновление таблицы
        update_sheets_data(RANGE, updated_rows)

        # Логика генерации PDF (если требуется) может быть добавлена здесь

        return jsonify({'message': 'PDF успешно сгенерирован. Остатки обновлены.', 'cart_cleared': True}), 200
    except Exception as e:
        print(f'Ошибка при обновлении Google Sheets: {e}')
        return jsonify({'error': 'Не удалось обновить остатки в Google Sheets.'}), 500