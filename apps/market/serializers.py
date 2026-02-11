from rest_framework import serializers
from .models import *
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework import status, viewsets, generics, permissions, response
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from django.db.models import Q
from django_rest_passwordreset.models import ResetPasswordToken


User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('username', 'email', 'phone_number', 'password')
        extra_kwargs = {
            'password': {'write_only': True},
            'username': {'required': True},
            'phone_number': {'required': True},
        }

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Пользователь с таким email уже существует")
        return value

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("Пользователь с таким username уже существует")
        return value

    def validate_phone_number(self, value):
        if not value:
            raise serializers.ValidationError("Номер телефона обязателен")
        if User.objects.filter(phone_number=value).exists():
            raise serializers.ValidationError("Пользователь с таким номером уже существует")
        return value

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user

    def to_representation(self, instance):
        refresh = RefreshToken.for_user(instance)

        return {
            'user': {
                'username': instance.username,
                'email': instance.email,
                'phone_number': str(instance.phone_number),
            },
            'access': str(refresh.access_token),
            'refresh': str(refresh),
        }


class CustomLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        email = data.get('email')
        password = data.get('password')

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError({"email": "Пользователь с таким email не найден"})

        if not user.check_password(password):
            raise serializers.ValidationError({"password": "Неверный пароль"})

        if not user.is_active:
            raise serializers.ValidationError("Пользователь не активен")

        self.context['user'] = user
        return data

    def to_representation(self, instance):
        user = self.context['user']
        refresh = RefreshToken.for_user(user)

        return {
            'user': {
                'username': user.username,
                'email': user.email,
            },
            'access': str(refresh.access_token),
            'refresh': str(refresh),
        }


class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()

    def validate(self, attrs):
        token = attrs.get('refresh')
        try:
            RefreshToken(token)
        except Exception:
            raise serializers.ValidationError({"refresh": "Невалидный токен"})
        return attrs

class VerifyResetCodeSerializer(serializers.Serializer):
    email = serializers.EmailField()
    reset_code = serializers.IntegerField()
    new_password = serializers.CharField(write_only=True, min_length=6)
    confirm_password = serializers.CharField(write_only=True)

    def validate(self, data):
        email = data.get('email')
        reset_code = data.get('reset_code')
        new_password = data.get('new_password')
        confirm_password = data.get('confirm_password')

        if new_password != confirm_password:
            raise serializers.ValidationError("Пароли не совпадают.")

        try:
            token = ResetPasswordToken.objects.get(user__email=email, key=str(reset_code))
        except ResetPasswordToken.DoesNotExist:
            raise serializers.ValidationError("Неверный код сброса или email.")

        data['user'] = token.user
        data['token'] = token
        return data

    def save(self):
        user = self.validated_data['user']
        token = self.validated_data['token']
        new_password = self.validated_data['new_password']

        user.set_password(new_password)
        user.save()

        # Удаляем использованный токен
        token.delete()

class ClientSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ('id', 'username', 'email', 'first_name', 'last_name')

class SellerSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ('id', 'username', 'email', 'first_name', 'last_name')

class AdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ('id', 'username', 'email', 'first_name', 'last_name')

class StoreCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Store
        fields = ('id','store_name','store_image','store_description')


class StoreListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Store
        fields = ('id','store_name','store_image')


class StoreDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Store
        fields = ('id','store_name','store_image','store_description')


class SubCategorySimpleSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubCategory
        fields = ('id','subcategory_name','subcategory_image')

class CategoryListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ('id','category_name','category_image')

class CategoryDetailSerializer(serializers.ModelSerializer):
    subcategories = SubCategorySimpleSerializer(many=True,read_only=True)
    class Meta:
        model = Category
        fields = ('id','category_name','category_image','subcategories',)

class CategorySimpleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ('id','category_name',)


class SubCategoryListSerializers(serializers.ModelSerializer):
    category = CategorySimpleSerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(),
        source='category',
        write_only=True
    )

    class Meta:
        model = SubCategory
        fields = (
            'id',
            'category',
            'category_id',
            'subcategory_name',
            'subcategory_image',
        )

class SubCategoryDetailSerializers(serializers.ModelSerializer):
    category = CategorySimpleSerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(),
        source='category',
        write_only=True
    )


    class Meta:
        model = SubCategory
        fields = ('id','category', 'subcategory_name', 'subcategory_image','category_id')

class ProductImageCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ('id', 'product_image','product')


class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ('id','product_image',)

class ProductImageDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ('id', 'product_image')


class ProductCreateSerializers(serializers.ModelSerializer):
    images = ProductImageSerializer(many=True,read_only=True)

    class Meta:
        model = Product
        fields = ('id','product_subcategory', 'product_name', 'images',
                  'price','country','ingredients',
                  'best_before_date','action','quantity','description')





class StorSimpleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Store
        fields = ('id','store_name',)


class ProductListSerializers(serializers.ModelSerializer):
    store = StorSimpleSerializer(read_only=True)
    images  = ProductImageSerializer(many=True,read_only=True)
    avg_rating = serializers.ReadOnlyField()
    rating_count = serializers.SerializerMethodField()
    good_rate = serializers.ReadOnlyField()


    class Meta:
        model = Product
        fields = ('id','store','product_name','images','price','avg_rating','rating_count','good_rate',
)
    def get_rating_count(self, obj):
        return obj.get_count_rating()





class ProductDetailSerializers(serializers.ModelSerializer):
    images = ProductImageSerializer(many=True,read_only=True)
    store = StorSimpleSerializer(read_only=True)
    avg_rating = serializers.ReadOnlyField()
    good_rate = serializers.ReadOnlyField()




    class Meta:
        model = Product
        fields = ('id', 'store', 'product_name', 'images',
                  'price','country','ingredients',
                  'best_before_date','action','quantity','description','avg_rating','good_rate',
)

    def get_avg_rating(self, obj):
        return obj.avg_rating




class ProductMiniSerializers(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ('id', 'product_name')




class SaleSerializer(serializers.ModelSerializer):
    product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all())
    product_name = serializers.ReadOnlyField(source='product.product_name')
    product_price = serializers.ReadOnlyField(source='product.price')
    discounted_price = serializers.ReadOnlyField()
    is_currently_active = serializers.ReadOnlyField()
    start_date = serializers.DateTimeField(format='%d-%m-%Y',)
    end_date = serializers.DateTimeField(format='%d-%m-%Y',)



    class Meta:
        model = Sale
        fields = (
 'id','product','product_name', 'product_price', 'discount_percent',
 'discounted_price', 'description1','description2','is_active', 'start_date','end_date',
 'is_currently_active',
        )


class OrderItemSerializers(serializers.ModelSerializer):
    product_items = ProductMiniSerializers(read_only=True)

    class Meta:
        model = OrderItem
        fields = (
            'id','product', 'address','quantity','price','phone_number','product_items'
        )

class OrderSerializers(serializers.ModelSerializer):
    items = OrderItemSerializers(many=True, read_only=True)
    customer_username = serializers.CharField(source='customer.username', read_only=True)

    class Meta:
        model = Order
        fields = ('id','customer', 'customer_username','status','created_at','items',)

class UserProfileReviewSerializers(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ('id','email','first_name','last_name','phone_number','username')


class ReviewReplySerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.username', read_only=True)
    parent_user_name = serializers.SerializerMethodField()

    class Meta:
        model = Review
        fields = (
            'id',
            'user_name',
            'comment',
            'rating',
            'likes_count',
            'parent_user_name',
        )

    def get_parent_user_name(self, obj):
        if obj.parent:
            return obj.parent.user.username  # вот так берём имя родителя
        return None





class ReviewSerializers(serializers.ModelSerializer):
    user_reviews = UserProfileReviewSerializers(read_only=True)
    likes_count = serializers.ReadOnlyField()
    replies = serializers.SerializerMethodField()
    product  = ProductMiniSerializers(read_only=True)
    product_id = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.all(),
        source='product',
        write_only=True
    )

    class Meta:
        model = Review
        fields = (
            'id','user_reviews','product','rating','comment',
            'photo1','photo2','photo3','photo4','likes_count',
            'created_at','replies','parent','product_id',

        )

    def get_replies(self, obj):
        qs = obj.replies.all()
        return ReviewReplySerializer(qs, many=True).data


class ReviewDetailSerializers(serializers.ModelSerializer):
    user_reviews = UserProfileReviewSerializers(read_only=True)
    likes_count = serializers.ReadOnlyField()
    replies = serializers.SerializerMethodField()  # вложенные ответы

    class Meta:
        model = Review
        fields = (
            'id','user_reviews','product','rating','comment',
            'photo1','photo2','photo3','photo4','likes_count',
            'created_at','replies','parent'
        )
        read_only_fields = ['user', 'likes_count', 'created_at']

    def get_replies(self, obj):
        qs = obj.replies.all()
        return ReviewReplySerializer(qs, many=True).data






class CommentLikeSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.username', read_only=True)
    review_text = serializers.CharField(source='review.comment', read_only=True)
    total_likes = serializers.IntegerField(source='review.likes_count', read_only=True)  # вот здесь

    class Meta:
        model = CommentLike
        fields = ('id', 'user', 'review', 'user_name', 'review_text', 'total_likes', 'created_at')
        read_only_fields = ('created_at', 'user_name', 'review_text', 'total_likes')


class CartItemSerializer(serializers.ModelSerializer):
    product_name = serializers.ReadOnlyField(source='product.product_name')
    product_price = serializers.ReadOnlyField(source='product.price')
    total_price = serializers.ReadOnlyField()

    class Meta:
        model = CartItem
        fields = (
            'id','product','product_name','product_price','quantity', 'total_price',)


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    total_price = serializers.ReadOnlyField()

    class Meta:
        model = Cart
        fields = (
            'id','user','items','total_price',
        )
        read_only_fields = ('user',)

class FavoriteProductSerializer(serializers.ModelSerializer):
    product_name = serializers.ReadOnlyField(source='product.product_name')
    product_price = serializers.ReadOnlyField(source='product.price')
    created_date = serializers.DateTimeField(format='%d-%m-%Y', read_only=True)




    class Meta:
        model = FavoriteProduct
        fields = (
            'id','product','product_name','product_price','created_date',
        )
        read_only_fields = ('created_date',)


class FavoriteSerializer(serializers.ModelSerializer):
    items = FavoriteProductSerializer(many=True, read_only=True)

    class Meta:
        model = Favorite
        fields = ('id', 'items',)





class SellerRequestCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = SellerRequest
        fields = ('id','phone_number',)

    def create(self, validated_data):
        user = self.context['request'].user
        if not user.is_authenticated:
            raise serializers.ValidationError("Вы должны быть авторизованы")

        if hasattr(user, 'seller_request'):
            raise serializers.ValidationError('Заявка уже отправлена')

        return SellerRequest.objects.create(
            user=user,
            **validated_data
        )


class SellerRequestAdminSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField()

    class Meta:
        model = SellerRequest
        fields = '__all__'
