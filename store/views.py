from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db import transaction
from django.db.models import Q, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.http import url_has_allowed_host_and_scheme

from .models import Cart, Order, OrderItem, Product


def get_cart_count(user):
    # Total quantity shown as cart badge in navbar for logged-in user only
    if not user.is_authenticated:
        return 0
    return Cart.objects.filter(user=user).aggregate(total_items=Sum("quantity"))["total_items"] or 0


def format_indian_currency(value):
    # Format numbers like 175000 -> 1,75,000.00
    try:
        number = float(value)
    except (TypeError, ValueError):
        return str(value)

    whole_part, decimal_part = f"{number:.2f}".split(".")
    if len(whole_part) > 3:
        last_three = whole_part[-3:]
        remaining = whole_part[:-3]
        groups = []
        while len(remaining) > 2:
            groups.insert(0, remaining[-2:])
            remaining = remaining[:-2]
        if remaining:
            groups.insert(0, remaining)
        whole_part = ",".join(groups + [last_three])

    return f"{whole_part}.{decimal_part}"


@login_required(login_url="customer_login")
def home(request):
    # Optional search query from URL: /?q=iphone
    query = request.GET.get("q", "").strip()

    # Show filtered products if search term exists
    products = Product.objects.all()
    if query:
        products = products.filter(Q(name__icontains=query) | Q(description__icontains=query))

    context = {
        "products": products,
        "query": query,
        "cart_count": get_cart_count(request.user),
    }
    return render(request, "store/home.html", context)


@login_required(login_url="customer_login")
def add_to_cart(request, product_id):
    # Get selected product or return 404 if invalid id
    product = get_object_or_404(Product, id=product_id)

    # If product already exists in cart, increase quantity
    cart_item, created = Cart.objects.get_or_create(product=product, user=request.user)
    if not created:
        cart_item.quantity += 1
        cart_item.save()

    # User feedback message after add action
    messages.success(request, f"{product.name} added to cart.")
    return redirect("home")


@login_required(login_url="customer_login")
def order_now(request, product_id):
    # Instantly place order for one product (skips cart)
    product = get_object_or_404(Product, id=product_id)

    with transaction.atomic():
        order = Order.objects.create(
            user=request.user,
            total_amount=product.price,
            payment_method="cod",
            status="Placed",
        )
        OrderItem.objects.create(
            order=order,
            product=product,
            quantity=1,
            price=product.price,
        )

    messages.success(request, f"Order #{order.id} placed for {product.name}.")
    return redirect("my_orders")


@login_required(login_url="customer_login")
def cart(request):
    # Fetch all cart rows from database
    cart_items = Cart.objects.select_related("product").filter(user=request.user)

    # Calculate grand total by summing each item's total_price()
    total = sum(item.total_price() for item in cart_items)

    context = {
        "cart_items": cart_items,
        "total": total,
        "formatted_total": format_indian_currency(total),
        "payment_choices": Order.PAYMENT_CHOICES,
        "cart_count": get_cart_count(request.user),
    }
    return render(request, "store/cart.html", context)


@login_required(login_url="customer_login")
def checkout(request):
    # Create an order from current cart items
    if request.method != "POST":
        return redirect("cart")

    cart_items = Cart.objects.select_related("product").filter(user=request.user)
    if not cart_items.exists():
        messages.warning(request, "Your cart is empty.")
        return redirect("cart")

    payment_method = request.POST.get("payment_method", "").strip()
    valid_payment_methods = [choice[0] for choice in Order.PAYMENT_CHOICES]
    if payment_method not in valid_payment_methods:
        messages.error(request, "Please select a valid payment method.")
        return redirect("cart")

    total = sum(item.total_price() for item in cart_items)

    with transaction.atomic():
        order = Order.objects.create(
            user=request.user,
            total_amount=total,
            payment_method=payment_method,
            status="Placed",
        )
        order_items = []
        for item in cart_items:
            order_items.append(
                OrderItem(
                    order=order,
                    product=item.product,
                    quantity=item.quantity,
                    price=item.product.price,
                )
            )
        OrderItem.objects.bulk_create(order_items)
        cart_items.delete()

    messages.success(request, f"Order #{order.id} placed successfully.")
    return redirect("my_orders")


@login_required(login_url="customer_login")
def my_orders(request):
    # Show logged-in customer's order history
    orders = Order.objects.filter(user=request.user).prefetch_related("items__product").order_by("-created_at")
    for order in orders:
        order.formatted_total = format_indian_currency(order.total_amount)
        for item in order.items.all():
            item.formatted_price = format_indian_currency(item.price)
            item.formatted_item_total = format_indian_currency(item.item_total())

    context = {
        "orders": orders,
        "cart_count": get_cart_count(request.user),
    }
    return render(request, "store/orders.html", context)


@login_required(login_url="customer_login")
def remove_order(request, order_id):
    # Allow customer to remove only "Placed" orders
    if request.method != "POST":
        return redirect("my_orders")

    order = get_object_or_404(Order, id=order_id, user=request.user)
    if order.status != "Placed":
        messages.error(request, "Only placed orders can be removed.")
        return redirect("my_orders")

    order.delete()
    messages.warning(request, f"Order #{order_id} removed successfully.")
    return redirect("my_orders")


@login_required(login_url="customer_login")
def update_cart_quantity(request, product_id, action):
    # Increase or decrease product quantity from cart page
    product = get_object_or_404(Product, id=product_id)
    cart_item = get_object_or_404(Cart, product=product, user=request.user)

    if action == "increase":
        cart_item.quantity += 1
        cart_item.save()
        messages.info(request, f"Increased quantity for {product.name}.")
    elif action == "decrease":
        if cart_item.quantity > 1:
            cart_item.quantity -= 1
            cart_item.save()
            messages.info(request, f"Decreased quantity for {product.name}.")
        else:
            cart_item.delete()
            messages.info(request, f"{product.name} removed from cart.")

    return redirect("cart")


@login_required(login_url="customer_login")
def remove_from_cart(request, product_id):
    # Delete product entry from cart page
    product = get_object_or_404(Product, id=product_id)
    Cart.objects.filter(product=product, user=request.user).delete()
    messages.warning(request, f"{product.name} removed from cart.")
    return redirect("cart")


def customer_login(request):
    # Handle customer login with username and password
    if request.user.is_authenticated:
        return redirect("home")

    next_url = request.POST.get("next") or request.GET.get("next") or ""

    if request.method == "POST":
        username_or_email = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")

        # Support login using either username or email
        matched_user = User.objects.filter(
            Q(username__iexact=username_or_email) | Q(email__iexact=username_or_email)
        ).first()
        auth_username = matched_user.username if matched_user else username_or_email

        user = authenticate(request, username=auth_username, password=password)

        if user:
            login(request, user)
            messages.success(request, f"Welcome back, {user.username}!")
            if next_url and url_has_allowed_host_and_scheme(
                next_url,
                allowed_hosts={request.get_host()},
                require_https=request.is_secure(),
            ):
                return redirect(next_url)
            return redirect("home")

        messages.error(request, "Invalid username/email or password.")

    return render(request, "store/login.html", {"next": next_url})


def customer_register(request):
    # Handle simple customer registration form
    if request.user.is_authenticated:
        return redirect("home")

    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        email = request.POST.get("email", "").strip()
        password = request.POST.get("password", "")
        confirm_password = request.POST.get("confirm_password", "")

        if not username or not password:
            messages.error(request, "Username and password are required.")
            return redirect("customer_register")

        if password != confirm_password:
            messages.error(request, "Password and confirm password do not match.")
            return redirect("customer_register")

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists. Please choose another one.")
            return redirect("customer_register")

        user = User.objects.create_user(username=username, email=email, password=password)
        login(request, user)
        messages.success(request, "Account created successfully. You are now logged in.")
        return redirect("home")

    return render(request, "store/register.html")


@login_required(login_url="customer_login")
def customer_logout(request):
    # Log out current user
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect("customer_login")
