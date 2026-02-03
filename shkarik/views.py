import json           # для работы с JSON
import re
from datetime import timedelta

from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils import timezone
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Q, Sum, Count
from django.db.models.functions import ExtractHour
from django_ratelimit.decorators import ratelimit

from .models import Product, Order, OrderItem, Courier, Chef



# ==================== ГЛАВНАЯ СТРАНИЦА ====================

@ensure_csrf_cookie
def home(request):
    products = Product.objects.filter(available=True)
    return render(request, 'shkarik/index.html', {'products': products})


# ==================== КОРЗИНА ====================

@ensure_csrf_cookie
def cart_view(request):
    return render(request, 'shkarik/cart.html')


# ==================== СОЗДАНИЕ ЗАКАЗА ====================

@ratelimit(key='ip', rate='10/m', method='POST')
@require_http_methods(["POST"])
def create_order(request):
    """Создание заказа с полной валидацией"""
    
    was_limited = getattr(request, 'limited', False)
    if was_limited:
        return JsonResponse({
            'success': False, 
            'error': 'Слишком много заказов. Подождите минуту.'
        }, status=429)
    
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Неверный формат данных'}, status=400)
    
    # === ВАЛИДАЦИЯ ИМЕНИ ===
    client_name = data.get('client_name', '').strip()
    
    if not client_name:
        return JsonResponse({'success': False, 'error': 'Введите ваше имя'}, status=400)
    
    if len(client_name) > 100:
        return JsonResponse({'success': False, 'error': 'Имя слишком длинное'}, status=400)
    
    if not re.match(r'^[а-яА-ЯёЁa-zA-Z\s]+$', client_name):
        return JsonResponse({
            'success': False, 
            'error': 'Имя должно содержать только буквы'
        }, status=400)
    
    # === ВАЛИДАЦИЯ ТЕЛЕФОНА ===
    client_phone = data.get('client_phone', '').strip().replace(' ', '')
    
    if not client_phone:
        return JsonResponse({'success': False, 'error': 'Введите номер телефона'}, status=400)
    
    if not re.match(r'^(\+996|996|0)\d{9}$', client_phone):
        return JsonResponse({
            'success': False, 
            'error': 'Неверный формат телефона. Пример: +996 700 123 456'
        }, status=400)
    
    if client_phone.startswith('0'):
        client_phone = '+996' + client_phone[1:]
    elif not client_phone.startswith('+'):
        client_phone = '+' + client_phone
    
    # === ВАЛИДАЦИЯ ТИПА ДОСТАВКИ ===
    delivery_type = data.get('delivery_type', '')
    
    if delivery_type not in ['pickup', 'delivery']:
        return JsonResponse({'success': False, 'error': 'Неверный тип доставки'}, status=400)
    
    # === ВАЛИДАЦИЯ АДРЕСА ===
    address = data.get('address', '').strip()
    
    if delivery_type == 'delivery':
        if not address:
            return JsonResponse({'success': False, 'error': 'Укажите адрес доставки'}, status=400)
        
        if len(address) > 500:
            return JsonResponse({'success': False, 'error': 'Адрес слишком длинный'}, status=400)
    
    # === ВАЛИДАЦИЯ КОРЗИНЫ ===
    cart = data.get('cart', [])
    
    if not cart or not isinstance(cart, list):
        return JsonResponse({'success': False, 'error': 'Корзина пуста'}, status=400)
    
    if len(cart) > 50:
        return JsonResponse({'success': False, 'error': 'Слишком много товаров в заказе'}, status=400)
    
    for item in cart:
        if not isinstance(item, dict):
            return JsonResponse({'success': False, 'error': 'Неверный формат товара'}, status=400)
        
        if 'name' not in item or 'price' not in item or 'quantity' not in item:
            return JsonResponse({'success': False, 'error': 'Неполные данные товара'}, status=400)
        
        try:
            price = int(item['price'])
            quantity = int(item['quantity'])
        except (ValueError, TypeError):
            return JsonResponse({'success': False, 'error': 'Неверные цена или количество'}, status=400)
        
        if price < 0 or price > 10000:
            return JsonResponse({'success': False, 'error': 'Подозрительная цена товара'}, status=400)
        
        if quantity < 1 or quantity > 100:
            return JsonResponse({'success': False, 'error': 'Неверное количество товара'}, status=400)
    
    # === ВАЛИДАЦИЯ КОММЕНТАРИЯ ===
    comment = data.get('comment', '').strip()
    
    if len(comment) > 1000:
        return JsonResponse({'success': False, 'error': 'Комментарий слишком длинный'}, status=400)
    
    # === ВАЛИДАЦИЯ ВРЕМЕНИ ===
    scheduled_time = data.get('scheduled_time', '').strip()
    
    if len(scheduled_time) > 50:
        return JsonResponse({'success': False, 'error': 'Неверное время'}, status=400)
    
    # === РАСЧЁТ СУММЫ ===
    try:
        total_price = sum(int(item['price']) * int(item['quantity']) for item in cart)
    except (ValueError, TypeError, KeyError):
        return JsonResponse({'success': False, 'error': 'Ошибка расчёта суммы'}, status=400)
    
    if delivery_type == 'delivery':
        total_price += 50
    
    if total_price > 100000:
        return JsonResponse({
            'success': False, 
            'error': 'Слишком большая сумма заказа. Свяжитесь с нами по телефону.'
        }, status=400)
    
    # === СОЗДАНИЕ ЗАКАЗА ===
    try:
        order = Order.objects.create(
            client_name=client_name,
            client_phone=client_phone,
            delivery_type=delivery_type,
            address=address,
            scheduled_time=scheduled_time,
            comment=comment,
            total_price=total_price,
            status='new'
        )
        
        for item in cart:
            OrderItem.objects.create(
                order=order,
                product_name=item['name'][:200],
                product_price=int(item['price']),
                quantity=int(item['quantity'])
            )
        
        return JsonResponse({
            'success': True,
            'public_code': order.public_code,
            'secret_code': order.secret_code,
            'total_price': total_price
        })
    
    except Exception as e:
        return JsonResponse({
            'success': False, 
            'error': 'Ошибка сервера. Попробуйте позже.'
        }, status=500)


# ==================== СТРАНИЦА УСПЕХА ====================

def order_success(request, secret_code):
    """Отслеживание заказа по секретному коду"""
    
    if len(secret_code) > 100:
        return render(request, 'shkarik/order_success.html', {'error': 'Неверная ссылка'})
    
    try:
        order = Order.objects.get(secret_code=secret_code)
        return render(request, 'shkarik/order_success.html', {'order': order})
    except Order.DoesNotExist:
        return render(request, 'shkarik/order_success.html', {'error': 'Заказ не найден'})


# ==================== ПОВАР - ЗАЩИЩЁННЫЙ ДОСТУП ====================

def chef_login(request):
    """Страница входа для повара"""
    
    if request.session.get('chef_code'):
        return redirect('chef_panel')
    
    if request.method == 'POST':
        code = request.POST.get('code', '').strip()
        
        if len(code) > 50:
            return render(request, 'shkarik/chef_login.html', {
                'error': 'Неверный код'
            })
        
        try:
            chef = Chef.objects.get(code=code, is_active=True)
            
            request.session['chef_code'] = chef.code
            request.session['chef_name'] = chef.name
            
            return redirect('chef_panel')
        
        except Chef.DoesNotExist:
            return render(request, 'shkarik/chef_login.html', {
                'error': 'Неверный код доступа'
            })
    
    return render(request, 'shkarik/chef_login.html')


@ensure_csrf_cookie
def chef_panel(request):
    """Панель повара - только для авторизованных"""
    
    chef_code = request.session.get('chef_code')
    if not chef_code:
        return redirect('chef_login')
    
    if not Chef.objects.filter(code=chef_code, is_active=True).exists():
        del request.session['chef_code']
        del request.session['chef_name']
        return redirect('chef_login')
    
    return render(request, 'shkarik/chef.html', {
        'chef_name': request.session.get('chef_name', 'Повар')
    })


def chef_logout(request):
    """Выход повара"""
    
    if 'chef_code' in request.session:
        del request.session['chef_code']
    if 'chef_name' in request.session:
        del request.session['chef_name']
    
    return redirect('chef_login')


@ratelimit(key='ip', rate='60/m', method='GET')
def get_orders(request):
    """API для получения заказов повара"""
    
    chef_code = request.session.get('chef_code')
    if not chef_code or not Chef.objects.filter(code=chef_code, is_active=True).exists():
        return JsonResponse({"error": "Unauthorized"}, status=401)
    
    orders = Order.objects.filter(
        status__in=['new', 'cooking']
    ).order_by('-created_at')[:50]
    
    return JsonResponse({
        "orders": [
            {
                "public_code": o.public_code,
                "client_name": o.client_name,
                "delivery_type": o.delivery_type,
                "scheduled_time": o.scheduled_time,
                "comment": o.comment,
                "status": o.status,
                "total_price": o.total_price,
                "items": [
                    {
                        "name": i.product_name,
                        "qty": i.quantity,
                        "price": i.product_price
                    } for i in o.items.all()
                ]
            } for o in orders
        ]
    })


@require_http_methods(["POST"])
@ratelimit(key='ip', rate='30/m', method='POST')
def update_status(request):
    """Обновление статуса - ТОЛЬКО для авторизованных"""
    
    chef_code = request.session.get('chef_code')
    courier_code_session = request.session.get('courier_code')
    
    is_chef = chef_code and Chef.objects.filter(code=chef_code, is_active=True).exists()
    is_courier = courier_code_session and Courier.objects.filter(code=courier_code_session, is_active=True).exists()
    
    if not (is_chef or is_courier):
        return JsonResponse({"success": False, "error": "Unauthorized"}, status=401)
    
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"success": False, "error": "Неверный формат"}, status=400)
    
    code = data.get('public_code', '').strip()
    status = data.get('status', '').strip()
    courier_accept = data.get('accepted_by', '').strip()
    
    valid_statuses = ['new', 'cooking', 'ready', 'delivering', 'completed', 'cancelled']
    if status not in valid_statuses:
        return JsonResponse({"success": False, "error": "Неверный статус"}, status=400)
    
    try:
        order = Order.objects.get(public_code=code)
    except Order.DoesNotExist:
        return JsonResponse({"success": False, "error": "Заказ не найден"}, status=404)
    
    if status == "delivering":
        if courier_accept and Courier.objects.filter(code=courier_accept, is_active=True).exists():
            order.accepted_by = courier_accept
        else:
            return JsonResponse({"success": False, "error": "Курьер не найден"}, status=400)
    
    if status in ["completed", "cancelled"]:
        order.accepted_by = None
    
    order.status = status
    order.save()
    
    return JsonResponse({"success": True})


# ==================== КУРЬЕР ====================

def courier_login(request):
    """Страница входа для курьера"""
    
    if request.session.get('courier_code'):
        return redirect('courier_orders')
    
    if request.method == 'POST':
        code = request.POST.get('code', '').strip()
        
        if len(code) > 50:
            return render(request, 'shkarik/courier_login.html', {
                'error': 'Неверный код'
            })
        
        try:
            courier = Courier.objects.get(code=code, is_active=True)
            
            request.session['courier_code'] = courier.code
            request.session['courier_name'] = courier.name
            
            return redirect('courier_orders')
        
        except Courier.DoesNotExist:
            return render(request, 'shkarik/courier_login.html', {
                'error': 'Неверный код доступа'
            })
    
    return render(request, 'shkarik/courier_login.html')


@ensure_csrf_cookie
def courier_orders(request):
    """Панель курьера - только для авторизованных"""
    
    courier_code = request.session.get('courier_code')
    if not courier_code:
        return redirect('courier_login')
    
    if not Courier.objects.filter(code=courier_code, is_active=True).exists():
        del request.session['courier_code']
        del request.session['courier_name']
        return redirect('courier_login')
    
    return render(request, 'shkarik/courier_orders.html', {
        'courier_code': courier_code,
        'courier_name': request.session.get('courier_name', 'Курьер')
    })


def courier_logout(request):
    """Выход курьера"""
    
    if 'courier_code' in request.session:
        del request.session['courier_code']
    if 'courier_name' in request.session:
        del request.session['courier_name']
    
    return redirect('courier_login')


@ratelimit(key='ip', rate='60/m', method='GET')
def get_courier_orders(request):
    """API для получения заказов курьера"""
    
    courier_code = request.GET.get("code", "").strip()
    
    if not Courier.objects.filter(code=courier_code, is_active=True).exists():
        return JsonResponse({"error": "Unauthorized"}, status=401)
    
    orders = Order.objects.filter(
        delivery_type='delivery'
    ).filter(
        Q(status='ready') |
        Q(status='delivering', accepted_by=courier_code)
    ).order_by('-created_at')[:20]
    
    return JsonResponse({
        "orders": [
            {
                "public_code": o.public_code,
                "address": o.address,
                "comment": o.comment,
                "status": o.status,
                "delivery_type": o.delivery_type,
                "scheduled_time": o.scheduled_time,
                "client_name": o.client_name,
                "client_phone": o.client_phone,
                "total_price": o.total_price,
            } for o in orders
        ]
    })


# ==================== ДАШБОРД ВЛАДЕЛЬЦА ====================

@staff_member_required
def owner_dashboard(request):
    """Дашборд владельца - только для админов"""
    now = timezone.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = today_start - timedelta(days=6)   # 7 дней: today + previous 6 (total 7)
    month_start = today_start - timedelta(days=30)

    # === ВЫРУЧКА ===
    revenue_today = Order.objects.filter(
        created_at__gte=today_start,
        status='completed'
    ).aggregate(total=Sum('total_price'))['total'] or 0

    revenue_week = Order.objects.filter(
        created_at__gte=week_start,
        status='completed'
    ).aggregate(total=Sum('total_price'))['total'] or 0

    revenue_month = Order.objects.filter(
        created_at__gte=month_start,
        status='completed'
    ).aggregate(total=Sum('total_price'))['total'] or 0

    # === ЗАКАЗЫ ===
    orders_today = Order.objects.filter(created_at__gte=today_start).count()
    orders_week = Order.objects.filter(created_at__gte=week_start).count()
    orders_month = Order.objects.filter(created_at__gte=month_start).count()

    # === ГРАФИК ПРОДАЖ ЗА НЕДЕЛЮ ===
    sales_by_day = []
    for i in range(7):
        day_start = week_start + timedelta(days=i)
        day_end = day_start + timedelta(days=1)
        total = Order.objects.filter(
            created_at__gte=day_start,
            created_at__lt=day_end,
            status='completed'
        ).aggregate(total=Sum('total_price'))['total'] or 0
        sales_by_day.append({
            'date': day_start.strftime('%d.%m'),
            'total': float(total)
        })

    # === ТОП-5 БЛЮД (за месяц) ===
    # Предполагается, что OrderItem хранит product_name, product_price и quantity
    top_dishes_qs = (OrderItem.objects
                     .filter(order__created_at__gte=month_start, order__status='completed')
                     .values('product_name', 'product_price')
                     .annotate(total_qty=Sum('quantity'))
                     .order_by('-total_qty')[:5])
    top_dishes_list = []
    for dish in top_dishes_qs:
        qty = int(dish['total_qty'] or 0)
        price = float(dish['product_price'] or 0)
        top_dishes_list.append({
            'name': dish['product_name'],
            'quantity': qty,
            'revenue': round(price * qty, 2)
        })

    # === ЗАКАЗЫ ПО ЧАСАМ ===
    orders_by_hour = (Order.objects
                      .filter(created_at__gte=today_start)
                      .annotate(hour=ExtractHour('created_at'))
                      .values('hour')
                      .annotate(count=Count('id'))
                      .order_by('hour'))

    # БК: разбивка в слоты, как у тебя в коде
    slots = {
        '09-12': 0,
        '12-14': 0,
        '14-18': 0,
        '18-20': 0,
        '20-22': 0,
    }
    for item in orders_by_hour:
        hour = int(item['hour'])
        c = item['count']
        if 9 <= hour < 12:
            slots['09-12'] += c
        elif 12 <= hour < 14:
            slots['12-14'] += c
        elif 14 <= hour < 18:
            slots['14-18'] += c
        elif 18 <= hour < 20:
            slots['18-20'] += c
        elif 20 <= hour < 22:
            slots['20-22'] += c

    total_today_orders = sum(slots.values()) or 0
    time_slots_data = []
    for k, v in slots.items():
        percent = round((v / total_today_orders * 100) if total_today_orders else 0)
        time_slots_data.append({'slot': k, 'count': v, 'percent': percent})

    # === КУРЬЕРЫ ===
    couriers_stats = []
    couriers = Courier.objects.all()
    for courier in couriers:
        deliveries_today = Order.objects.filter(
            accepted_by=courier.code,
            created_at__gte=today_start,
            delivery_type='delivery'
        ).count()
        is_active_now = Order.objects.filter(
            accepted_by=courier.code,
            status='delivering'
        ).exists()
        couriers_stats.append({
            'name': courier.name,
            'code': courier.code,
            'deliveries': deliveries_today,
            'is_active': is_active_now
        })

    context = {
        'revenue_today': revenue_today,
        'revenue_week': revenue_week,
        'revenue_month': revenue_month,
        'orders_today': orders_today,
        'orders_week': orders_week,
        'orders_month': orders_month,
        'sales_by_day': sales_by_day,
        'top_dishes': top_dishes_list,
        'time_slots': time_slots_data,
        'couriers_stats': couriers_stats,
    }
    return render(request, 'shkarik/owner_dashboard.html', context)