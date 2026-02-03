const grid = document.getElementById('menuGrid');
let activeDetails = null;

grid.addEventListener('click', e => {
  const item = e.target.closest('.menu-item');
  if (!item) return;

  // если уже открыт — закрыть
  if (activeDetails && activeDetails.previousElementSibling === item) {
    activeDetails.remove();
    activeDetails = null;
    return;
  }

  // удалить прошлый блок
  if (activeDetails) activeDetails.remove();

  // вставить новый блок
  const detailsHTML = `
    <div class="details-block">
      <h4>Состав:</h4>
      <p>${item.dataset.info}</p>

      <div class="item-count">
        <button class="decrease">-</button>
        <p class="count-p">1</p>
        <button class="increase">+</button>
      </div>

      <button class="push-carton">Добавить в корзину</button>
    </div>`;

  item.insertAdjacentHTML('afterend', detailsHTML);
  activeDetails = item.nextElementSibling;

  // Найти элементы
  const countEl = activeDetails.querySelector('.count-p');
  const decBtn = activeDetails.querySelector('.decrease');
  const incBtn = activeDetails.querySelector('.increase');
  const addBtn = activeDetails.querySelector('.push-carton');

  let count = 1;

  // Кнопка "+"
  incBtn.addEventListener('click', () => {
    if(count < 50) {
      count++;
      countEl.textContent = count;
    }
  });

  // Кнопка "-"
  decBtn.addEventListener('click', () => {
    if (count > 1) {
      count--;
      countEl.textContent = count;
    }
  });

  // === ДОБАВЛЕНИЕ В КОРЗИНУ ===
  addBtn.addEventListener('click', () => {
    const product = {
      name: item.querySelector('h3').textContent.trim(),
      price: parseInt(item.querySelector('.price').textContent),
      quantity: count,
      image: item.querySelector('img').src
    };

    addToCart(product);
    
    // Показать уведомление
    addBtn.textContent = '✓ Добавлено!';
    addBtn.style.background = '#4caf50';
    
    setTimeout(() => {
      addBtn.textContent = 'Добавить в корзину';
      addBtn.style.background = '#ffcb05';
    }, 1500);
  });
});

// === ФУНКЦИИ РАБОТЫ С КОРЗИНОЙ ===
function addToCart(product) {
  // Получить корзину из localStorage
  let cart = JSON.parse(localStorage.getItem('cart')) || [];
  
  // Проверить, есть ли товар в корзине
  const existingProduct = cart.find(item => item.name === product.name);
  
  if (existingProduct) {
    // Если есть - увеличить количество
    existingProduct.quantity += product.quantity;
  } else {
    // Если нет - добавить новый
    cart.push(product);
  }
  
  // Сохранить в localStorage
  localStorage.setItem('cart', JSON.stringify(cart));
  
  // Обновить счетчик корзины (если есть)
  updateCartBadge();
}

function updateCartBadge() {
  const cart = JSON.parse(localStorage.getItem('cart')) || [];
  const totalItems = cart.reduce((sum, item) => sum + item.quantity, 0);
  
  // Можно добавить бейдж на кнопку "Корзина" в навигации
  const cartLink = document.querySelector('nav a[href*="cart"]');
  if (cartLink && totalItems > 0) {
    cartLink.textContent = `Корзина (${totalItems})`;
  }
}

// Вызвать при загрузке страницы
updateCartBadge();