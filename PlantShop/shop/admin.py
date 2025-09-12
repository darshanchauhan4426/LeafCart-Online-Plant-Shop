# In shop/admin.py

from django.contrib import admin
from .models import User, Category, Product, ProductImage, CartItem, Order, OrderItem, Review, Contact, Wishlist, Coupon

# This allows us to add images directly on the Product admin page
class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1  # How many extra empty forms to show

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'price', 'is_available', 'is_bestseller']
    list_filter = ['is_available', 'category']
    inlines = [ProductImageInline]

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_active']

# (The rest of your admin registrations can remain)
admin.site.register(User)
admin.site.register(CartItem)
admin.site.register(Review)
admin.site.register(Contact)
admin.site.register(Wishlist)
admin.site.register(Coupon)

# Register Order and OrderItem if you haven't already
class OrderItemInline(admin.TabularInline):
    model = OrderItem
    raw_id_fields = ['product']

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'status', 'created_at', 'total_price']
    list_filter = ['status', 'created_at']
    inlines = [OrderItemInline]