// --- Контейнер для заказов ---
const wrapper = document.querySelector('.orders-wrapper');

// --- Хранилище подтверждений ---
let confirmStack = {};

// --- Пинг каждые 5 сек ---
setInterval(loadOrders, 5000);
loadOrders();

// --- Функция загрузки ---
function loadOrders() {
    fetch('/api/orders/')
        .then(r => {
            if (r.status === 401) {
                // Не авторизован - перенаправить на вход
                window.location.href = '/chef/login/';
                return;
            }
            return r.json();
        })
        .then(data => {
            if (data) {
                renderOrders(data.orders);
            }
        })
        .catch(err => {
            console.error('Ошибка загрузки заказов:', err);
        });
}

// --- Рендер ---
function renderOrders(orders) {
    wrapper.innerHTML = '';

    if (orders.length === 0) {
        wrapper.innerHTML = '<p style="text-align:center; color:#ccc; margin-top:50px;">Нет активных заказов</p>';
        return;
    }

    orders.forEach(order => {
        let productsHTML = '';
        order.items.forEach(i => {
            productsHTML += `
                <div class="price-line"><span>${i.name} x${i.qty}</span><span>${i.price * i.qty}</span></div>
            `;
        });

        wrapper.innerHTML += `
        <div class="container" id="ord-${order.public_code}">
            <div class="title">${order.public_code} — ${order.scheduled_time || 'По готовности'}</div>

            <div class="block"><div class="line">${order.client_name}</div></div>

            <div class="block">
                ${productsHTML}
                <div class="price-line"><span>${order.delivery_type === 'delivery' ? 'Доставка' : 'Самовывоз'}</span><span>${order.delivery_type === 'delivery' ? '50' : '—'}</span></div>
                <div class="sum">${order.total_price} сом</div>
            </div>

            ${order.comment ? `<div class="block"><div class="comment">${order.comment}</div></div>` : ''}

            <div class="block bottom">
                <div class="btns">
                    ${order.status === 'new' ? `<div class="btn yellow" onclick="confirmAction('${order.public_code}','cooking', this)">Готовить</div>` : ''}
                    <div class="btn green" onclick="confirmAction('${order.public_code}','ready', this)">Готово</div>
                    <div class="btn red" onclick="confirmAction('${order.public_code}','cancelled', this)">Отмена</div>
                </div>
            </div>
        </div>`;
    });
}

// --- Подтверждение кнопок ---
function confirmAction(code, status, btn) {
    const key = code + status;
    const now = Date.now();

    // Если не было первого нажатия
    if (!confirmStack[key]) {
        confirmStack[key] = now;
        btn.style.opacity = "0.6";
        btn.textContent = "Подтвердите...";
        return;
    }

    // Если прошло более 5 секунд — заново
    if (now - confirmStack[key] > 5000) {
        confirmStack[key] = now;
        btn.style.opacity = "0.6";
        btn.textContent = "Подтвердите...";
        return;
    }

    // Второе нажатие — действуем
    delete confirmStack[key];
    btn.style.opacity = "1";

    setStatus(code, status);

    // Если нажали "Готовить" → скрыть эту кнопку
    if (status === "cooking") {
        btn.style.display = "none";
    }

    // Если готов — скрываем заказ из UI
    if (status === "ready") {
        const block = document.getElementById("ord-" + code);
        if (block) block.remove();
    }
}

// --- Обновление статуса ---
function setStatus(code, status) {
    fetch('/api/update/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify({
            public_code: code,
            status: status
        })
    })
    .then(r => {
        if (r.status === 401) {
            window.location.href = '/chef/login/';
        }
        return r.json();
    })
    .catch(err => {
        console.error('Ошибка обновления статуса:', err);
    });
}

// --- Обновление статуса ---
function setStatus(code, status) {
    fetch('/api/update/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')  // ← ДОБАВИТЬ
        },
        body: JSON.stringify({
            public_code: code,
            status: status
        })
    })
    .then(r => {
        if (r.status === 401) {
            window.location.href = '/chef/login/';
        }
        return r.json();
    })
    .catch(err => {
        console.error('Ошибка обновления статуса:', err);
    });
}

// --- CSRF токен ---
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}