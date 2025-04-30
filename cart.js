document.addEventListener('DOMContentLoaded', async () => {
    const cartItemsContainer = document.getElementById('cart-items');
    const generatePdfButton = document.getElementById('generate-pdf');
    

    if (!cartItemsContainer) {
        console.error("Элемент с id='cart-items' не найден!");
        return;
    }

    // Загружаем корзину из localStorage
    let cart = JSON.parse(localStorage.getItem('cart') || '[]');
    if (!Array.isArray(cart)) {
        console.error('Данные корзины повреждены. Сбрасываем корзину.');
        cart = [];
    }

    // Получаем актуальные остатки из Google Таблицы
    const stockData = await fetchStockFromGoogleSheets();

    // Удаляем дубликаты: объединяем элементы с одинаковым ID
    const uniqueCart = cart.reduce((acc, item) => {
        const existingItem = acc.find(cartItem => cartItem.id === item.id);
        if (existingItem) {
            existingItem.quantity += item.quantity; // Суммируем количество
        } else {
            acc.push({ ...item }); // Добавляем новый товар
        }
        return acc;
    }, []);

    // Сохраняем обработанную корзину (без дубликатов) в localStorage
    localStorage.setItem('cart', JSON.stringify(uniqueCart));

    console.log("Данные корзины после удаления дубликатов:", uniqueCart);
    console.log("Данные остатков из Google Таблицы:", stockData);

    if (uniqueCart.length === 0) {
        cartItemsContainer.innerHTML = '<p>Корзина пуста</p>';
        return;
    }

    // Очищаем контейнер перед рендерингом
    cartItemsContainer.innerHTML = '';

    // Рендеринг товаров в корзине
    uniqueCart.forEach(item => {
        console.log("Рендеринг товара:", item);
        const availableStock = stockData[item.id] || 0; // Получаем остаток товара из Google Таблицы
        const cartItem = document.createElement('div');
        cartItem.className = 'cart-item';
        cartItem.innerHTML = `
            <img src="${item.image || '/static/default-thumbnail.png'}"
                 alt="${item.name || 'Без названия'}"
                 class="cart-item-image">
            <div class="item-details">
                <h3>${item.name || 'Без названия'}</h3>
                <p>ID: ${item.id}</p>
                <p>Количество: ${item.quantity}</p>
                <p>Остаток: ${availableStock}</p>
                <p>Цена: ${item.price.toFixed(2)} ₽</p>
                <p>Сумма: ${(item.price * item.quantity).toFixed(2)} ₽</p>
                <div class="quantity-controls">
                    <button data-id="${item.id}" class="decrease">-</button>
                    <span class="quantity">${item.quantity}</span>
                    <button data-id="${item.id}" class="increase">+</button>
                </div>
                <button data-id="${item.id}" class="remove-item">Удалить</button>
            </div>
        `;
        cartItemsContainer.appendChild(cartItem);
    });

    document.querySelectorAll('.increase').forEach(btn =>
        btn.addEventListener('click', e => updateQuantity(e.target.dataset.id, 1))
    );
    document.querySelectorAll('.decrease').forEach(btn =>
        btn.addEventListener('click', e => updateQuantity(e.target.dataset.id, -1))
    );
    document.querySelectorAll('.remove-item').forEach(btn =>
        btn.addEventListener('click', e => removeFromCart(e.target.dataset.id))
    );

    if (generatePdfButton) {
        generatePdfButton.addEventListener('click', async () => {
            try {
                console.log("Кнопка 'Генерация PDF' нажата");
                
                // Получение текущих остатков из Google Таблицы
                const stock = await fetchStockFromGoogleSheets();
                console.log('Текущие остатки:', stock);
                
                // Получение данных из полей формы
                const projectName = document.getElementById("project-name").value;
                const deliveryDate = document.getElementById("delivery-date").value;
                const returnDate = document.getElementById("return-date").value;
                
                // Генерация PDF
                PDFGenerator(uniqueCart, projectName, deliveryDate, returnDate);
                
                // Преобразуем данные корзины для обновления остатков
                const updates = uniqueCart.map(item => ({
                    id: item.id,
                    ordered: item.quantity
                }));
                console.log('Данные для обновления остатков:', updates);
                
                // Отправляем данные для обновления остатков
                const updateResult = await updateStockInGoogleSheets(updates);
                if (updateResult) {
                    console.log('Остатки успешно обновлены.');
                } else {
                    console.error('Ошибка обновления остатков.');
                }
                
                // Очистка корзины после завершения всех операций
                clearCart();
            } catch (error) {
                console.error('Ошибка при выполнении операций:', error);
            }
        });
    } else {
        console.error("Кнопка для генерации PDF не найдена!");
    }

    async function fetchStockFromGoogleSheets() {
        try {
            const response = await fetch('/api/getstock'); // Эндпоинт для получения остатков
            if (!response.ok) throw new Error('Не удалось получить данные из Google Таблицы.');
            const stock = await response.json();
            return stock; // Возвращает объект вида { id: остаток, ... }
        } catch (error) {
            console.error('Ошибка при получении остатков из Google Таблицы:', error);
            return {}; // Возвращаем пустой объект, если произошла ошибка
        }
    }
    console.log('Отправляем данные:', updates);
    async function updateStockInGoogleSheets(updates) {
        try {
            const response = await fetch('/api/update_stock', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ updates }), // Отправляем список с ID и количеством заказанного
            });
            
            if (!response.ok) {
                const errorResponse = await response.json();
                throw new Error(errorResponse.error || 'Не удалось обновить данные в Google Таблице.');
            }
            
            const result = await response.json();
            console.log('Результат обновления:', result);
            return result;
        } catch (error) {
            console.error('Ошибка при обновлении данных в Google Таблице:', error);
            return null;
        }
    }
    
    // Пример использования
    document.getElementById('generate-pdf-button').addEventListener('click', async () => {
        // Пример данных: товар ID 1, заказано 2 единицы
        const updates = [
            { id: 1, ordered: 2 },
            { id: 2, ordered: 1 },
        ];
        
        const result = await updateStockInGoogleSheets(updates);
        if (result) {
            alert('Остатки обновлены!');
        }
    });
    function updateQuantity(productId, change) {
        let cart = JSON.parse(localStorage.getItem('cart') || '[]');
        const idx = cart.findIndex(item => item.id === productId);
        const availableStock = stockData[productId] || 0; // Остаток из Google Таблицы

        if (idx !== -1) {
            const currentQuantity = cart[idx].quantity;
            const newQuantity = currentQuantity + change;

            // Проверяем, что остаток не превышает значение из таблицы
            if (newQuantity > availableStock) {
                alert("Нельзя добавить больше, чем доступный остаток.");
                return;
            }

            // Если количество стало <= 0 - удаляем товар из корзины
            if (newQuantity <= 0) {
                cart.splice(idx, 1); // Удаляем товар из корзины
            } else {
                cart[idx].quantity = newQuantity;
            }

            // Сохраняем обновления
            localStorage.setItem('cart', JSON.stringify(cart));
            location.reload();
        } else {
            console.error(`Товар с ID ${productId} не найден.`);
        }
    }

    function removeFromCart(productId) {
        let cart = JSON.parse(localStorage.getItem('cart') || '[]');
        cart = cart.filter(item => item.id !== productId);
        localStorage.setItem('cart', JSON.stringify(cart));
        location.reload();
    }

    async function updateStockInGoogleSheets(cartItems) {
        try {
            const response = await fetch('/api/update_stock', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ cart: cartItems }),
            });

            const result = await response.json();
            if (response.ok) {
                console.log('Остатки успешно обновлены в Google Sheets:', result);
            } else {
                console.error('Ошибка обновления остатков:', result.error);
                alert('Не удалось обновить остатки в Google Sheets.');
            }
        } catch (error) {
            console.error('Ошибка при обновлении остатков в Google Sheets:', error);
        }
    }

    function clearCart() {
        console.log("Очищаем корзину и кэш.");
        localStorage.removeItem('cart'); // Удаляем корзину из localStorage
        location.reload(); // Перезагружаем страницу
    }

    function PDFGenerator(cartItems, projectName, deliveryDate, returnDate) {
        try {
            if (!Array.isArray(cartItems) || cartItems.length === 0) {
                alert("Корзина пуста или данные некорректны");
                return;
            }

            const { jsPDF } = window.jspdf;
            const doc = new jsPDF();
            doc.addFont("/static/fonts/arial.ttf", "Arial", "normal");
            doc.setFont("Arial", "normal");

            doc.setFontSize(16);
            const title = "Позиции на отгрузку";
            doc.text(title, 14, 20);

            const headers = [["ID", "Название", "Кол-во", "Остаток"]];
            const data = cartItems.map(item => [
                String(item.id ?? ""),
                String(item.name ?? ""),
                String(item.quantity ?? ""),
                String(stockData[item.id] ?? "0")
            ]);

            doc.autoTable({
                head: headers,
                body: data,
                startY: 30,
                headStyles: {
                    fillColor: [78, 92, 128],
                    textColor: [255, 255, 255],
                    fontStyle: "bold"
                },
                styles: {
                    fontSize: 10,
                    font: "Arial"
                }
            });

            const endY = doc.autoTable.previous.finalY || 40;
            const footerData = [
                `Проект: ${projectName ?? "-"}`,
                `Срок: ${(deliveryDate ?? "-")} — ${(returnDate ?? "-")}`
            ];

            doc.setFontSize(12);
            footerData.forEach((line, i) => doc.text(line, 14, endY + 10 + i * 10));

            doc.save("order.pdf");
            console.log("PDF сгенерирован и сохранён");
        } catch (error) {
            console.error("Ошибка генерации PDF:", error);
            alert("Не удалось сгенерировать PDF.");
        }
    }
});