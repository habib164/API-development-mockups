from django.contrib import admin
from .models import Category, MenuItem, OrderItem, Order, Cart
# Register your models here.
admin.site.register(MenuItem)
admin.site.register(Category)
admin.site.register(OrderItem)
admin.site.register(Order)
admin.site.register(Cart)