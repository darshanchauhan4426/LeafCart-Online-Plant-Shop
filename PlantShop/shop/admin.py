# shop/admin.py

from django.contrib import admin
from .models import User, Category, Product, CartItem, Order, OrderItem, Review, Contact

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    raw_id_fields = ['product']

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'full_name', 'status', 'created_at', 'total_price']
    list_filter = ['status', 'created_at']
    inlines = [OrderItemInline]

admin.site.register(User)
admin.site.register(Category)
admin.site.register(Product)
admin.site.register(CartItem)
admin.site.register(Review)
admin.site.register(Contact)