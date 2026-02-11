from django.db import models
from django.contrib.auth.models import AbstractUser
from  phonenumber_field.modelfields import PhoneNumberField
from django.core.exceptions import ValidationError
from django.db.models import Avg
from decimal import Decimal
from django.core.validators import MinValueValidator, MaxValueValidator


class UserProfile(AbstractUser):
    email = models.EmailField(unique=True)
    phone_number = PhoneNumberField(null=True,blank=True, unique=True)
    ROLES_CHOICES = (
        ('admin', 'admin'),
        ('seller', 'seller'),
        ('client', 'client'),
    )
    user_role = models.CharField(max_length=16, choices=ROLES_CHOICES, default='client')
    profile_icon =models.ImageField(upload_to='profile_iconka/',null=True,blank=True)

    def __str__(self):
        return f'{self.username},{self.user_role}'


class Store(models.Model):
    store_owner = models.OneToOneField(UserProfile,on_delete=models.CASCADE)
    store_name = models.CharField(max_length=100)
    store_image = models.ImageField(upload_to='store_image',null=True,blank=True)
    store_description = models.TextField(max_length=500,null=True,blank=True)

    def __str__(self):
        return self.store_name

    def clean(self):
        if Store.objects.filter(
            store_owner=self.store_owner
        ).exclude(pk=self.pk).exists():
            raise ValidationError("Этот пользователь уже имеет магазин")


class Category(models.Model):
    category_name = models.CharField(max_length=100,unique=True)
    category_image = models.ImageField(upload_to='category_image',)

    def __str__(self):
        return self.category_name

class SubCategory(models.Model):
    category = models.ForeignKey(Category,on_delete=models.CASCADE,related_name='subcategories')
    subcategory_name = models.CharField(max_length=100,unique=True)
    subcategory_image = models.ImageField(upload_to='subcategory_image/')

    def __str__(self):
        return self.subcategory_name




class Product(models.Model):
    store = models.ForeignKey(Store,on_delete=models.CASCADE)
    product_subcategory = models.ForeignKey(SubCategory,on_delete=models.CASCADE)
    product_name = models.CharField(max_length=500,null=True,blank=True)
    country = models.CharField(max_length=100,null=True,blank=True)
    ingredients = models.TextField(null=True,blank=True)
    price =  models.DecimalField(max_digits=8,decimal_places=2,default=0)
    best_before_date = models.CharField(max_length=100,null=True,blank=True) #Срок годности
    action = models.CharField(max_length=100,null=True,blank=True)
    quantity =  models.CharField(max_length=100,null=True,blank=True)
    description = models.TextField(null=True,blank=True)


    def __str__(self):
        return self.product_name

    @property
    def avg_rating(self):
        avg = self.review_product.aggregate(avg=Avg('rating'))['avg']
        return round(avg, 1) if avg else 0

    def get_count_rating(self):
        count = self.review_product.count()

        if count > 3:
            return '3+'
        return count

    @property
    def good_rate(self):
        total = self.review_product.count()
        if total == 0:
            return '0%'
        good = self.review_product.filter(rating__gt=3).count()
        percent = round((good * 100) / total)
        return f'{percent}%'


class Sale(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='sales')
    is_active = models.BooleanField(default=False)
    description1 = models.TextField()
    description2 = models.TextField()
    discount_percent = models.PositiveSmallIntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )

    start_date = models.DateTimeField()
    end_date = models.DateTimeField()

    @property
    def discounted_price(self):
        if self.discount_percent and self.product.price:
            return self.product.price * (Decimal(100) - self.discount_percent) / Decimal(100)

        return self.product.price

    @property
    def is_currently_active(self):
        from django.utils import timezone
        now = timezone.now()
        return self.is_active and self.start_date <= now <= self.end_date



    def __str__(self):
        return f"{self.product.product_name} - {self.discount_percent}%"


class ProductImage(models.Model):
    product = models.ForeignKey(Product,on_delete=models.CASCADE,related_name='images')
    product_image = models.ImageField(upload_to='product_image',null=True,blank=True)

    def __str__(self):
        return self.product_image.name or self.product.product_name


class Order(models.Model):
    customer = models.ForeignKey(UserProfile, on_delete=models.CASCADE,related_name='customer_orders')
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=50, choices=[
        ('pending', 'В ожидании'),
        ('shipped', 'Отправлен'),
        ('delivered', 'Доставлен'),
        ('cancelled', 'Отменён')
    ], default='pending')


    def __str__(self):
        return self.customer.username

class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name="items", on_delete=models.SET_NULL, null=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, null=True,related_name='product_items')
    address = models.CharField(max_length=500)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    phone_number = models.CharField(max_length=100,null=True,blank=True)

    def __str__(self):
        return self.product.product_name

class Review(models.Model):
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE,related_name='user_reviews')
    product = models.ForeignKey(Product,on_delete=models.CASCADE,related_name='review_product',)
    rating = models.PositiveIntegerField(
        choices=[(i, str(i)) for i in range(1, 6)])
    comment = models.TextField(null=True,blank=True)
    photo1 = models.ImageField(upload_to='photo1',null=True,blank=True)
    photo2 = models.ImageField(upload_to='photo2',null=True,blank=True)
    photo3 = models.ImageField(upload_to='photo3',null=True,blank=True)
    photo4 = models.ImageField(upload_to='photo4',null=True,blank=True)
    parent = models.ForeignKey('self',on_delete=models.CASCADE,null=True,blank=True,related_name='replies')
    created_at = models.DateTimeField(auto_now_add=True)

    def is_reply(self):
        return self.parent is not None
    @property
    def likes_count(self):
        return self.likes.count()  # считает все лайки для этого отзыва

    def __str__(self):
        if self.is_reply():
            return f"Reply by {self.user.username} to Review {self.parent.id}"
        return f"Review by {self.user.username} on {self.product.product_name}"





class CommentLike(models.Model):
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    review  = models.ForeignKey(Review, on_delete=models.CASCADE,related_name='likes')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('review', 'user')

    def __str__(self):
        return f'{self.user} {self.review}'



class Favorite(models.Model):
    user = models.OneToOneField(UserProfile, on_delete=models.CASCADE, related_name='favorite'
)

    def __str__(self):
        return f'{self.user}'

class FavoriteProduct(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    favorite = models.ForeignKey(Favorite, on_delete=models.CASCADE)
    created_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('favorite', 'product')

    def __str__(self):
        return f'{self.product} {self.favorite}'




class Cart(models.Model):
    user = models.OneToOneField(UserProfile, on_delete=models.CASCADE, related_name='cart')
    created_at = models.DateTimeField(auto_now_add=True)


    def __str__(self):
        return f"Cart of {self.user.username}"

    @property
    def total_price(self):
        return sum(item.total_price for item in self.items.all())

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    @property
    def total_price(self):
        return self.product.price * self.quantity

    def __str__(self):
        return f"{self.quantity} x {self.product.product_name}"


class SellerRequest(models.Model):
    STATUS_CHOICES = (
        ('pending', 'В ожидании'),
        ('approved', 'Одобрено'),
        ('rejected', 'Отклонено'),
    )

    user = models.OneToOneField(UserProfile,on_delete=models.CASCADE,related_name='seller_request',)
    phone_number = PhoneNumberField()
    status = models.CharField(max_length=20,choices=STATUS_CHOICES,default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.user.username} - {self.status}'
