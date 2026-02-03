from django.urls import path
from . import views

urlpatterns = [
    # Главная и корзина
    path('', views.home, name='home'),
    path('cart/', views.cart_view, name='cart'),
    
    # Повар
    path('chef/login/', views.chef_login, name='chef_login'),
    path('chef/panel/', views.chef_panel, name='chef_panel'),
    path('chef/logout/', views.chef_logout, name='chef_logout'),
    path('api/orders/', views.get_orders),
    path('api/update/', views.update_status),
    
    # Курьер
    path('courier/login/', views.courier_login, name='courier_login'),
    path('courier/orders/', views.courier_orders, name='courier_orders'),
    path('courier/logout/', views.courier_logout, name='courier_logout'),
    path('api/courier/', views.get_courier_orders),
    
    # Заказы
    path('create-order/', views.create_order, name='create_order'),
    path('order-success/<str:secret_code>/', views.order_success, name='order_success'),

    # Дашборд владельца (только для админов)
    path('xjf8k2n9s/', views.owner_dashboard, name='owner_dashboard'),
]