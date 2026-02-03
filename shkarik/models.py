from django.db import models
import random
import string
import secrets

class Product(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField()
    price = models.IntegerField()
    image = models.ImageField(upload_to='products/')
    available = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class Order(models.Model):
    STATUS_CHOICES = [
        ('new', 'В очереди'),
        ('cooking', 'Готовится'),
        ('ready', 'Готов'),
        ('delivering', 'Доставляется'),
        ('completed', 'Выполнен'),
        ('cancelled', 'Отменен'),
    ]
    
    DELIVERY_CHOICES = [
        ('pickup', 'Самовывоз'),
        ('delivery', 'Доставка'),
    ]

    secret_code = models.CharField(max_length=50, unique=True)
    public_code = models.CharField(max_length=10, unique=True)

    client_name = models.CharField(max_length=100)
    client_phone = models.CharField(max_length=20)

    delivery_type = models.CharField(max_length=20, choices=DELIVERY_CHOICES)
    address = models.TextField(blank=True)
    scheduled_time = models.CharField(max_length=50, blank=True)
    comment = models.TextField(blank=True)
    total_price = models.IntegerField()

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new')
    accepted_by = models.CharField(max_length=50, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    

    def __str__(self):
        return f"Заказ {self.public_code}"

    def save(self, *args, **kwargs):
        if not self.secret_code:
            self.secret_code = self.generate_secret_code()
        if not self.public_code:
            self.public_code = self.generate_public_code()
        super().save(*args, **kwargs)

    @staticmethod
    def generate_secret_code():
        while True:
            token = secrets.token_urlsafe(16)
            if not Order.objects.filter(secret_code=token).exists():
                return token

    @staticmethod
    def generate_public_code():
        while True:
            code = '#' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
            if not Order.objects.filter(public_code=code).exists():
                return code


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product_name = models.CharField(max_length=200)
    product_price = models.IntegerField()
    quantity = models.IntegerField()

    def __str__(self):
        return f"{self.product_name} x{self.quantity}"

    @property
    def total_price(self):
        return self.product_price * self.quantity


class Courier(models.Model):
    """Курьер с уникальным кодом"""
    name = models.CharField(max_length=100, verbose_name="Имя курьера")
    code = models.CharField(max_length=20, unique=True, verbose_name="Код доступа")
    phone = models.CharField(max_length=20, blank=True, verbose_name="Телефон")
    is_active = models.BooleanField(default=True, verbose_name="Активен")
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.name} ({self.code})"
    
    class Meta:
        verbose_name = "Курьер"
        verbose_name_plural = "Курьеры"


class Chef(models.Model):
    """Повар с кодом доступа"""
    name = models.CharField(max_length=100, verbose_name="Имя повара")
    code = models.CharField(max_length=20, unique=True, verbose_name="Код доступа")
    is_active = models.BooleanField(default=True, verbose_name="Активен")
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.name} ({self.code})"
    
    class Meta:
        verbose_name = "Повар"
        verbose_name_plural = "Повара"