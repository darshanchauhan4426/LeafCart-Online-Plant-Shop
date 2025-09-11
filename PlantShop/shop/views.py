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

# In shop/views.py

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

# --- Shop & Product Views ---
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
    related_products = Product.objects.filter(category=product.category).exclude(id=product.id)[:4]
    if request.method == "POST" and request.user.is_authenticated:
        Review.objects.create(product=product, user=request.user, rating=request.POST.get("rating", 5), comment=request.POST.get("comment"))
        messages.success(request, "Your review has been submitted.")
        return redirect("shop_details", product_id=product.id)
    context = {"product": product, "related_products": related_products}
    return render(request, "shop_details.html", context)


# --- Cart Views ---
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
    
    # 1. Get the quantity from the form. Defaults to 1 if not provided.
    #    This works for both the shop page (sends 1) and details page (sends user's choice).
    quantity_from_form = int(request.POST.get('quantity', 1))

    # 2. Get the item, or create it if it doesn't exist.
    cart_item, created = CartItem.objects.get_or_create(
        user=request.user, 
        product=product
    )

    if created:
        # 3. If a NEW item was created, set its quantity to what the form sent.
        cart_item.quantity = quantity_from_form
        messages.success(request, f"'{product.name}' was added to your cart.")
    else:
        # 4. If the item ALREADY EXISTED, add the new quantity to the existing quantity.
        cart_item.quantity += quantity_from_form
        messages.success(request, f"Quantity of '{product.name}' was updated.")
    
    cart_item.save()

    # This part handles the AJAX response for the interactive shop page
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        total_items = sum(item.quantity for item in CartItem.objects.filter(user=request.user))
        return JsonResponse({'message': 'Success', 'cart_item_count': total_items})

    # This handles the standard redirect for the details page
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


# In shop/views.py

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

# --- Authentication & Profile Views ---
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
    # ... (Full registration logic) ...
    if request.method == 'POST':
        # ... validation ...
        if request.POST.get('password') != request.POST.get('confirm_password'):
            messages.error(request, "Passwords do not match.")
            return redirect('register_view')
        try:
            user = User.objects.create_user(email=request.POST.get('email'), password=request.POST.get('password'), full_name=request.POST.get('full_name'), phone=request.POST.get('phone'))
            auth_login(request, user)
            return redirect('index')
        except Exception as e:
            messages.error(request, f"Registration failed: {e}")
    return render(request, 'register.html')

def logout_view(request):
    auth_logout(request)
    messages.success(request, "Logged out successfully.")
    return redirect('login_view')

@login_required(login_url='login_view')
def profile_view(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'profile.html', {'orders': orders})

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
