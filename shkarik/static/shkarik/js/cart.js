// === ЗАГРУЗКА КОРЗИНЫ ===
function loadCart() {
  const cart = JSON.parse(localStorage.getItem('cart')) || [];
  const cartContainer = document.querySelector('main');
  
  // Очистить существующие товары (кроме заголовка и формы)
  document.querySelectorAll('.cart-item').forEach(item => item.remove());
  
  if (cart.length === 0) {
    // Пустая корзина
    const emptyMsg = document.createElement('p');
    emptyMsg.textContent = 'Корзина пуста';
    emptyMsg.style.textAlign = 'center';
    emptyMsg.style.color = '#ccc';
    emptyMsg.style.margin = '40px 0';
    cartContainer.insertBefore(emptyMsg, document.querySelector('.checkout-block'));
    
    // Скрыть форму
    document.querySelector('.checkout-block').style.display = 'none';
    return;
  }
  
  // Показать форму
  document.querySelector('.checkout-block').style.display = 'block';
  
  // Отобразить товары
  cart.forEach((product, index) => {
    const cartItem = document.createElement('div');
    cartItem.className = 'cart-item';
    cartItem.innerHTML = `
      <img src="${product.image}" alt="${product.name}">
      <div class="cart-details">
        <h3>${product.name}</h3>
        <p>${product.price} сом × ${product.quantity}</p>
      </div>
      <div class="cart-actions">
        <button class="cart-decrease" data-index="${index}">−</button>
        <span>${product.quantity}</span>
        <button class="cart-increase" data-index="${index}">+</button>
      </div>
      <div class="cart-price">${product.price * product.quantity}с</div>
      <button class="cart-remove" data-index="${index}">🗑️</button>
    `;
    
    cartContainer.insertBefore(cartItem, document.querySelector('.checkout-block'));
  });
  
  // Обновить итоговую сумму
  updateTotal();
  
  // Добавить обработчики
  addCartEventListeners();
}

// === ОБНОВЛЕНИЕ ИТОГОВОЙ СУММЫ ===
function updateTotal() {
  const cart = JSON.parse(localStorage.getItem('cart')) || [];
  const deliveryType = document.querySelector('input[name="delivery"]:checked').value;
  
  let total = cart.reduce((sum, item) => sum + (item.price * item.quantity), 0);
  
  // Добавить доставку если нужно
  if (deliveryType === 'delivery') {
    total += 50; // Стоимость доставки
  }
  
  document.querySelector('.total').textContent = `Итого: ${total}с`;
}

// === ОБРАБОТЧИКИ СОБЫТИЙ ===
function addCartEventListeners() {
  document.querySelectorAll('.cart-increase').forEach(btn => {
    btn.addEventListener('click', () => {
      const index = parseInt(btn.dataset.index);
      updateQuantity(index, 1);
    });
  });
  
  document.querySelectorAll('.cart-decrease').forEach(btn => {
    btn.addEventListener('click', () => {
      const index = parseInt(btn.dataset.index);
      updateQuantity(index, -1);
    });
  });
  
  document.querySelectorAll('.cart-remove').forEach(btn => {
    btn.addEventListener('click', () => {
      const index = parseInt(btn.dataset.index);
      removeFromCart(index);
    });
  });
}

// === ИЗМЕНЕНИЕ КОЛИЧЕСТВА ===
function updateQuantity(index, change) {
  let cart = JSON.parse(localStorage.getItem('cart')) || [];
  cart[index].quantity += change;
  if (cart[index].quantity <= 0) cart.splice(index, 1);
  localStorage.setItem('cart', JSON.stringify(cart));
  loadCart();
}

// === УДАЛЕНИЕ ТОВАРА ===
function removeFromCart(index) {
  let cart = JSON.parse(localStorage.getItem('cart')) || [];
  cart.splice(index, 1);
  localStorage.setItem('cart', JSON.stringify(cart));
  loadCart();
}

// === ПОКАЗАТЬ/СКРЫТЬ БЛОКИ ===
const deliveryRadios = document.querySelectorAll('input[name="delivery"]');
const addressBlock = document.querySelector('.address-block');
const delayedCheckbox = document.getElementById('delayed');
const timeBlock = document.querySelector('.time-block');

deliveryRadios.forEach(r => {
  r.addEventListener('change', () => {
    addressBlock.style.display = r.value === 'delivery' ? 'block' : 'none';
    updateTotal();
  });
});

delayedCheckbox.addEventListener('change', () => {
  timeBlock.style.display = delayedCheckbox.checked ? 'block' : 'none';
});

// === ОТПРАВКА ЗАКАЗА ===
document.querySelector('.confirm-btn').addEventListener('click', () => {
  const cart = JSON.parse(localStorage.getItem('cart')) || [];
  
  if (cart.length === 0) {
    alert('Корзина пуста!');
    return;
  }
  
  const orderData = {
    client_name: document.querySelector('input[placeholder="Введите ваше имя"]').value.trim(),
    client_phone: document.querySelector('input[placeholder="+996 XXX XXX XXX"]').value.trim(),
    delivery_type: document.querySelector('input[name="delivery"]:checked').value,
    address: document.querySelector('.address-block input')?.value.trim() || '',
    scheduled_time: document.querySelector('.time-block input')?.value || '',
    comment: document.querySelector('textarea').value.trim(),
    cart: cart
  };
  
  // === Валидация ===
  if (!orderData.client_name) {
    alert('Введите ваше имя!');
    return;
  }
  
  if (!orderData.client_phone) {
    alert('Введите номер телефона!');
    return;
  }
  
  const phoneRegex = /^(\+?996|0)[0-9]{9}$/;
  if (!phoneRegex.test(orderData.client_phone.replace(/\s/g, ''))) {
    alert('Неверный формат телефона!\nПример: +996 700 123 456');
    return;
  }
  
  if (orderData.delivery_type === 'delivery' && !orderData.address) {
    alert('Укажите адрес доставки!');
    return;
  }
  
  // === Отправка ===
  const btn = document.querySelector('.confirm-btn');
  const originalText = btn.textContent;
  btn.textContent = 'Отправка...';
  btn.disabled = true;
  
  fetch('/create-order/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': getCookie('csrftoken')
    },
    body: JSON.stringify(orderData)
  })
  .then(response => response.json())
  .then(data => {
    if (data.success) {
      localStorage.removeItem('cart');
      window.location.href = `/order-success/${data.secret_code}/`;
    } else {
      alert('Ошибка: ' + data.error);
      btn.textContent = originalText;
      btn.disabled = false;
    }
  })
  .catch(() => {
    alert('Не удалось отправить заказ. Проверьте подключение к интернету.');
    btn.textContent = originalText;
    btn.disabled = false;
  });
});


// === ПОЛУЧИТЬ CSRF ТОКЕН ===
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

// === ЗАГРУЗИТЬ КОРЗИНУ ПРИ ОТКРЫТИИ ===
loadCart();
