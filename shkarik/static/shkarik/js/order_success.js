// Функция скриншота
function takeScreenshot() {
  alert(
    "📸 Как сделать скриншот:\n\n" +
    "На Android: Кнопка питания + громкость вниз\n" +
    "На iPhone: Боковая кнопка + громкость вверх\n" +
    "На Windows: Win + Shift + S\n" +
    "На Mac: Cmd + Shift + 4"
  );
}

// Функция отмены заказа
function cancelOrder() {
  if (confirm('❌ Отменить заказ?\n\nЗаказ может уже готовиться!')) {
    fetch('/cancel-order/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCookie('csrftoken')
      },
      body: JSON.stringify({
        secret_code: '{{ order.secret_code }}'
      })
    })
    .then(r => r.json())
    .then(data => {
      if (data.success) {
        alert('✅ Заказ отменён');
        location.reload();
      } else {
        alert('❌ ' + data.error);
      }
    })
    .catch(() => {
      alert('❌ Ошибка. Попробуйте позвонить: +996 223 515 353');
    });
  }
}

// CSRF токен
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