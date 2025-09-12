from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.paginator import Paginator
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from .models import User, Product, Category, Contact, Review, CartItem, Order, OrderItem, ProductImage, Wishlist, Coupon
from django.http import JsonResponse
from django.http import HttpResponse
from django.template.loader import render_to_string
from weasyprint import HTML
from django.contrib.auth import update_session_auth_hash
from django.core.exceptions import ValidationError
from django.contrib.auth.password_validation import validate_password
from django.urls import reverse
from django.db.models import Q

def index(request):
    """
    Renders the homepage and fetches the 4 newest products for the
    'New Arrivals' section.
    """
    # Fetch the 4 most recently created, available products
    new_arrivals = Product.objects.filter(is_available=True).order_by('-created_at')[:4]
    
    context = {
        'new_arrivals': new_arrivals
    }
    return render(request, 'index.html', context)

def about(request):
    """
    Renders the about page and fetches a random selection of product images
    for the gallery.
    """
    # Fetch 8 random images from your entire product collection
    all_images = ProductImage.objects.order_by('?')[:8]
    
    context = {
        'plant_images': all_images
    }
    return render(request, 'about.html', context)

def contact(request):
    """
    Handles displaying the contact form and processing form submissions.
    """
    if request.method == "POST":
        # Get the form data from the POST request
        name = request.POST.get('name')
        email = request.POST.get('email')
        subject = request.POST.get('subject')
        message_text = request.POST.get('message')

        # Simple validation to ensure all fields are filled
        if not all([name, email, subject, message_text]):
            messages.error(request, "All fields are required. Please fill out the form completely.")
        else:
            # If valid, create a new Contact object and save it
            Contact.objects.create(
                name=name, 
                email=email, 
                subject=subject, 
                message=message_text
            )
            messages.success(request, "Thank you for your message! We will get back to you shortly.")
            # Redirect to the same page to prevent re-submission on refresh
            return redirect('contact')

    # If the request is GET, just render the empty form
    return render(request, 'contact.html')


def shop(request):
    # ... (the top part of the view is the same) ...
    categories = Category.objects.filter(is_active=True)
    selected_category_ids = request.GET.getlist("categories")
    search_query = request.GET.get('search', None)
    sort_option = request.GET.get('sort', 'default')

    products_list = Product.objects.all()

    # ... (filtering logic is the same) ...
    if search_query:
        products_list = products_list.filter(Q(name__icontains=search_query) | Q(description__icontains=search_query))
    if selected_category_ids:
        products_list = products_list.filter(category_id__in=selected_category_ids)

    # --- SORTING LOGIC ---
    if sort_option == 'price_asc':
        products_list = products_list.order_by('price')
    elif sort_option == 'price_desc':
        products_list = products_list.order_by('-price')
    elif sort_option == 'name_asc':
        products_list = products_list.order_by('name')
    else: 
        # FIX: Sort by stock (descending) so items with stock > 0 appear first.
        products_list = products_list.order_by('-stock', '-created_at')

    # ... (the rest of the view is the same) ...
    paginator = Paginator(products_list, 6)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "categories": categories,
        "page_obj": page_obj,
        "selected_categories": [int(c) for c in selected_category_ids if c.isdigit()],
        "search_query": search_query,
        "sort_option": sort_option,
        "wishlist_product_ids": Wishlist.objects.filter(user=request.user).values_list('product_id', flat=True) if request.user.is_authenticated else [],
    }
    return render(request, "shop.html", context)


def shop_details(request, product_id):
    # ... (Logic to show a single product and its reviews) ...
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
    context = {
        "product": product,
        "product_images": product_images,
        "related_products": related_products,
        "is_in_wishlist": is_in_wishlist, 
    }    
    return render(request, "shop_details.html", context)


def cart_view(request):
    cart_items = CartItem.objects.filter(user=request.user)
    cart_subtotal = sum(item.get_total for item in cart_items)
    
    discount_amount = 0
    final_total = cart_subtotal
    coupon_code = None
    
    # Check if a coupon is stored in the session
    coupon_id = request.session.get('coupon_id')
    if coupon_id:
        try:
            coupon = Coupon.objects.get(id=coupon_id, is_active=True)
            discount_amount = (cart_subtotal * coupon.discount_percent) / 100
            final_total = cart_subtotal - discount_amount
            coupon_code = coupon.code
        except Coupon.DoesNotExist:
            # If coupon is invalid, remove it from session
            del request.session['coupon_id']

    context = {
        'cart_items': cart_items,
        'cart_subtotal': cart_subtotal,
        'discount_amount': discount_amount,
        'final_total': final_total,
        'coupon_code': coupon_code,
    }
    return render(request, 'cart.html', context)


@login_required(login_url='login_view')
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    if product.stock <= 0:
        messages.error(request, f"Sorry, '{product.name}' is out of stock.")
        return redirect('shop')
    
    quantity_from_form = int(request.POST.get('quantity', 1))

    cart_item, created = CartItem.objects.get_or_create(
        user=request.user, 
        product=product
    )

    if created:
        cart_item.quantity = quantity_from_form
        messages.success(request, f"'{product.name}' was added to your cart.")
    else:
        cart_item.quantity += quantity_from_form
        messages.success(request, f"Quantity of '{product.name}' was updated.")
    
    cart_item.save()

    # ADD THIS CHECK for interactive (AJAX) requests from the shop page
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        # Recalculate the total number of items in the cart
        total_items = sum(item.quantity for item in CartItem.objects.filter(user=request.user))
        # Send the new count back to the JavaScript
        return JsonResponse({'message': 'Success', 'cart_item_count': total_items})

    # For standard form posts (like from the details page), redirect as normal
    return redirect('cart_view')


@login_required(login_url='login_view')
def remove_from_cart(request, item_id):
    get_object_or_404(CartItem, id=item_id, user=request.user).delete()
    messages.success(request, "Item removed from cart.")
    return redirect('cart_view')

@login_required(login_url='login_view')
def update_cart(request):
    if request.method == 'POST':
        for key, value in request.POST.items():
            if key.startswith('quantity_'):
                item_id = int(key.split('_')[1])
                quantity = int(value)
                item = get_object_or_404(CartItem, id=item_id, user=request.user)
                if quantity > 0:
                    item.quantity = quantity
                    item.save()
                else:
                    item.delete()
        messages.success(request, "Cart updated.")
    return redirect('cart_view')


@login_required(login_url='login_view')
def checkout(request):
    """
    Handles the entire checkout process:
    - Displays the checkout form with final totals.
    - Validates stock before creating an order.
    - Processes the order, saves it to the database, and updates stock.
    - Clears the cart and coupon upon successful order.
    """
    cart_items = CartItem.objects.filter(user=request.user)
    cart_subtotal = sum(item.get_total for item in cart_items)

    # Prevent access if the cart is empty
    if not cart_items:
        messages.warning(request, "Your cart is empty. Please add products before checking out.")
        return redirect('shop')

    # --- Coupon Calculation Logic ---
    discount_amount = 0
    final_total = cart_subtotal
    coupon_code = None
    
    coupon_id = request.session.get('coupon_id')
    if coupon_id:
        try:
            coupon = Coupon.objects.get(id=coupon_id, is_active=True)
            discount_amount = (cart_subtotal * coupon.discount_percent) / 100
            final_total = cart_subtotal - discount_amount
            coupon_code = coupon.code
        except Coupon.DoesNotExist:
            # If coupon has become invalid, remove it from the session
            del request.session['coupon_id']
    # --- End Coupon Logic ---

    # --- Order Processing (on form submission) ---
    if request.method == 'POST':
        # 1. Validate stock one last time before creating the order
        for item in cart_items:
            if item.product.stock < item.quantity:
                messages.error(request, f"Sorry, the quantity for '{item.product.name}' is no longer available. Only {item.product.stock} left.")
                return redirect('cart_view')

        # 2. Create the Order object with all billing details
        new_order = Order.objects.create(
            user=request.user,
            full_name=request.POST.get('full_name'),
            email=request.POST.get('email'),
            phone=request.POST.get('phone'),
            address=request.POST.get('address'),
            city=request.POST.get('city'),
            state=request.POST.get('state'),
            postcode=request.POST.get('postcode'),
            total_price=final_total,
            payment_method='Cash on Delivery'
        )
        
        # 3. Create Order Items and decrease product stock
        for item in cart_items:
            OrderItem.objects.create(
                order=new_order,
                product=item.product,
                quantity=item.quantity,
                price=item.product.price
            )
            # Decrease the stock for the purchased product
            item.product.stock -= item.quantity
            item.product.save()

        # 4. Clear the cart and the coupon from the session
        cart_items.delete()
        if 'coupon_id' in request.session:
            del request.session['coupon_id']
        
        # 5. Redirect to the confirmation page
        messages.success(request, "Your order has been placed successfully!")
        return redirect('order_confirmation', order_id=new_order.id)

    # --- Displaying the Page (if not a POST request) ---
    context = {
        'cart_items': cart_items,
        'cart_subtotal': cart_subtotal,
        'discount_amount': discount_amount,
        'final_total': final_total,
        'coupon_code': coupon_code,
    }
    return render(request, 'checkout.html', context)


@login_required(login_url='login_view')
def order_confirmation_view(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, 'order_confirmation.html', {'order': order})

def login_view(request):
    # ... (Full login logic) ...
    if request.method == 'POST':
        email = request.POST.get('email').strip()
        password = request.POST.get('password')
        user = authenticate(request, username=email, password=password)
        if user:
            auth_login(request, user)
            return redirect('index')
        else:
            messages.error(request, "Invalid credentials.")
    return render(request, 'login.html')

def register_view(request):
    if request.user.is_authenticated:
        return redirect('index')

    if request.method == 'POST':
        full_name = request.POST.get('full_name')
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        phone = request.POST.get('phone')

        if password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return redirect('register_view')
        
        if User.objects.filter(email=email).exists():
            messages.error(request, "An account with this email already exists.")
            return redirect('register_view')

        # --- ADD THIS VALIDATION BLOCK ---
        try:
            validate_password(password)
        except ValidationError as e:
            # Join all validation error messages into a single message
            messages.error(request, ". ".join(e.messages))
            return redirect('register_view')
        # --- END OF VALIDATION BLOCK ---

        user = User.objects.create_user(
            email=email, password=password, full_name=full_name, phone=phone
        )
        auth_login(request, user)
        messages.success(request, f"Welcome, {user.full_name}! Your account has been created.")
        return redirect('index')

    return render(request, 'register.html')

def logout_view(request):
    auth_logout(request)
    messages.success(request, "Logged out successfully.")
    return redirect('login_view')

@login_required(login_url='login_view')
def generate_invoice_pdf(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    
    # The context and template remain the same as before
    template_path = 'invoice.html'
    context = {'order': order}

    # Render the HTML template
    html_string = render_to_string(template_path, context)
    
    # Generate the PDF file using WeasyPrint
    # base_url is important for WeasyPrint to find static files like fonts
    pdf_file = HTML(string=html_string, base_url=request.build_absolute_uri()).write_pdf()

    # Create the HTTP response to send the PDF back to the browser
    response = HttpResponse(pdf_file, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="invoice_#{order.id}.pdf"'
    
    return response

@login_required(login_url='login_view')
def profile_view(request):
    if request.method == 'POST':
        user = request.user
        password = request.POST.get('password')

        # This is where we build the correct redirect URL with the hash
        redirect_url = f"{reverse('profile_view')}#details"

        if not user.check_password(password):
            messages.error(request, 'Incorrect password. Please try again.')
            # FIX: Redirect to the correct URL
            return redirect(redirect_url)

        new_email = request.POST.get('email')
        if User.objects.filter(email=new_email).exclude(pk=user.pk).exists():
            messages.error(request, 'An account with this email already exists.')
            # FIX: Redirect to the correct URL
            return redirect(redirect_url)

        user.full_name = request.POST.get('full_name')
        user.phone = request.POST.get('phone')
        user.email = new_email
        user.save()
        
        messages.success(request, 'Your profile has been updated successfully!')
        return redirect('profile_view')

    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    context = {'orders': orders}
    return render(request, 'profile.html', context)


@login_required(login_url='login_view')
def change_password_view(request):
    if request.method == 'POST':
        current_password = request.POST.get('current_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')
        
        # This is where we build the correct redirect URL with the hash
        redirect_url = f"{reverse('profile_view')}#password"

        if new_password != confirm_password:
            messages.error(request, "New passwords do not match.")
            # FIX: Redirect to the correct URL
            return redirect(redirect_url)

        user = request.user
        if not user.check_password(current_password):
            messages.error(request, "Your current password is not correct.")
            # FIX: Redirect to the correct URL
            return redirect(redirect_url)
        
        try:
            validate_password(new_password, user=user)
        except ValidationError as e:
            messages.error(request, ". ".join(e.messages))
            # FIX: Redirect to the correct URL
            return redirect(redirect_url)
        
        user.set_password(new_password)
        user.save()
        
        update_session_auth_hash(request, user)
        
        messages.success(request, "Your password has been changed successfully.")
        return redirect('profile_view')
    
    return redirect('profile_view')


@login_required(login_url='login_view')
def view_wishlist(request):
    """
    Displays all items in the user's wishlist.
    """
    wishlist_items = Wishlist.objects.filter(user=request.user)
    context = {'wishlist_items': wishlist_items}
    return render(request, 'wishlist.html', context)


@login_required(login_url='login_view')
def add_to_wishlist(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    Wishlist.objects.get_or_create(user=request.user, product=product)
    
    # If the request is from our script, send back a success message
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'status': 'success', 'message': 'Item added to wishlist.'})

    messages.success(request, f"'{product.name}' has been added to your wishlist.")
    return redirect(request.META.get('HTTP_REFERER', 'shop'))

@login_required(login_url='login_view')
def remove_from_wishlist(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    Wishlist.objects.filter(user=request.user, product=product).delete()

    # If the request is from our script, send back a success message
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'status': 'success', 'message': 'Item removed from wishlist.'})
    
    messages.success(request, f"'{product.name}' has been removed from your wishlist.")
    return redirect(request.META.get('HTTP_REFERER', 'view_wishlist'))

# In shop/views.py

def apply_coupon(request):
    if request.method == 'POST':
        code = request.POST.get('code')
        try:
            coupon = Coupon.objects.get(code__iexact=code, is_active=True)
            # Store the valid coupon's ID in the user's session
            request.session['coupon_id'] = coupon.id
            messages.success(request, 'Coupon applied successfully!')
        except Coupon.DoesNotExist:
            request.session['coupon_id'] = None
            messages.error(request, 'This coupon is invalid or has expired.')
    return redirect('cart_view')

