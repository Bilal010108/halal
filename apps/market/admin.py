from django.contrib import admin
from .models import *

class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    inlines = [ProductImageInline]


admin.site.register(UserProfile)
admin.site.register(Store)
admin.site.register(Category)
admin.site.register(SubCategory)
admin.site.register(Order)
admin.site.register(OrderItem)
admin.site.register(Review)
admin.site.register(CommentLike)
admin.site.register(Favorite)
admin.site.register(FavoriteProduct)
admin.site.register(Cart)
admin.site.register(CartItem)
admin.site.register(Sale)
admin.site.register(SellerRequest)



