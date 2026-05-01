from django.contrib import admin
from .models import Cart, Order, OrderItem, Product

# Register models so they appear in Django admin panel
admin.site.register(Product)
admin.site.register(Cart)
admin.site.register(Order)
admin.site.register(OrderItem)
