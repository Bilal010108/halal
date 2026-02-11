from django_filters import FilterSet
from .models import *



class ProductFilter(FilterSet):
    class Meta:
        model = Product
        fields = {
            'product_subcategory': ['exact'],
            'price': ['gt', 'lt'],}