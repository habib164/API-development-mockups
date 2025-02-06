from rest_framework import serializers
from .models import MenuItem, Category, Cart, Order, OrderItem
from decimal import Decimal
import bleach
from django.contrib.auth.models import User


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'slug', 'title']

class MenuItemSerializer(serializers.ModelSerializer):
    #goods = serializers.IntegerField(source = 'inventory')
    featured = serializers.BooleanField()
    category = CategorySerializer(read_only=True)
    def validate_title(self, value):
        return bleach.clean(value)
    
    class Meta:
        model = MenuItem
        fields = ['id', 'title', 'price', 'category', 'featured']
        extra_kwargs = {
            'price' : {'min_value':2},
        }

class ManagerSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email']


class CartMenuItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = MenuItem
        fields = ['id','title','price']


class CartSerializer(serializers.ModelSerializer):
    menuitem = CartMenuItemSerializer()
    class Meta:
        model = Cart
        fields = ['menuitem','quantity','price']
        
        
class Add_To_Cart_Serializer(serializers.ModelSerializer):
    class Meta:
        model = Cart
        fields = ['menuitem','quantity']
        extra_kwargs = {
            'quantity': {'min_value': 1},
        }
        
        
class Remove_From_Cart_Serializer(serializers.ModelSerializer):
    class Meta:
        model = Cart
        fields = ['menuitem']


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username']
        

class OrderSerializer(serializers.ModelSerializer):
    user = UserSerializer()
    class Meta:
        model = Order
        fields = ['id','user','total','status','delivery_crew','date']
        

class OneMenuSerializer(serializers.ModelSerializer):
    class Meta:
        model = MenuItem
        fields = ['title','price']
        
        
class SingleOrderSerializer(serializers.ModelSerializer):
    menuitem = OneMenuSerializer()
    class Meta:
        model = OrderItem
        fields = ['menuitem','quantity']


class DeliveryOrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ['delivery_crew']

