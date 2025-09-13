# ===================================================================
# IMPORTS
# ===================================================================

# Standard Django Imports
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.paginator import Paginator
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Avg
from django.urls import reverse
from django.http import JsonResponse, HttpResponse
from django.core.exceptions import ValidationError
from django.contrib.auth.password_validation import validate_password
from django.contrib.staticfiles import finders
from django.template.loader import render_to_string

# Third-Party Imports
from weasyprint import HTML

# Local App Imports
from .models import (
    User, Product, Category, Contact, Review, CartItem, Order, OrderItem, 
    ProductImage, Wishlist, Coupon
)


# ===================================================================
# 1. CORE & STATIC PAGE VIEWS
# ===================================================================

def index(request):
    """Renders the homepage with featured categories and new arrival products."""
    new_arrivals = Product.objects.filter(is_available=True, stock__gt=0).order_by('-created_at')[:4]
    featured_categories = Category.objects.filter(is_active=True)[:3]
    context = {'new_arrivals': new_arrivals, 'featured_categories': featured_categories}
    return render(request, 'index.html', context)


def about(request):
    """Renders the about page with a random gallery of plant images."""
    all_images = ProductImage.objects.order_by('?')[:12]
    context = {'plant_images': all_images}
    return render(request, 'about.html', context)


def contact(request):
    """Handles the contact form submission."""
    if request.method == "POST":
        name = request.POST.get('name')
        email = request.POST.get('email')
        subject = request.POST.get('subject')
        message_text = request.POST.get('message')
        if not all([name, email, subject, message_text]):
            messages.error(request, "All fields are required.")
        else:
            Contact.objects.create(name=name, email=email, subject=subject, message=message_text)
            messages.success(request, "Thank you for your message!")
            return redirect('contact')
    return render(request, 'contact.html')


# ===================================================================
# 2. SHOP & PRODUCT VIEWS
# ===================================================================

def shop(request):
    """Renders the main shop page with filtering, searching, sorting, and pagination."""
    categories = Category.objects.filter(is_active=True)
    selected_category_ids = request.GET.getlist("categories")
    search_query = request.GET.get('search', None)
    sort_option = request.GET.get('sort', 'default')

    products_list = Product.objects.all()

    if search_query:
        products_list = products_list.filter(Q(name__icontains=search_query) | Q(description__icontains=search_query))
    if selected_category_ids:
        products_list = products_list.filter(category_id__in=selected_category_ids)

    if sort_option == 'price_asc':
        products_list = products_list.order_by('price')
    elif sort_option == 'price_desc':
        products_list = products_list.order_by('-price')
    elif sort_option == 'name_asc':
        products_list = products_list.order_by('name')
    else:
        products_list = products_list.order_by('-stock', '-created_at')

    wishlist_product_ids = []
    if request.user.is_authenticated:
        wishlist_product_ids = Wishlist.objects.filter(user=request.user).values_list('product_id', flat=True)

    paginator = Paginator(products_list, 6)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "categories": categories, "page_obj": page_obj, "selected_categories": [int(c) for c in selected_category_ids if c.isdigit()],
        "search_query": search_query, "sort_option": sort_option, "wishlist_product_ids": wishlist_product_ids,
    }
    return render(request, "shop.html", context)


def shop_details(request, product_id):
    """Renders the product detail page and handles review submission."""
    product = get_object_or_404(Product, id=product_id)
    product_images = product.images.all()
    related_products = Product.objects.filter(category=product.category).exclude(id=product.id)[:4]

    is_in_wishlist = False
    if request.user.is_authenticated:
        is_in_wishlist = Wishlist.objects.filter(user=request.user, product=product).exists()

    if request.method == "POST" and request.user.is_authenticated:
        Review.objects.create(product=product, user=request.user, rating=request.POST.get("rating", 5), comment=request.POST.get("comment"))
        messages.success(request, "Your review has been submitted.")
        return redirect("shop_details", product_id=product.id)
        
    context = {"product": product, "product_images": product_images, "related_products": related_products, "is_in_wishlist": is_in_wishlist}
    return render(request, "shop-details.html", context)


# ===================================================================
# 3. CART & COUPON VIEWS
# ===================================================================

@login_required(login_url='login_view')
def cart_view(request):
    """Renders the shopping cart page with totals and coupon info."""
    cart_items = CartItem.objects.filter(user=request.user).select_related('product')
    cart_subtotal = sum(item.get_total for item in cart_items)
    discount_amount = 0; final_total = cart_subtotal; coupon_code = None; coupon_discount_percent = 0
    
    coupon_id = request.session.get('coupon_id')
    if coupon_id:
        try:
            coupon = Coupon.objects.get(id=coupon_id, is_active=True)
            discount_amount = (cart_subtotal * coupon.discount_percent) / 100
            final_total = cart_subtotal - discount_amount
            coupon_code = coupon.code; coupon_discount_percent = coupon.discount_percent
        except Coupon.DoesNotExist:
            del request.session['coupon_id']

    context = {
        'cart_items': cart_items, 'cart_subtotal': cart_subtotal, 'discount_amount': discount_amount,
        'final_total': final_total, 'coupon_code': coupon_code, 'coupon_discount_percent': coupon_discount_percent,
    }
    return render(request, 'cart.html', context)


@login_required(login_url='login_view')
def add_to_cart(request, product_id):
    """Handles adding a product to the cart or updating its quantity, then redirects."""
    product = get_object_or_404(Product, id=product_id)
    if product.stock <= 0:
        messages.error(request, f"Sorry, '{product.name}' is out of stock.")
        return redirect('shop')
    
    quantity_from_form = int(request.POST.get('quantity', 1))
    cart_item, created = CartItem.objects.get_or_create(user=request.user, product=product)

    if created:
        cart_item.quantity = quantity_from_form
        messages.success(request, f"'{product.name}' was added to your cart.")
    else:
        cart_item.quantity += quantity_from_form
        messages.success(request, f"Quantity of '{product.name}' was updated.")
    
    cart_item.save()
    return redirect('cart_view')


@login_required(login_url='login_view')
def remove_from_cart(request, item_id):
    """Removes a single item from the cart."""
    get_object_or_404(CartItem, id=item_id, user=request.user).delete()
    messages.success(request, "Item removed from cart.")
    return redirect('cart_view')


@login_required(login_url='login_view')
def update_cart(request):
    """Updates quantities for all items in the cart from the cart page form."""
    if request.method == 'POST':
        for key, value in request.POST.items():
            if key.startswith('quantity_'):
                try:
                    item_id = int(key.split('_')[1]); quantity = int(value)
                    item = get_object_or_404(CartItem, id=item_id, user=request.user)
                    if quantity > 0:
                        item.quantity = quantity
                        item.save()
                    else:
                        item.delete()
                except (ValueError, CartItem.DoesNotExist):
                    continue
        messages.success(request, "Cart updated.")
    return redirect('cart_view')


def apply_coupon(request):
    """Applies a coupon code to the user's session."""
    if request.method == 'POST':
        code = request.POST.get('code')
        try:
            coupon = Coupon.objects.get(code__iexact=code, is_active=True)
            request.session['coupon_id'] = coupon.id
            messages.success(request, 'Coupon applied successfully!')
        except Coupon.DoesNotExist:
            request.session['coupon_id'] = None
            messages.error(request, 'This coupon is invalid or has expired.')
    return redirect('cart_view')


# ===================================================================
# 4. CHECKOUT & ORDER VIEWS
# ===================================================================

@login_required(login_url='login_view')
def checkout(request):
    """Handles the final checkout process, including stock validation and order creation."""
    cart_items = CartItem.objects.filter(user=request.user)
    cart_subtotal = sum(item.get_total for item in cart_items)
    if not cart_items:
        messages.warning(request, "Your cart is empty.")
        return redirect('shop')

    discount_amount = 0; final_total = cart_subtotal
    coupon_id = request.session.get('coupon_id')
    if coupon_id:
        try:
            coupon = Coupon.objects.get(id=coupon_id)
            discount_amount = (cart_subtotal * coupon.discount_percent) / 100
            final_total = cart_subtotal - discount_amount
        except Coupon.DoesNotExist:
            del request.session['coupon_id']

    if request.method == 'POST':
        for item in cart_items:
            if item.product.stock < item.quantity:
                messages.error(request, f"Sorry, '{item.product.name}' is out of stock.")
                return redirect('cart_view')

        new_order = Order.objects.create(
            user=request.user, full_name=request.POST.get('full_name'),
            email=request.POST.get('email'), phone=request.POST.get('phone'),
            address=request.POST.get('address'), city=request.POST.get('city'),
            state=request.POST.get('state'), postcode=request.POST.get('postcode'),
            total_price=final_total, payment_method='Cash on Delivery'
        )
        for item in cart_items:
            OrderItem.objects.create(order=new_order, product=item.product, quantity=item.quantity, price=item.product.price)
            item.product.stock -= item.quantity
            item.product.save()

        cart_items.delete()
        if 'coupon_id' in request.session:
            del request.session['coupon_id']
        
        messages.success(request, "Your order has been placed successfully!")
        return redirect('order_confirmation', order_id=new_order.id)

    context = {'cart_items': cart_items, 'cart_subtotal': cart_subtotal, 'discount_amount': discount_amount, 'final_total': final_total, 'coupon_code': coupon.code if coupon_id else None}
    return render(request, 'checkout.html', context)


@login_required(login_url='login_view')
def order_confirmation_view(request, order_id):
    """Displays the "Thank You" page after a successful order."""
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, 'order_confirmation.html', {'order': order})


@login_required(login_url='login_view')
def generate_invoice_pdf(request, order_id):
    """Generates a PDF invoice for a given order using WeasyPrint."""
    order = get_object_or_404(Order, id=order_id, user=request.user)
    context = {'order': order}
    html_string = render_to_string('invoice.html', context)
    pdf_file = HTML(string=html_string, base_url=request.build_absolute_uri()).write_pdf()
    response = HttpResponse(pdf_file, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="invoice_#{order.id}.pdf"'
    return response


# ===================================================================
# 5. AUTH, PROFILE & WISHLIST VIEWS
# ===================================================================

def login_view(request):
    """Handles user login."""
    if request.user.is_authenticated: return redirect('index')
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        user = authenticate(request, username=email, password=password)
        if user is not None:
            auth_login(request, user)
            messages.success(request, f"Welcome back, {user.full_name}!")
            return redirect('index')
        else:
            messages.error(request, "Invalid email or password.")
    return render(request, 'login.html')


def register_view(request):
    """Handles new user registration with password validation."""
    if request.user.is_authenticated: return redirect('index')
    if request.method == 'POST':
        password = request.POST.get('password')
        if password != request.POST.get('confirm_password'):
            messages.error(request, "Passwords do not match.")
            return redirect('register_view')
        try:
            validate_password(password)
        except ValidationError as e:
            messages.error(request, ". ".join(e.messages))
            return redirect('register_view')
        
        email = request.POST.get('email')
        if User.objects.filter(email=email).exists():
            messages.error(request, "An account with this email already exists.")
            return redirect('register_view')

        user = User.objects.create_user(
            email=email, password=password, 
            full_name=request.POST.get('full_name'), 
            phone=request.POST.get('phone')
        )
        auth_login(request, user)
        messages.success(request, f"Welcome, {user.full_name}! Your account has been created.")
        return redirect('index')
    return render(request, 'register.html')


def logout_view(request):
    """Logs the user out."""
    auth_logout(request)
    messages.success(request, "You have been logged out successfully.")
    return redirect('login_view')


@login_required(login_url='login_view')
def profile_view(request):
    """Displays user profile and handles detail updates."""
    if request.method == 'POST':
        user = request.user
        password = request.POST.get('password')
        redirect_url = f"{reverse('profile_view')}#details"
        if not user.check_password(password):
            messages.error(request, 'Incorrect password.')
            return redirect(redirect_url)
        new_email = request.POST.get('email')
        if User.objects.filter(email=new_email).exclude(pk=user.pk).exists():
            messages.error(request, 'An account with this email already exists.')
            return redirect(redirect_url)
        user.full_name = request.POST.get('full_name'); user.phone = request.POST.get('phone'); user.email = new_email
        user.save()
        messages.success(request, 'Your profile has been updated!')
        return redirect('profile_view')
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'profile.html', {'orders': orders})


@login_required(login_url='login_view')
def change_password_view(request):
    """Handles secure password changes for logged-in users."""
    if request.method == 'POST':
        user = request.user
        current_password = request.POST.get('current_password')
        new_password = request.POST.get('new_password')
        redirect_url = f"{reverse('profile_view')}#password"
        if new_password != request.POST.get('confirm_password'):
            messages.error(request, "New passwords do not match.")
            return redirect(redirect_url)
        if not user.check_password(current_password):
            messages.error(request, "Your current password is not correct.")
            return redirect(redirect_url)
        try:
            validate_password(new_password, user=user)
        except ValidationError as e:
            messages.error(request, ". ".join(e.messages))
            return redirect(redirect_url)
        user.set_password(new_password)
        user.save()
        update_session_auth_hash(request, user)
        messages.success(request, "Your password has been changed successfully.")
        return redirect('profile_view')
    return redirect('profile_view')


@login_required(login_url='login_view')
def view_wishlist(request):
    """Displays all items in the user's wishlist."""
    wishlist_items = Wishlist.objects.filter(user=request.user).select_related('product')
    return render(request, 'wishlist.html', {'wishlist_items': wishlist_items})


@login_required(login_url='login_view')
def add_to_wishlist(request, product_id):
    """Adds a product to the user's wishlist, handles AJAX."""
    product = get_object_or_404(Product, id=product_id)
    Wishlist.objects.get_or_create(user=request.user, product=product)
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'status': 'success'})
    messages.success(request, f"'{product.name}' has been added to your wishlist.")
    return redirect(request.META.get('HTTP_REFERER', 'shop'))


@login_required(login_url='login_view')
def remove_from_wishlist(request, product_id):
    """Removes a product from the user's wishlist, handles AJAX."""
    product = get_object_or_404(Product, id=product_id)
    Wishlist.objects.filter(user=request.user, product=product).delete()
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'status': 'success'})
    messages.success(request, f"'{product.name}' has been removed from your wishlist.")
    return redirect('view_wishlist')
