from rest_framework import routers
from unicodedata import category

from .views import *
from django.urls import path, include

router = routers.SimpleRouter()


urlpatterns = [
    path('', include(router.urls)),
    path('clients/', ClientAPIView.as_view(), name='clients-list'),
    path('sellers/', SellerAPIView.as_view(), name='sellers-list'),
    path('admins/', AdminAPIView.as_view(), name='admins-list'),


    # Store
    path('stores/', StoreAPIView.as_view(), name='store-list'),
    path('stores/<int:pk>/', StoreDetailAPIView.as_view(), name='store-detail'),
    path('stores_create/',StoreCreateAPIView.as_view(), name='store-create'),


    #  Categories
    path('categories/', CategoryListAPIView.as_view(), name='category-list'),
    path('categories/<int:pk>/',CategoryDetailAPIView.as_view(), name='category-detail'),
    path('subcategories/', SubCategoryListApiView.as_view(), name='subcategory-list'),
    path('subcategories/<int:pk>/',SubCategoryDetailApiView.as_view(), name='subcategory-detail'),

    # Products
    path('products/', ProductListAPIView.as_view(), name='product-list'),
    path('products_create/', ProductCreateAPIView.as_view(), name='product-create'),
    path('products/<int:pk>/', ProductDetailAPIView.as_view(), name='product-detail'),

    path('productsimage/', ProductImageAPIView.as_view(), name='products_image-list'),
    path('productsimage_create/', ProductImageCreateAPIView.as_view(), name='products_image-create'),
    path('productsimage/<int:pk>/', ProductImageDetailAPIView.as_view(), name='products_image-detail'),

    # sale
    path('sales/', SaleListAPIView.as_view(), name='sale-list'),
    path('sales/<int:pk>/', SaleDetailAPIView.as_view(), name='sale-detail'),

    # Orders
    path('orders/', OrderAPIView.as_view(), name='order-list'),
    path('order-items/', OrderItemAPIView.as_view(), name='order-item-list'),

    # Reviews & Comments
    path('reviews/', ReviewListAPIView.as_view(), name='review-list'),
    path('reviews/<int:pk>/', ReviewDetailAPIView.as_view(), name='review-detail'),
    path('comments/', CommentListAPIView.as_view(), name='comment-list'),
    # cart карзина
    path('cart/', CartAPIView.as_view(),name = 'bilal_cart'),
    path('cart_create/', CartItemCreateAPIView.as_view(),name = 'cart_item_create'),
    path('cart/<int:pk>/', CartItemDetailAPIView.as_view(),name = 'cart_item_detail'),

    # favorite

    path('favorite/', FavoriteAPIView.as_view()),
    path('favorite_create/', FavoriteProductCreateAPIView.as_view()),
    path('favorite/<int:pk>/', FavoriteProductDeleteAPIView.as_view()),

    path('seller_requests/', SellerRequestCreateView.as_view()),

    # админ
    path(
    'seller_requests/<int:pk>/',SellerRequestDetailAdminView.as_view()),

    path('register/', RegisterView.as_view(), name='register'),
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),

    path('password_reset/', include('django_rest_passwordreset.urls', namespace='password_reset')),
    path('password_reset/verify_code/', verify_reset_code, name='verify_reset_code'),

]