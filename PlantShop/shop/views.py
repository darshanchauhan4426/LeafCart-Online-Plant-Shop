from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.paginator import Paginator
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from .models import User, Product, Category, Contact, Review, CartItem, Order, OrderItem
from django.http import JsonResponse
from django.http import HttpResponse
from django.template.loader import render_to_string
from weasyprint import HTML
from django.contrib.auth import update_session_auth_hash
from django.core.exceptions import ValidationError
from django.contrib.auth.password_validation import validate_password

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
    return render(request, 'about.html')

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
    # ... (Logic to fetch and filter products with pagination) ...
    categories = Category.objects.filter(is_active=True)
    selected_category_ids = request.GET.getlist("categories")
    products_list = Product.objects.filter(is_available=True).order_by('-created_at')
    if selected_category_ids:
        products_list = products_list.filter(category_id__in=selected_category_ids)
    paginator = Paginator(products_list, 6)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    context = { "categories": categories, "page_obj": page_obj, "selected_categories": [int(c) for c in selected_category_ids if c.isdigit()]}
    return render(request, "shop.html", context)


def shop_details(request, product_id):
    # ... (Logic to show a single product and its reviews) ...
    product = get_object_or_404(Product, id=product_id)
    product_images = product.images.all()
    related_products = Product.objects.filter(category=product.category).exclude(id=product.id)[:4]
    if request.method == "POST" and request.user.is_authenticated:
        Review.objects.create(product=product, user=request.user, rating=request.POST.get("rating", 5), comment=request.POST.get("comment"))
        messages.success(request, "Your review has been submitted.")
        return redirect("shop_details", product_id=product.id)
    context = {
        "product": product,
        "product_images": product_images,
        "related_products": related_products,
    }    
    return render(request, "shop_details.html", context)

@login_required(login_url='login_view')
def cart_view(request):
    # ... (Logic to show cart items and total) ...
    cart_items = CartItem.objects.filter(user=request.user)
    cart_total = sum(item.get_total for item in cart_items)
    context = {'cart_items': cart_items, 'cart_total': cart_total}
    return render(request, 'cart.html', context)

@login_required(login_url='login_view')
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
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
    cart_items = CartItem.objects.filter(user=request.user)
    cart_total = sum(item.get_total for item in cart_items)

    if not cart_items:
        messages.warning(request, "Your cart is empty.")
        return redirect('shop')

    # --- FIX: Define shipping and calculate total price correctly ---
    shipping_cost = 0  # Set shipping to be free
    total_price = cart_total + shipping_cost
    # --- END FIX ---

    if request.method == 'POST':
        new_order = Order.objects.create(
            user=request.user,
            full_name=request.POST.get('full_name'),
            email=request.POST.get('email'),
            phone=request.POST.get('phone'),
            address=request.POST.get('address'),
            city=request.POST.get('city'),
            state=request.POST.get('state'),
            postcode=request.POST.get('postcode'),
            total_price=total_price,         # Use the corrected total
            shipping_cost=shipping_cost      # Save the shipping cost
        )
        for item in cart_items:
            OrderItem.objects.create(
                order=new_order,
                product=item.product,
                quantity=item.quantity,
                price=item.product.price
            )
        
        cart_items.delete()
        
        messages.success(request, "Your order has been placed successfully!")
        return redirect('order_confirmation', order_id=new_order.id)

    context = {'cart_items': cart_items, 'cart_total': cart_total}
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
def profile_view(request):
    if request.method == 'POST':
        user = request.user
        password = request.POST.get('password')

        if not user.check_password(password):
            messages.error(request, 'Incorrect password. Please try again.')
            # FIX: Redirect back to the #details tab on error
            return redirect('/profile/#details')

        new_email = request.POST.get('email')
        if User.objects.filter(email=new_email).exclude(pk=user.pk).exists():
            messages.error(request, 'An account with this email already exists.')
            # FIX: Redirect back to the #details tab on error
            return redirect('/profile/#details')

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
def change_password_view(request):
    if request.method == 'POST':
        # ... (get passwords) ...
        current_password = request.POST.get('current_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')

        if new_password != confirm_password:
            messages.error(request, "New passwords do not match.")
            # FIX: Redirect back to the #password tab on error
            return redirect('/profile_view/#password')

        user = request.user
        if not user.check_password(current_password):
            messages.error(request, "Your current password is not correct.")
            # FIX: Redirect back to the #password tab on error
            return redirect('/profile_view/#password')
        
        try:
            validate_password(new_password, user=user)
        except ValidationError as e:
            messages.error(request, ". ".join(e.messages))
            # FIX: Redirect back to the #password tab on error
            return redirect('/profile_view/#password')
        
        user.set_password(new_password)
        user.save()
        
        update_session_auth_hash(request, user)
        
        messages.success(request, "Your password has been changed successfully.")
        return redirect('profile_view')
    
    return redirect('profile_view')
