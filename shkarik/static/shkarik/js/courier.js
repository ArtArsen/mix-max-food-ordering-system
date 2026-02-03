document.addEventListener("DOMContentLoaded", () => {
    const wrapper = document.querySelector('.orders-wrapper');
    let activeOrderCode = localStorage.getItem("activeDelivery") || null;

    setInterval(loadOrders, 4000);
    loadOrders();

    function loadOrders() {
        fetch('/api/courier/?code=' + COURIER_CODE)
            .then(r => {
                if (r.status === 401) {
                    window.location.href = '/courier/login/';
                    return;
                }
                return r.json();
            })
            .then(data => {
                if (data) {
                    renderOrders(data.orders);
                }
            })
            .catch(err => console.error('Ошибка:', err));
    }

    function renderOrders(orders) {
        wrapper.innerHTML = "";

        const delivering = orders.find(o => o.status === "delivering");

        if (delivering) {
            activeOrderCode = delivering.public_code;
            localStorage.setItem("activeDelivery", activeOrderCode);
            wrapper.innerHTML = card(delivering);
            return;
        }

        activeOrderCode = null;
        localStorage.removeItem("activeDelivery");

        const readyOrders = orders.filter(o => o.status === "ready");
        
        readyOrders.forEach(o => wrapper.innerHTML += card(o));
        
        if (readyOrders.length === 0) {
            wrapper.innerHTML = '<p style="text-align:center; color:#ccc; margin-top:50px; font-size:20px;">Нет заказов на доставку</p>';
        }
    }

    function card(o) {
        const cardClass = o.status === "delivering" ? "taken" : "waiting";
        const hidden = o.status === "ready" ? "hide" : "";

        return `
        <div class="courier-card ${cardClass}" id="ord-${o.public_code}">
            <div class="code">${o.public_code}</div>

            <div class="field">📍 ${o.address}</div>
            <div class="field ${hidden}">🧑 ${o.client_name}</div>
            <div class="field ${hidden}">📞 <a href="tel:${o.client_phone}">${o.client_phone}</a></div>
            <div class="field ${hidden}">💬 ${o.comment || "—"}</div>

            <div class="price">💵 ${o.total_price} сом</div>

            <div class="actions">
                ${o.status === "ready"
                    ? `<button class="btn take" onclick="confirmTake('${o.public_code}')">🚚 Взять заказ</button>`
                    : `
                        <button class="btn success" onclick="confirmFinish('${o.public_code}')">✅ Доставлено</button>
                        <button class="btn fail" onclick="confirmFail('${o.public_code}')">❌ Не отвечает</button>
                    `
                }
            </div>
        </div>`;
    }

    // === ПРОВЕРКА КОДА ===
    function checkCode() {
        const inputCode = prompt('Введите ваш код для подтверждения:');
        
        if (inputCode === null) {
            return false;
        }
        
        if (inputCode.trim() === COURIER_CODE) {
            return true;
        } else {
            alert('❌ Неверный код!');
            return false;
        }
    }

    // === CSRF ТОКЕН ===
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

    // === ВЗЯТЬ ЗАКАЗ ===
    window.confirmTake = (code) => {
        if (!checkCode()) return;
        
        fetch("/api/update/", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": getCookie('csrftoken')  // ← ДОБАВЛЕНО!
            },
            body: JSON.stringify({
                public_code: code,
                status: "delivering",
                accepted_by: COURIER_CODE
            })
        })
        .then(r => r.json())
        .then(data => {
            if (data && data.success) {
                loadOrders();
            }
        });
    };

    // === ДОСТАВЛЕНО ===
    window.confirmFinish = (code) => {
        if (!checkCode()) return;
        
        fetch("/api/update/", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": getCookie('csrftoken')  // ← ДОБАВЛЕНО!
            },
            body: JSON.stringify({
                public_code: code,
                status: "completed"
            })
        })
        .then(r => r.json())
        .then(data => {
            if (data && data.success) {
                loadOrders();
            }
        });
    };

    // === НЕ ОТВЕЧАЕТ ===
    window.confirmFail = (code) => {
        if (!checkCode()) return;
        
        fetch("/api/update/", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": getCookie('csrftoken')  // ← ДОБАВЛЕНО!
            },
            body: JSON.stringify({
                public_code: code,
                status: "cancelled"
            })
        })
        .then(r => r.json())
        .then(data => {
            if (data && data.success) {
                loadOrders();
            }
        });
    };
});