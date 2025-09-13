# ===================================================================
# IMPORTS
# ===================================================================
from django.db import models
from django.conf import settings
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin, Group, Permission
from django.utils.translation import gettext_lazy as _
from django.db.models import Avg
from django.core.validators import MinValueValidator, MaxValueValidator


# ===================================================================
# 1. USER MANAGEMENT
# ===================================================================

class CustomUserManager(BaseUserManager):
    """
    Custom manager for the User model where email is the unique identifier.
    """
    def create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError(_('The Email must be set'))
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        return self.create_user(email, password, **extra_fields)

class User(AbstractBaseUser, PermissionsMixin):
    """
    Custom User model for the application.
    Uses email as the primary identifier instead of a username.
    """
    email = models.EmailField(_('email address'), unique=True)
    full_name = models.CharField(max_length=150)
    phone = models.CharField(max_length=20, blank=True)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    date_joined = models.DateTimeField(auto_now_add=True)

    # Necessary for custom user models with PermissionsMixin
    groups = models.ManyToManyField(Group, verbose_name=_('groups'), blank=True, related_name="shop_user_set")
    user_permissions = models.ManyToManyField(Permission, verbose_name=_('user permissions'), blank=True, related_name="shop_user_permissions_set")
    
    objects = CustomUserManager()
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['full_name']

    def __str__(self):
        return self.email

# ===================================================================
# 2. CORE E-COMMERCE MODELS
# ===================================================================

class Category(models.Model):
    """
    Represents a product category (e.g., Indoor Plants, Succulents).
    """
    name = models.CharField(max_length=100, unique=True)
    image = models.ImageField(upload_to='Category_Images/')
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return self.name

class Product(models.Model):
    """
    Represents a single product for sale in the shop.
    """
    name = models.CharField(max_length=150)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField(default=10)
    is_available = models.BooleanField(default=True)
    is_bestseller = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
    
    # --- Properties for calculated fields ---

    @property
    def average_rating(self):
        """Calculates the average rating from all reviews, returns 0 if none exist."""
        return self.reviews.aggregate(Avg('rating'))['rating__avg'] or 0

    @property
    def review_count(self):
        """Returns the total number of reviews for the product."""
        return self.reviews.count()
    
    @property
    def rating_breakdown(self):
        """Calculates the percentage of 1, 2, 3, 4, and 5-star reviews."""
        breakdown = {f'{i}_star_percent': 0 for i in range(1, 6)}
        total = self.review_count
        if total > 0:
            for i in range(1, 6):
                breakdown[f'{i}_star_percent'] = (self.reviews.filter(rating=i).count() / total) * 100
        return breakdown

class ProductImage(models.Model):
    """
    Represents one of potentially multiple images for a Product.
    """
    product = models.ForeignKey(Product, related_name='images', on_delete=models.CASCADE)
    image = models.ImageField(upload_to='Product_Images/')

    def __str__(self):
        return f"Image for {self.product.name}"

# ===================================================================
# 3. ORDER & CART MODELS
# ===================================================================

class CartItem(models.Model):
    """
    Represents a single product item in a user's shopping cart.
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    @property
    def get_total(self):
        """Calculates the total price for this cart item."""
        return self.product.price * self.quantity
    
    def __str__(self):
        return f"{self.quantity} x {self.product.name}"

class Order(models.Model):
    """
    Represents a single customer order.
    """
    STATUS_CHOICES = (
        ('Pending', 'Pending'), ('Processing', 'Processing'),
        ('Shipped', 'Shipped'), ('Delivered', 'Delivered'), ('Cancelled', 'Cancelled'),
    )
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    full_name = models.CharField(max_length=150)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    address = models.TextField()
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    postcode = models.CharField(max_length=20)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    shipping_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='Pending')
    payment_method = models.CharField(max_length=50, default='Cash on Delivery')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order #{self.id}"
    
    @property
    def subtotal(self):
        """Calculates the subtotal (total price minus shipping)."""
        return self.total_price - self.shipping_cost

class OrderItem(models.Model):
    """
    Represents a single product line item within an Order.
    """
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)

    @property
    def get_total(self):
        """Calculates the total price for this line item."""
        return self.price * self.quantity

# ===================================================================
# 4. USER INTERACTION MODELS
# ===================================================================

class Review(models.Model):
    """
    Represents a single user review for a Product.
    """
    product = models.ForeignKey(Product, related_name="reviews", on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    rating = models.PositiveIntegerField(default=5)
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Review for {self.product.name} by {self.user.full_name}"

class Wishlist(models.Model):
    """
    Represents a single product in a user's wishlist.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # Ensures a user can only add a specific product to their wishlist once.
        unique_together = ('user', 'product')

    def __str__(self):
        return f"{self.product.name} in {self.user.email}'s Wishlist"

# ===================================================================
# 5. SITE UTILITY MODELS
# ===================================================================

class Contact(models.Model):
    """
    Represents a message sent through the contact form.
    """
    name = models.CharField(max_length=100)
    email = models.EmailField()
    subject = models.CharField(max_length=200)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Message from {self.name}"
    
class Coupon(models.Model):
    """
    Represents a discount coupon.
    """
    code = models.CharField(max_length=50, unique=True)
    discount_percent = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(100)])
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.code} ({self.discount_percent}%)"