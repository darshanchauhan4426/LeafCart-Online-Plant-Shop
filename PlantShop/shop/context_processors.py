from .models import CartItem, Product

def cart_item_count(request):
    """
    Makes the cart item count and bestseller products available to all templates.
    """
    context = {}
    
    # Calculate cart item count for authenticated users
    if request.user.is_authenticated:
        cart_items = CartItem.objects.filter(user=request.user)
        total_items = sum(item.quantity for item in cart_items)
        context['cart_item_count'] = total_items
    else:
        context['cart_item_count'] = 0

    # Fetch the top 2 bestseller products
    bestseller_products = Product.objects.filter(is_bestseller=True, is_available=True)[:2]
    context['bestseller_products'] = bestseller_products
    
    return context