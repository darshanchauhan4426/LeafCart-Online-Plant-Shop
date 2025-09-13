# ===================================================================
# IMPORTS
# ===================================================================
from django.contrib import admin
from .models import (
    User, Category, Product, ProductImage, CartItem, Order, OrderItem, 
    Review, Contact, Wishlist, Coupon
)

# ===================================================================
# ADMIN CONFIGURATIONS
# ===================================================================

# This "Inline" class allows us to add multiple images directly on the Product admin page
class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1  # How many extra empty image forms to show

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    """
    Customizes the admin interface for the Product model.
    """
    list_display = ['name', 'category', 'price', 'stock', 'is_available', 'is_bestseller']
    list_filter = ['is_available', 'is_bestseller', 'category']
    search_fields = ['name', 'description']
    inlines = [ProductImageInline]

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """
    Customizes the admin interface for the Category model.
    """
    list_display = ['name', 'is_active']
    list_filter = ['is_active']

# This "Inline" class allows us to see the items purchased within each Order
class OrderItemInline(admin.TabularInline):
    model = OrderItem
    raw_id_fields = ['product']
    readonly_fields = ['product', 'quantity', 'price']
    can_delete = False
    extra = 0

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    """
    Customizes the admin interface for the Order model.
    """
    list_display = ['id', 'user', 'full_name', 'status', 'created_at', 'total_price']
    list_filter = ['status', 'created_at']
    search_fields = ['id', 'full_name', 'email']
    inlines = [OrderItemInline]

# ===================================================================
# STANDARD MODEL REGISTRATIONS
# ===================================================================

# For models that don't need special customization, we can register them directly.
admin.site.register(User)
admin.site.register(CartItem)
admin.site.register(Review)
admin.site.register(Contact)
admin.site.register(Wishlist)
admin.site.register(Coupon)