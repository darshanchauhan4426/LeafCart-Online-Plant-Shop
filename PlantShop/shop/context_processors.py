# shop/context_processors.py

from .models import CartItem

def cart_item_count(request):
    """
    Makes the total quantity of items in the cart available to all templates.
    """
    if not request.user.is_authenticated:
        return {'cart_item_count': 0}
    
    # Get all cart items for the logged-in user
    cart_items = CartItem.objects.filter(user=request.user)
    
    # Calculate the sum of the 'quantity' field for all items
    total_items = sum(item.quantity for item in cart_items)
    
    return {'cart_item_count': total_items}