from rest_framework.generics import CreateAPIView, ListCreateAPIView

from .serializers import *
from rest_framework import status, viewsets, generics, permissions, response
from .models import *
from .permissions import *
from .filters import *
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.utils import timezone
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.decorators import api_view
from django.db.models import Count, Sum, Avg, Q, F, DecimalField
from django.db.models.functions import Coalesce
from datetime import datetime, timedelta
from .services import create_order_from_cart
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser


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
    serializer_class = ClientSerializer
    permission_classes = (permissions.IsAuthenticated,)

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

class StoreAPIView(generics.ListAPIView):
    queryset = Store.objects.all()
    serializer_class = StoreListSerializer
    parser_classes = (JSONParser, MultiPartParser, FormParser)

    def get_queryset(self):
        return Store.objects.filter(store_owner=self.request.user.id)

class StoreDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Store.objects.all()
    serializer_class = StoreDetailSerializer
    parser_classes = (MultiPartParser, FormParser)
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Store.objects.filter(store_owner=self.request.user.id)

class CategoryListAPIView(generics.ListCreateAPIView):
    queryset = Category.objects.all()
    serializer_class = CategoryListSerializer
    permission_classes = (IsAdminOrReadOnly,)
    parser_classes = (MultiPartParser, FormParser,JSONParser)

class CategoryDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Category.objects.prefetch_related('subcategories')
    serializer_class = CategoryDetailSerializer
    permission_classes = (IsAdminOrReadOnly,)
    parser_classes = (MultiPartParser, FormParser,JSONParser)

class SubCategoryListApiView(generics.ListCreateAPIView):
    queryset = SubCategory.objects.all()
    serializer_class = SubCategoryListSerializers
    permission_classes = (IsAdminOrReadOnly,)
    parser_classes = (MultiPartParser, FormParser,JSONParser)

class SubCategoryDetailApiView(generics.RetrieveUpdateDestroyAPIView):
    queryset = SubCategory.objects.all()
    serializer_class = SubCategoryDetailSerializers
    permission_classes = (IsAdminOrReadOnly,)
    parser_classes = (MultiPartParser, FormParser,JSONParser)

class ProductCreateAPIView(generics.ListCreateAPIView):
    serializer_class = ProductCreateSerializers
    permission_classes = (IsProductOrReadProductOnly,)
    parser_classes = (MultiPartParser, FormParser,JSONParser)

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
    queryset = Product.objects.all()
    serializer_class = ProductListSerializers
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_class = ProductFilter
    search_fields = ['product_name']
    parser_classes = (MultiPartParser, FormParser,JSONParser)

class ProductImageAPIView(generics.ListAPIView):
    queryset = ProductImage.objects.all()
    serializer_class = ProductImageSerializer
    parser_classes = (MultiPartParser, FormParser,JSONParser)

class ProductImageCreateAPIView(generics.ListCreateAPIView):
    queryset = ProductImage.objects.all()
    serializer_class = ProductImageCreateSerializer
    parser_classes = (MultiPartParser, FormParser,JSONParser)

class ProductImageDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = ProductImage.objects.all()
    serializer_class = ProductImageDetailSerializer
    parser_classes = (MultiPartParser, FormParser,JSONParser)

class ProductDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductDetailSerializers
    permission_classes = (IsProductOrReadProductOnly,)
    parser_classes = (MultiPartParser, FormParser,JSONParser)

class SaleListAPIView(generics.ListCreateAPIView):
    serializer_class = SaleSerializer

    def get_queryset(self):
        now = timezone.now()
        return Sale.objects.filter(is_active=True, start_date__lte=now, end_date__gte=now)

class SaleDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Sale.objects.all()
    serializer_class = SaleSerializer

class ReviewListAPIView(generics.ListCreateAPIView):
    queryset = Review.objects.all()
    serializer_class = ReviewSerializers
    permission_classes = (permissions.IsAuthenticated,)
    parser_classes = (JSONParser, MultiPartParser, FormParser)

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
    permission_classes = (permissions.IsAuthenticated,)

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
        existing = CartItem.objects.filter(cart=cart, product=product)
        if existing.exists():
            cart_item = existing.first()
            existing.exclude(pk=cart_item.pk).delete()
            cart_item.quantity += quantity
            cart_item.save()
        else:
            serializer.save(cart=cart)


class CartItemDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = CartItemSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return CartItem.objects.none()
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
        if FavoriteProduct.objects.filter(favorite=favorite, product=product).exists():
            raise serializers.ValidationError("Этот товар уже в избранном")
        serializer.save(favorite=favorite)

class FavoriteProductDeleteAPIView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = FavoriteProductSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return FavoriteProduct.objects.none()
        return FavoriteProduct.objects.filter(favorite__user=self.request.user)

class SellerRequestCreateView(generics.ListCreateAPIView):
    serializer_class = SellerRequestCreateSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)

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
            return Response({'error': 'Заявка уже обработана'}, status=status.HTTP_400_BAD_REQUEST)

        if new_status not in ['approved', 'rejected']:
            return Response({'error': 'Недопустимый статус'}, status=status.HTTP_400_BAD_REQUEST)

        instance.status = new_status
        instance.save()

        if new_status == 'approved':
            user = instance.user
            user.user_role = 'seller'
            user.save()
            Store.objects.create(store_owner=user, store_name=f'Магазин {user.username}')

        return Response({'status': new_status})


class MonthlyAnalyticsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        if request.user.user_role != 'admin':
            return Response(
                {'error': 'Только администраторы имеют доступ к аналитике'},
                status=status.HTTP_403_FORBIDDEN
            )

        year = request.query_params.get('year', timezone.now().year)
        month = request.query_params.get('month', timezone.now().month)

        try:
            year = int(year)
            month = int(month)
        except (ValueError, TypeError):
            return Response({'error': 'Неверный формат года или месяца'}, status=status.HTTP_400_BAD_REQUEST)

        period_start = datetime(year, month, 1).date()
        if month == 12:
            period_end = datetime(year + 1, 1, 1).date()
        else:
            period_end = datetime(year, month + 1, 1).date()

        data = {
            'period_start': period_start,
            'period_end': period_end,
            'orders_stats': self._get_orders_stats(period_start, period_end),
            'sales_overview': self._get_sales_overview(period_start, period_end),
            'seller_stats': self._get_seller_stats(period_start, period_end),
            'store_stats': self._get_store_stats(period_start, period_end),
            'top_products': self._get_top_products(period_start, period_end),
            'popular_categories': self._get_popular_categories(period_start, period_end),
            'top_sellers': self._get_top_sellers(period_start, period_end),
        }

        serializer = AnalyticsDashboardSerializer(data)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def _get_orders_stats(self, start_date, end_date):
        orders = Order.objects.filter(
            created_at__date__gte=start_date,
            created_at__date__lt=end_date
        )
        total_orders = orders.count()

        if total_orders == 0:
            return {
                'total_orders': 0,
                'pending_orders': 0,
                'shipped_orders': 0,
                'delivered_orders': 0,
                'cancelled_orders': 0,
                'pending_percent': Decimal('0.00'),
                'shipped_percent': Decimal('0.00'),
                'delivered_percent': Decimal('0.00'),
                'cancelled_percent': Decimal('0.00'),
            }

        status_counts = orders.values('status').annotate(count=Count('id'))
        status_dict = {item['status']: item['count'] for item in status_counts}

        pending = status_dict.get('ожидании', 0)
        shipped = status_dict.get('Отправлен', 0)
        delivered = status_dict.get('Доставлен', 0)
        cancelled = status_dict.get('Отменён', 0)

        return {
            'total_orders': total_orders,
            'pending_orders': pending,
            'shipped_orders': shipped,
            'delivered_orders': delivered,
            'cancelled_orders': cancelled,
            'pending_percent': round(Decimal(pending * 100) / total_orders, 2),
            'shipped_percent': round(Decimal(shipped * 100) / total_orders, 2),
            'delivered_percent': round(Decimal(delivered * 100) / total_orders, 2),
            'cancelled_percent': round(Decimal(cancelled * 100) / total_orders, 2),
        }

    def _get_sales_overview(self, start_date, end_date):
        current_orders = Order.objects.filter(
            created_at__date__gte=start_date,
            created_at__date__lt=end_date,
            status__in=['Отправлен', 'Доставлен']
        )
        current_items = OrderItem.objects.filter(order__in=current_orders).aggregate(
            total=Coalesce(Sum(F('price') * F('quantity'), output_field=DecimalField()), Decimal('0.00')),
            count=Count('id')
        )
        total_sales = current_items['total'] or Decimal('0.00')
        total_orders = current_orders.count()
        average_order_value = (total_sales / total_orders) if total_orders > 0 else Decimal('0.00')

        prev_start = start_date - timedelta(days=start_date.day)
        prev_end = start_date
        prev_orders = Order.objects.filter(
            created_at__date__gte=prev_start,
            created_at__date__lt=prev_end,
            status__in=['Отправлен', 'Доставлен']
        )
        prev_items = OrderItem.objects.filter(order__in=prev_orders).aggregate(
            total=Coalesce(Sum(F('price') * F('quantity'), output_field=DecimalField()), Decimal('0.00'))
        )
        previous_month_sales = prev_items['total'] or Decimal('0.00')

        if previous_month_sales > 0:
            growth_amount = total_sales - previous_month_sales
            growth_percent = round((growth_amount / previous_month_sales) * 100, 2)
        else:
            growth_amount = total_sales
            growth_percent = Decimal('100.00') if total_sales > 0 else Decimal('0.00')

        return {
            'total_sales': total_sales,
            'total_orders': total_orders,
            'average_order_value': round(average_order_value, 2),
            'previous_month_sales': previous_month_sales,
            'sales_growth_percent': growth_percent,
            'sales_growth_amount': growth_amount,
        }

    def _get_seller_stats(self, start_date, end_date):
        active_sellers = UserProfile.objects.filter(
            user_role='seller',
            store__product__order_items__order__created_at__date__gte=start_date,
            store__product__order_items__order__created_at__date__lt=end_date,
            store__product__order_items__order__status__in=['Отправлен', 'Доставлен']
        ).distinct().count()

        new_sellers = UserProfile.objects.filter(
            user_role='seller',
            date_joined__date__gte=start_date,
            date_joined__date__lt=end_date
        ).count()

        total_sellers = UserProfile.objects.filter(user_role='seller').count()

        if total_sellers == 0:
            return {
                'active_sellers': 0,
                'new_sellers': 0,
                'total_sellers': 0,
                'active_percent': Decimal('0.00'),
                'new_percent': Decimal('0.00'),
            }

        return {
            'active_sellers': active_sellers,
            'new_sellers': new_sellers,
            'total_sellers': total_sellers,
            'active_percent': round(Decimal(active_sellers * 100) / total_sellers, 2),
            'new_percent': round(Decimal(new_sellers * 100) / total_sellers, 2),
        }

    def _get_store_stats(self, start_date, end_date):
        total_stores = Store.objects.count()

        if total_stores == 0:
            return {
                'active_stores': 0,
                'total_stores': 0,
                'inactive_stores': 0,
                'active_percent': Decimal('0.00'),
                'inactive_percent': Decimal('0.00'),
                'stores_with_1_5_orders': 0,
                'stores_with_6_20_orders': 0,
                'stores_with_20_plus_orders': 0,
            }

        stores_with_sales = Store.objects.filter(
            product__order_items__order__created_at__date__gte=start_date,
            product__order_items__order__created_at__date__lt=end_date,
            product__order_items__order__status__in=['Отправлен', 'Доставлен']
        ).annotate(orders_count=Count('product__order_items__order', distinct=True))

        active_stores = stores_with_sales.count()
        inactive_stores = total_stores - active_stores

        stores_1_5 = stores_with_sales.filter(orders_count__gte=1, orders_count__lte=5).count()
        stores_6_20 = stores_with_sales.filter(orders_count__gte=6, orders_count__lte=20).count()
        stores_20_plus = stores_with_sales.filter(orders_count__gt=20).count()

        return {
            'active_stores': active_stores,
            'total_stores': total_stores,
            'inactive_stores': inactive_stores,
            'active_percent': round(Decimal(active_stores * 100) / total_stores, 2),
            'inactive_percent': round(Decimal(inactive_stores * 100) / total_stores, 2),
            'stores_with_1_5_orders': stores_1_5,
            'stores_with_6_20_orders': stores_6_20,
            'stores_with_20_plus_orders': stores_20_plus,
        }

    def _get_top_products(self, start_date, end_date, limit=10):
        products = OrderItem.objects.filter(
            order__created_at__date__gte=start_date,
            order__created_at__date__lt=end_date,
            order__status__in=['Отправлен', 'Доставлен']
        ).values(
            'product__id',
            'product__product_name',
            'product__store__store_name'
        ).annotate(
            total_quantity=Sum('quantity'),
            total_revenue=Sum(F('price') * F('quantity'), output_field=DecimalField()),
            orders_count=Count('order', distinct=True)
        ).order_by('-total_revenue')[:limit]

        result = []
        for item in products:
            result.append({
                'product_id': item['product__id'],
                'product_name': item['product__product_name'] or 'Без названия',
                'store_name': item['product__store__store_name'] or 'Без магазина',
                'total_quantity': item['total_quantity'],
                'total_revenue': item['total_revenue'] or Decimal('0.00'),
                'orders_count': item['orders_count'],
            })
        return result

    def _get_popular_categories(self, start_date, end_date):
        total_stats = OrderItem.objects.filter(
            order__created_at__date__gte=start_date,
            order__created_at__date__lt=end_date,
            order__status__in=['Отправлен', 'Доставлен']
        ).aggregate(
            total_sales=Coalesce(Sum(F('price') * F('quantity'), output_field=DecimalField()), Decimal('0.00')),
            total_orders=Count('order', distinct=True)
        )
        total_sales = total_stats['total_sales'] or Decimal('0.00')
        total_orders = total_stats['total_orders'] or 0

        categories = OrderItem.objects.filter(
            order__created_at__date__gte=start_date,
            order__created_at__date__lt=end_date,
            order__status__in=['Отправлен', 'Доставлен']
        ).values(
            'product__product_subcategory__category__id',
            'product__product_subcategory__category__category_name'
        ).annotate(
            total_sales=Sum(F('price') * F('quantity'), output_field=DecimalField()),
            orders_count=Count('order', distinct=True),
            products_sold=Sum('quantity')
        ).order_by('-total_sales')

        result = []
        for cat in categories:
            category_sales = cat['total_sales'] or Decimal('0.00')
            category_orders = cat['orders_count'] or 0
            result.append({
                'category_id': cat['product__product_subcategory__category__id'],
                'category_name': cat['product__product_subcategory__category__category_name'] or 'Без категории',
                'total_sales': category_sales,
                'orders_count': category_orders,
                'products_sold': cat['products_sold'] or 0,
                'sales_percent': round((category_sales / total_sales * 100), 2) if total_sales > 0 else Decimal('0.00'),
                'orders_percent': round(Decimal(category_orders * 100) / total_orders, 2) if total_orders > 0 else Decimal('0.00'),
            })
        return result

    def _get_top_sellers(self, start_date, end_date, limit=5):
        total_revenue = OrderItem.objects.filter(
            order__created_at__date__gte=start_date,
            order__created_at__date__lt=end_date,
            order__status__in=['Отправлен', 'Доставлен']
        ).aggregate(
            total=Coalesce(Sum(F('price') * F('quantity'), output_field=DecimalField()), Decimal('0.00'))
        )['total'] or Decimal('0.00')

        sellers = OrderItem.objects.filter(
            order__created_at__date__gte=start_date,
            order__created_at__date__lt=end_date,
            order__status__in=['Отправлен', 'Доставлен']
        ).values(
            'product__store__store_owner__id',
            'product__store__store_owner__username',
            'product__store__store_name'
        ).annotate(
            total_revenue=Sum(F('price') * F('quantity'), output_field=DecimalField()),
            orders_count=Count('order', distinct=True),
            products_sold=Sum('quantity')
        ).order_by('-total_revenue')[:limit]

        result = []
        for seller in sellers:
            seller_revenue = seller['total_revenue'] or Decimal('0.00')
            seller_orders = seller['orders_count'] or 0
            result.append({
                'seller_id': seller['product__store__store_owner__id'],
                'seller_username': seller['product__store__store_owner__username'],
                'store_name': seller['product__store__store_name'] or 'Без названия',
                'total_revenue': seller_revenue,
                'orders_count': seller_orders,
                'products_sold': seller['products_sold'] or 0,
                'average_order_value': round(seller_revenue / seller_orders, 2) if seller_orders > 0 else Decimal('0.00'),
                'revenue_percent': round((seller_revenue / total_revenue * 100), 2) if total_revenue > 0 else Decimal('0.00'),
            })
        return result


class OrdersStatsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        if request.user.user_role != 'admin':
            return Response({'error': 'Доступ запрещен'}, status=status.HTTP_403_FORBIDDEN)

        year = int(request.query_params.get('year', timezone.now().year))
        month = int(request.query_params.get('month', timezone.now().month))
        period_start = datetime(year, month, 1).date()
        period_end = datetime(year, month + 1, 1).date() if month < 12 else datetime(year + 1, 1, 1).date()

        view = MonthlyAnalyticsView()
        data = view._get_orders_stats(period_start, period_end)
        serializer = MonthlyOrderStatsSerializer(data)
        return Response(serializer.data)


class TopProductsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        if request.user.user_role != 'admin':
            return Response({'error': 'Доступ запрещен'}, status=status.HTTP_403_FORBIDDEN)

        year = int(request.query_params.get('year', timezone.now().year))
        month = int(request.query_params.get('month', timezone.now().month))
        limit = int(request.query_params.get('limit', 10))
        period_start = datetime(year, month, 1).date()
        period_end = datetime(year, month + 1, 1).date() if month < 12 else datetime(year + 1, 1, 1).date()

        view = MonthlyAnalyticsView()
        data = view._get_top_products(period_start, period_end, limit)
        serializer = ProductSalesSerializer(data, many=True)
        return Response(serializer.data)


class TopSellersView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        if request.user.user_role != 'admin':
            return Response({'error': 'Доступ запрещен'}, status=status.HTTP_403_FORBIDDEN)

        year = int(request.query_params.get('year', timezone.now().year))
        month = int(request.query_params.get('month', timezone.now().month))
        limit = int(request.query_params.get('limit', 5))
        period_start = datetime(year, month, 1).date()
        period_end = datetime(year, month + 1, 1).date() if month < 12 else datetime(year + 1, 1, 1).date()

        view = MonthlyAnalyticsView()
        data = view._get_top_sellers(period_start, period_end, limit)
        serializer = TopSellerSerializer(data, many=True)
        return Response(serializer.data)


class AdminSellerRequestsView(generics.ListAPIView):
    serializer_class = SellerRequestSerializer
    permission_classes = [IsAdminOrReadOnly]

    def get_queryset(self):
        return SellerRequest.objects.select_related('user').order_by('-created_at')


class AdminSellerRequestDetailView(generics.RetrieveUpdateAPIView):
    queryset = SellerRequest.objects.all()
    serializer_class = SellerRequestSerializer
    permission_classes = [IsAdminOrReadOnly]

    def perform_update(self, serializer):
        new_status = self.request.data.get('status')
        instance = serializer.save(status=new_status)

        if new_status == 'approved':
            user = instance.user
            user.user_role = 'seller'
            user.save(update_fields=['user_role'])
            Store.objects.get_or_create(
                store_owner=user,
                defaults={'store_name': f'Магазин {user.username}'}
            )


class UserOrderListAPIView(generics.ListAPIView):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user)

class CreateOrderAPIView(ListCreateAPIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        phone_number = request.data.get('phone_number')
        address = request.data.get('address')

        if not phone_number or not address:
            return Response(
                {'error': 'Укажите телефон и адрес доставки'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            order = create_order_from_cart(request.user, phone_number, address)
            serializer = OrderSerializer(order)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except DjangoValidationError as e:
            return Response({'error': e.messages}, status=status.HTTP_400_BAD_REQUEST)


class SellerOrderListView(generics.ListAPIView):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Order.objects.filter(
            items__product__store__store_owner=self.request.user
        ).distinct()


class SellerOrderUpdateView(generics.RetrieveUpdateAPIView):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Order.objects.filter(
            items__product__store__store_owner=self.request.user
        ).distinct()

    def patch(self, request, *args, **kwargs):
        order = self.get_object()
        new_status = request.data.get('status')

        allowed = ['ожидании', 'Отправлен', 'Доставлен', 'Отменён']
        if new_status not in allowed:
            return Response({'error': 'Неверный статус'}, status=400)

        order.status = new_status
        order.save()
        return Response(OrderSerializer(order).data)