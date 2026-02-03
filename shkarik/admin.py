from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from django.db.models import Sum
from .models import Product, Order, OrderItem, Courier, Chef


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'available')
    list_filter = ('available',)
    search_fields = ('name',)


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('product_name', 'product_price', 'quantity', 'item_total')
    can_delete = False
    
    def item_total(self, obj):
        return f"{obj.total_price} сом"
    item_total.short_description = 'Сумма'
    
    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        'public_code',
        'client_name',
        'client_phone',
        'delivery_type',
        
        'courier_link',  # НОВОЕ - ссылка на курьера
        
        'status',
        'total_price',
        'created_at'
    )
    
    list_filter = ('status', 'delivery_type', 'created_at', 'accepted_by')
    search_fields = ('public_code', 'client_name', 'client_phone', 'accepted_by')
    readonly_fields = ('public_code', 'created_at')
    inlines = [OrderItemInline]
    
    # НОВОЕ - показать ссылку на курьера в списке заказов
    def courier_link(self, obj):
        if obj.accepted_by:
            try:
                courier = Courier.objects.get(code=obj.accepted_by)
                url = reverse('admin:shkarik_courier_change', args=[courier.id])
                return format_html('<a href="{}">{}</a>', url, courier.name)
            except Courier.DoesNotExist:
                return obj.accepted_by
        return '—'
    courier_link.short_description = 'Курьер'
    
    fieldsets = (
        ('Информация о заказе', {
            'fields': ('public_code', 'status', 'created_at')
        }),
        ('Клиент', {
            'fields': ('client_name', 'client_phone')
        }),
        ('Доставка', {
            'fields': ('delivery_type', 'address', 'scheduled_time', 'accepted_by')
        }),
        ('Дополнительно', {
            'fields': ('comment', 'total_price')
        }),
    )


@admin.register(Courier)
class CourierAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'code',
        'phone',
        'is_active',
        
        'total_deliveries',  # НОВОЕ - всего доставок
        
        'created_at'
    )
    list_filter = ('is_active',)
    search_fields = ('name', 'code', 'phone')
    list_editable = ('is_active',)
    
    readonly_fields = ('created_at', 'delivery_history')  # НОВОЕ
    
    # НОВОЕ - показать сколько всего доставок
    def total_deliveries(self, obj):
        count = Order.objects.filter(
            accepted_by=obj.code,
            status='completed'
        ).count()
        return f"{count} шт"
    total_deliveries.short_description = 'Всего доставок'
    
    # НОВОЕ - показать историю всех доставок
    def delivery_history(self, obj):
        orders = Order.objects.filter(
            accepted_by=obj.code
        ).order_by('-created_at')[:50]  # Последние 50 заказов
        
        if not orders:
            return "Нет доставок"
        
        # Статистика
        total_count = orders.count()
        completed_count = orders.filter(status='completed').count()
        total_revenue = orders.filter(status='completed').aggregate(
            Sum('total_price')
        )['total_price__sum'] or 0
        
        html = f"""
        <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; margin-top: 10px;">
            <h3 style="color: #333; margin-bottom: 15px;">📊 Статистика курьера</h3>
            
            <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 15px; margin-bottom: 20px;">
                <div style="background: white; padding: 15px; border-radius: 5px; text-align: center;">
                    <div style="font-size: 28px; font-weight: bold; color: #007bff;">{total_count}</div>
                    <div style="color: #666; font-size: 14px;">Всего заказов</div>
                </div>
                <div style="background: white; padding: 15px; border-radius: 5px; text-align: center;">
                    <div style="font-size: 28px; font-weight: bold; color: #28a745;">{completed_count}</div>
                    <div style="color: #666; font-size: 14px;">Выполнено</div>
                </div>
                <div style="background: white; padding: 15px; border-radius: 5px; text-align: center;">
                    <div style="font-size: 28px; font-weight: bold; color: #ffc107;">{total_revenue:,}</div>
                    <div style="color: #666; font-size: 14px;">Выручка (сом)</div>
                </div>
            </div>
            
            <h4 style="color: #333; margin-bottom: 10px;">📦 История доставок (последние 50):</h4>
            <table style="width: 100%; border-collapse: collapse; background: white; border-radius: 5px; overflow: hidden;">
                <thead>
                    <tr style="background: #007bff; color: white;">
                        <th style="padding: 12px; text-align: left;">№</th>
                        <th style="padding: 12px; text-align: left;">Заказ</th>
                        <th style="padding: 12px; text-align: left;">Клиент</th>
                        <th style="padding: 12px; text-align: left;">Адрес</th>
                        <th style="padding: 12px; text-align: left;">Сумма</th>
                        <th style="padding: 12px; text-align: left;">Статус</th>
                        <th style="padding: 12px; text-align: left;">Дата</th>
                    </tr>
                </thead>
                <tbody>
        """
        
        for idx, order in enumerate(orders, 1):
            # Цвет статуса
            status_colors = {
                'completed': '#28a745',
                'delivering': '#007bff',
                'ready': '#ffc107',
                'cancelled': '#dc3545'
            }
            status_color = status_colors.get(order.status, '#6c757d')
            status_text = dict(Order.STATUS_CHOICES).get(order.status, order.status)
            
            # Ссылка на заказ
            order_url = reverse('admin:shkarik_order_change', args=[order.id])
            
            # Цвет строки (чередование)
            row_bg = '#f8f9fa' if idx % 2 == 0 else 'white'
            
            html += f"""
                <tr style="background: {row_bg}; border-bottom: 1px solid #dee2e6;">
                    <td style="padding: 12px;">{idx}</td>
                    <td style="padding: 12px;">
                        <a href="{order_url}" style="color: #007bff; text-decoration: none; font-weight: bold;">
                            {order.public_code}
                        </a>
                    </td>
                    <td style="padding: 12px;">{order.client_name}</td>
                    <td style="padding: 12px; font-size: 13px; max-width: 200px; overflow: hidden; text-overflow: ellipsis;">
                        {order.address if order.address else '—'}
                    </td>
                    <td style="padding: 12px; font-weight: bold;">{order.total_price} сом</td>
                    <td style="padding: 12px;">
                        <span style="background: {status_color}; color: white; padding: 4px 10px; border-radius: 12px; font-size: 12px; font-weight: bold;">
                            {status_text}
                        </span>
                    </td>
                    <td style="padding: 12px; font-size: 13px; color: #666;">
                        {order.created_at.strftime('%d.%m.%Y %H:%M')}
                    </td>
                </tr>
            """
        
        html += """
                </tbody>
            </table>
        </div>
        """
        
        return format_html(html)
    
    delivery_history.short_description = 'История доставок'
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('name', 'code', 'phone', 'is_active', 'created_at')
        }),
        ('История доставок', {
            'fields': ('delivery_history',),
            'classes': ('wide',),  # Широкий блок
        }),
    )


@admin.register(Chef)
class ChefAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'is_active', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('name', 'code')
    list_editable = ('is_active',)