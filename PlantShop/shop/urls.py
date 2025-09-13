from django.urls import path
from . import views

# app_name = 'shop' # Optional: Add an app namespace for larger projects

urlpatterns = [
    # ===================================================================
    # Core & Static Page URLs
    # ===================================================================
    path('', views.index, name='index'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),

    # ===================================================================
    # Shop & Product URLs
    # ===================================================================
    path('shop/', views.shop, name='shop'),
    path('shop/product/<int:product_id>/', views.shop_details, name='shop_details'),

    # ===================================================================
    # Cart & Coupon URLs
    # ===================================================================
    path('cart/', views.cart_view, name='cart_view'),
    path('cart/add/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/remove/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('cart/update/', views.update_cart, name='update_cart'),
    path('cart/apply-coupon/', views.apply_coupon, name='apply_coupon'),
    
    # ===================================================================
    # Checkout & Order URLs
    # ===================================================================
    path('checkout/', views.checkout, name='checkout'),
    path('order/confirmation/<int:order_id>/', views.order_confirmation_view, name='order_confirmation'),
    path('order/invoice/<int:order_id>/', views.generate_invoice_pdf, name='generate_invoice_pdf'),

    # ===================================================================
    # Authentication & Profile URLs
    # ===================================================================
    path('login/', views.login_view, name='login_view'),
    path('register/', views.register_view, name='register_view'),
    path('logout/', views.logout_view, name='logout_view'),
    path('profile/', views.profile_view, name='profile_view'),
    path('profile/change-password/', views.change_password_view, name='change_password_view'), 
    
    # ===================================================================
    # Wishlist URLs
    # ===================================================================
    path('wishlist/', views.view_wishlist, name='view_wishlist'),
    path('wishlist/add/<int:product_id>/', views.add_to_wishlist, name='add_to_wishlist'),
    path('wishlist/remove/<int:product_id>/', views.remove_from_wishlist, name='remove_from_wishlist'),
]