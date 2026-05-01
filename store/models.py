from django.contrib.auth.models import User
from django.db import models


class Product(models.Model):
    # Basic product details shown on the home page
    name = models.CharField(max_length=200)
    price = models.FloatField()
    image = models.URLField()
    description = models.TextField()

    def __str__(self):
        return self.name


class Cart(models.Model):
    # Each row represents one product entry in cart
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)

    def __str__(self):
        username = self.user.username if self.user else "guest"
        return f"{username} - {self.product.name} - {self.quantity}"

    def total_price(self):
        # Helpful method used in cart page total calculations
        return self.product.price * self.quantity


class Order(models.Model):
    # Basic order record for each checkout
    PAYMENT_CHOICES = [
        ("cod", "Cash on Delivery"),
        ("upi", "UPI"),
        ("card", "Credit/Debit Card"),
        ("net_banking", "Net Banking"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    total_amount = models.FloatField(default=0)
    payment_method = models.CharField(max_length=30, choices=PAYMENT_CHOICES, default="cod")
    status = models.CharField(max_length=30, default="Placed")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order #{self.id} - {self.user.username}"


class OrderItem(models.Model):
    # Items that belong to one order
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)
    price = models.FloatField(default=0)

    def __str__(self):
        return f"{self.product.name} x {self.quantity}"

    def item_total(self):
        return self.price * self.quantity
