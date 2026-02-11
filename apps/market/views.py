from coreapi import Client
from django.shortcuts import render
from .serializers import *
from rest_framework import status, viewsets, generics, permissions, response
from .models import *
from .permissions import *
from .filters import *
from  django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.utils import timezone
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.decorators import api_view


class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

class CustomLoginView(generics.GenericAPIView):
    serializer_class = CustomLoginSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class LogoutView(generics.GenericAPIView):
    serializer_class = LogoutSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            refresh_token = serializer.validated_data['refresh']
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response(status=status.HTTP_205_RESET_CONTENT)
        except Exception:
            return Response({'detail': 'Невалидный токен'}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
def verify_reset_code(request):
    serializer = VerifyResetCodeSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response({'message': 'Пароль успешно сброшен.'}, status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ClientAPIView(generics.ListAPIView):
    queryset = UserProfile.objects.filter(user_role='client')
    serializer_class = ClientSerializer

    def get_queryset(self):
        return UserProfile.objects.filter(id=self.request.user.id)


class SellerAPIView(generics.ListAPIView):
    queryset = UserProfile.objects.filter(user_role='seller')
    serializer_class = SellerSerializer

    def get_queryset(self):
        return UserProfile.objects.filter(id=self.request.user.id)


class AdminAPIView(generics.ListAPIView):
    queryset = UserProfile.objects.filter(user_role='seller')
    serializer_class = AdminSerializer

    def get_queryset(self):
        return UserProfile.objects.filter(id=self.request.user.id)


class StoreCreateAPIView(generics.ListCreateAPIView):
    queryset = Store.objects.all()
    serializer_class = StoreCreateSerializer
    permission_classes = (IsSeller,)

    def perform_create(self, serializer):
        if Store.objects.filter(store_owner=self.request.user).exists():
            raise serializers.ValidationError("У вас уже есть магазин")
        serializer.save(store_owner=self.request.user)


class StoreAPIView(generics.ListAPIView):
    queryset = Store.objects.all()
    serializer_class = StoreListSerializer

class StoreDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Store.objects.all()
    serializer_class = StoreDetailSerializer


class CategoryListAPIView(generics.ListCreateAPIView):
    queryset = Category.objects.all()
    serializer_class = CategoryListSerializer
    permission_classes = (IsAdminOrReadOnly,)

class CategoryDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Category.objects.prefetch_related('subcategories')
    serializer_class = CategoryDetailSerializer
    permission_classes = (IsAdminOrReadOnly,)

class SubCategoryListApiView(generics.ListCreateAPIView):
    queryset = SubCategory.objects.all()
    serializer_class = SubCategoryListSerializers
    permission_classes = (IsAdminOrReadOnly,)

class SubCategoryDetailApiView(generics.RetrieveUpdateDestroyAPIView):
    queryset = SubCategory.objects.all()
    serializer_class =  SubCategoryDetailSerializers
    permission_classes = (IsAdminOrReadOnly,)


class ProductCreateAPIView(generics.ListCreateAPIView):
    serializer_class = ProductCreateSerializers
    permission_classes = (IsProductOrReadProductOnly,)

    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated and user.user_role == 'seller':
            return Product.objects.filter(store__store_owner=user)
        return Product.objects.none()

    def perform_create(self, serializer):
        store = Store.objects.filter(store_owner=self.request.user).first()

        if not store:
            raise serializers.ValidationError("У вас нет магазина")

        serializer.save(store=store)

class ProductListAPIView(generics.ListAPIView):
    queryset =  Product.objects.all()
    serializer_class = ProductListSerializers
    filter_backends = [DjangoFilterBackend,SearchFilter]
    filterset_class = ProductFilter
    search_fields = ['product_name']



class ProductImageAPIView(generics.ListAPIView):
    queryset =  ProductImage.objects.all()
    serializer_class = ProductImageSerializer

class ProductImageCreateAPIView(generics.ListCreateAPIView):
    queryset =  ProductImage.objects.all()
    serializer_class = ProductImageCreateSerializer

class ProductImageDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = ProductImage.objects.all()
    serializer_class = ProductImageDetailSerializer

class ProductDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductDetailSerializers
    permission_classes = (IsProductOrReadProductOnly,)

class SaleListAPIView(generics.ListCreateAPIView):
    serializer_class = SaleSerializer

    def get_queryset(self):
        now = timezone.now()
        return Sale.objects.filter(
            is_active=True,
            start_date__lte=now,
            end_date__gte=now
        )


class SaleDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Sale.objects.all()
    serializer_class = SaleSerializer

class OrderAPIView(generics.ListAPIView):
    queryset = Order.objects.all()
    serializer_class = OrderSerializers

class OrderItemAPIView(generics.ListAPIView):
    queryset = OrderItem.objects.all()
    serializer_class = OrderItemSerializers



class ReviewListAPIView(generics.ListCreateAPIView):
    queryset = Review.objects.all()
    serializer_class = ReviewSerializers
    permission_classes = (permissions.IsAuthenticated,)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class ReviewDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Review.objects.all()
    serializer_class = ReviewSerializers
    permission_classes = (permissions.IsAuthenticated,)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class CommentListAPIView(generics.ListCreateAPIView):
    queryset = CommentLike.objects.all()
    serializer_class = CommentLikeSerializer


class CartAPIView(generics.RetrieveAPIView):
    serializer_class = CartSerializer

    def get_object(self):
        cart, _ = Cart.objects.get_or_create(user=self.request.user)
        return cart

class CartItemCreateAPIView(generics.CreateAPIView):
    serializer_class = CartItemSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def perform_create(self, serializer):
        cart, _ = Cart.objects.get_or_create(user=self.request.user)

        product = serializer.validated_data['product']
        quantity = serializer.validated_data.get('quantity', 1)

        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            product=product
        )

        if not created:
            cart_item.quantity += quantity
            cart_item.save()
        else:
            serializer.save(cart=cart)

class CartItemDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = CartItemSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        return CartItem.objects.filter(cart__user=self.request.user)

    def perform_update(self, serializer):
        quantity = serializer.validated_data.get('quantity')

        if quantity <= 0:
            serializer.instance.delete()
        else:
            serializer.save()


class FavoriteAPIView(generics.RetrieveAPIView):
    serializer_class = FavoriteSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_object(self):
        favorite, _ = Favorite.objects.get_or_create(user=self.request.user)
        return favorite

class FavoriteProductCreateAPIView(generics.CreateAPIView):
    queryset = FavoriteProduct.objects.all()

    serializer_class = FavoriteProductSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def perform_create(self, serializer):
        favorite, _ = Favorite.objects.get_or_create(user=self.request.user)
        product = serializer.validated_data['product']

        if FavoriteProduct.objects.filter(
            favorite=favorite,
            product=product
        ).exists():
            raise serializers.ValidationError(
                "Этот товар уже в избранном"
            )

        serializer.save(favorite=favorite)

class FavoriteProductDeleteAPIView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = FavoriteProductSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        return FavoriteProduct.objects.filter(
            favorite__user=self.request.user
        )

class SellerRequestCreateView(generics.ListCreateAPIView):
    serializer_class = SellerRequestCreateSerializer
    permission_classes = (permissions. IsAuthenticatedOrReadOnly ,)

    def get_queryset(self):
        return SellerRequest.objects.all()


class SellerRequestDetailAdminView(generics.RetrieveUpdateAPIView):
    queryset = SellerRequest.objects.all()
    serializer_class = SellerRequestAdminSerializer
    permission_classes = [IsAdminRole]

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        new_status = request.data.get('status')

        if instance.status != 'pending':
            return Response(
                {'error': 'Заявка уже обработана'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if new_status not in ['approved', 'rejected']:
            return Response(
                {'error': 'Недопустимый статус'},
                status=status.HTTP_400_BAD_REQUEST
            )

        instance.status = new_status
        instance.save()

        if new_status == 'approved':
            user = instance.user
            user.user_role = 'seller'
            user.save()

            Store.objects.create(
                store_owner=user,
                store_name=f'Магазин {user.username}'
            )

        return Response({'status': new_status})



