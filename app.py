from flask import Flask, request, jsonify, render_template, session, redirect, url_for
from googleapiclient.discovery import build
from io import BytesIO
from flask_session import Session
from reportlab.pdfgen import canvas
from api.getstock import get_stock_bp  # Импортируем Blueprint
from api.updatestock import update_stock_bp  # Импортируем Blueprint из updatestock.py

# Создаем Flask приложение
app = Flask(__name__)
app.secret_key = 'your_secret_key'
# Настройка Flask-Session
app.config['SESSION_TYPE'] = 'filesystem'  # Хранение сессий в файловой системе
app.config['SESSION_COOKIE_NAME'] = "your_cookie_name"  # Название cookie
# Регистрируем Blueprint
app.register_blueprint(get_stock_bp)

if __name__ == '__init__':
    app.run(debug=True)
    
# Регистрируем Blueprint из updatestock.py
app.register_blueprint(update_stock_bp)
    
if __name__ == '__init__':
    app.run(debug=True)  # Убедитесь, что порт соответствует клиентскому коду
        
Session(app)

# Параметры Google Sheets
SPREADSHEET_ID = '17vAx26XcUJEJ8POW6zwJ-oUHGK0uoNF5PlYuXwFgdsU'
RANGE = 'Sheet1!A2:H'

# Настройка Google API
API_KEY = 'AIzaSyAmdSOhE9WOqh75rFdRE9lZdzZRyXhNWCc'
service = build('sheets', 'v4', developerKey=API_KEY)

# Глобальная переменная для хранения корзины
cart = {}

# Эндпоинт для входа
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        name = request.form['name']
        session['user'] = name
        # Записать имя в лог
        with open('user_log.txt', 'a') as log_file:
            log_file.write(f'{name}\n')
        return redirect(url_for('index'))
    return render_template('login.html')

# Эндпоинт для главной страницы
@app.route('/')
def index():
    if 'user' not in session:
        return redirect(url_for('login'))

    # Получение списка товаров
    sheet = service.spreadsheets()
    result = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range=RANGE).execute()
    rows = result.get('values', [])
    products = []

    for i, row in enumerate(rows, start=2):
        id = int(row[0]) if len(row) > 0 and row[0].isdigit() else i
        name = row[1] if len(row) > 1 else ''
        description = row[2] if len(row) > 2 else ''
        quantity = int(row[3]) if len(row) > 3 and row[3].isdigit() else 0
        image_urls = row[4].split(',') if len(row) > 4 and row[4] else ['/static/default.png']
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

    return render_template('index.html', products=products)

# Эндпоинт для получения данных о конкретном продукте
@app.route('/product/<int:product_id>', methods=['GET'])
def get_product(product_id):
    try:
        sheet = service.spreadsheets()
        result = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range=RANGE).execute()
        rows = result.get('values', [])
        for row in rows:
            if int(row[0]) == product_id:
                return jsonify({
                    'id': product_id,
                    'name': row[1],
                    'description': row[2],
                    'imageURLs': row[4].split(',') if row[4] else ['/static/default.png']
                })
        return jsonify({'error': 'Товар не найден'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Эндпоинт для корзины
@app.route('/cart', methods=['GET'])
def view_cart():
    """Эндпоинт для отображения корзины."""
    if request.method == 'POST':
        # Обновление Google Sheets
        for item_id, item in cart.items():
            range_name = f'Sheet1!D{item_id}'
            service.spreadsheets().values().update(
                spreadsheetId=SPREADSHEET_ID,
                range=range_name,
                valueInputOption='RAW',
                body={'values': [[item['quantity']]]}
            ).execute()
        return generate_pdf()

    return render_template('cart.html', cart=cart)

@app.route('/cart-data', methods=['GET'])
def cart_data():
    """Эндпоинт для получения данных корзины."""
    return jsonify(cart)

# Эндпоинт для обновления корзины
@app.route('/update_cart', methods=['POST'])
def update_cart():
    try:
        data = request.json
        product_id = data.get('id')
        change = data.get('change')  # +1 для добавления, -1 для удаления
        max_quantity = data.get('maxQuantity')

        if product_id is None or change is None or max_quantity is None:
            return jsonify({'error': 'Отсутствуют необходимые данные'}), 400

        if product_id not in cart:
            cart[product_id] = {'name': '', 'quantity': 0}

        # Обновляем количество в корзине с учетом ограничения
        cart[product_id]['quantity'] += change
        if cart[product_id]['quantity'] > max_quantity:
            cart[product_id]['quantity'] = max_quantity
        elif cart[product_id]['quantity'] < 0:
            cart[product_id]['quantity'] = 0

        return jsonify({'id': product_id, 'quantityInCart': cart[product_id]['quantity']})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Генерация PDF
def generate_pdf():
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer)
    pdf.drawString(100, 750, "Отгрузочный лист")
    y = 700
    for item_id, item in cart.items():
        pdf.drawString(100, y, f"{item['name']}: {item['quantity']}")
        y -= 20
    pdf.save()
    buffer.seek(0)
    return buffer.getvalue(), 200, {'Content-Type': 'application/pdf'}

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000, debug=True)