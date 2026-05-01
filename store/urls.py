from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("login/", views.customer_login, name="customer_login"),
    path("register/", views.customer_register, name="customer_register"),
    path("logout/", views.customer_logout, name="customer_logout"),
    path("add-to-cart/<int:product_id>/", views.add_to_cart, name="add_to_cart"),
    path("order-now/<int:product_id>/", views.order_now, name="order_now"),
    path("cart/", views.cart, name="cart"),
    path("checkout/", views.checkout, name="checkout"),
    path("my-orders/", views.my_orders, name="my_orders"),
    path("remove-order/<int:order_id>/", views.remove_order, name="remove_order"),
    path(
        "update-cart/<int:product_id>/<str:action>/",
        views.update_cart_quantity,
        name="update_cart_quantity",
    ),
    path("remove-from-cart/<int:product_id>/", views.remove_from_cart, name="remove_from_cart"),
]