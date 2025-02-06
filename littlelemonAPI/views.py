from django.shortcuts import render, get_object_or_404
from rest_framework import generics, status, permissions
from .models import MenuItem
from littlelemonAPI.serializers import *
from .filters import MenuItemFilter
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from rest_framework.throttling import UserRateThrottle, AnonRateThrottle
from django.contrib.auth.models import User, Group
from datetime import date
from django.http import HttpResponseBadRequest
import math
# Create your views here.

class MenuItemsView(generics.ListCreateAPIView):
    queryset = MenuItem.objects.all()
    serializer_class = MenuItemSerializer
    throttle_classes = [AnonRateThrottle, UserRateThrottle]
    filter_backends = (DjangoFilterBackend, SearchFilter, OrderingFilter)
    filterset_class = MenuItemFilter
    search_fields = ['title', 'category__title']
    ordering_fields = ['price', 'title', 'category']
    
    def permission(self):
        permission_classes = []
        if self.request.method != "GET":
            permission_classes = [IsAuthenticated, IsAdminUser]
        return [permission() for permission in permission_classes]
    
    
class Authorized_Manager(permissions.BasePermission):
    def is_permitted(self, request, view):
        if request.user.group.filter(name="Manager").exists():
            return True
        
class Authorized_Delivery_Crew(permissions.BasePermission):
    def is_permitted(self, request, view):
        if request.user.group.filter(name="Delivery crew").exists():
            return True

class SingleMenuItemView(generics.RetrieveUpdateDestroyAPIView):
    queryset = MenuItem.objects.all()
    serializer_class = MenuItemSerializer
    throttle_classes = [AnonRateThrottle, UserRateThrottle]
    
    def permission(self):
        permission_classes = [IsAuthenticated]
        if self.request.method == "PATCH":
            permission_classes = [IsAuthenticated, Authorized_Manager | IsAdminUser]
        if self.request.method == "DELETE":
            permission_classes = [IsAuthenticated, IsAdminUser]
        return[permission() for permission in permission_classes]
    
    def patch(self, request, *args, **kwargs):
        menuitem = MenuItem.objects.get(pk=self.kwargs['pk'])
        menuitem.featured = not menuitem.featured
        menuitem.save()
        return Response({'message': '{} changed to {}'.format({str(menuitem.title)}, {str(menuitem.featured)})}, status.HTTP_200_OK)

class CategoryView(generics.ListCreateAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    throttle_classes = [AnonRateThrottle, UserRateThrottle]
    permission_classes = [IsAdminUser]


class ManagerView(APIView):
    queryset = User.objects.filter(groups__name='Manager')
    permission_classes = [IsAuthenticated, Authorized_Manager, IsAdminUser]
    serializer_class = ManagerSerializer
    throttle_classes = [AnonRateThrottle, UserRateThrottle]
    
    def post(self, request):
        username = request.data.get('username')
        if username:
            try:
                user = User.objects.get(username=username)
                group = Group.objects.get(name='Manager')
                group.user_set.add(user)
                return Response({"message": "User added to manager group."}, status=status.HTTP_200_OK)
            except User.DoesNotExist:
                return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)
            except Group.DoesNotExist:
                return Response({"error": "Group not found."}, status=status.HTTP_404_NOT_FOUND)
        return Response({"error": "Username is required."}, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request):
        username = request.data.get('username')
        if username:
            try:
                user = User.objects.get(username=username)
                group = Group.objects.get(name='Manager') 
                group.user_set.remove(user)
                return Response({"message": "User removed from manager group."}, status=status.HTTP_200_OK)
            except User.DoesNotExist:
                return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)
            except Group.DoesNotExist:
                return Response({"error": "Group not found."}, status=status.HTTP_404_NOT_FOUND)
        return Response({"error": "Username is required."}, status=status.HTTP_400_BAD_REQUEST)
    
class DeliveryCrewView(generics.ListCreateAPIView):
    throttle_classes = [AnonRateThrottle, UserRateThrottle]
    queryset = User.objects.filter(groups__name='Delivery crew')
    serializer_class = ManagerSerializer
    permission_classes = [IsAuthenticated, Authorized_Manager | IsAdminUser]

    def post(self, request, *args, **kwargs):
        username = request.data['username']
        if username:
            try:
                user = User.objects.get(username=username)
                group = Group.objects.get(name='Delivery crew') 
                group.user_set.add(user)
                return Response({"message": "User added to delivery crew."}, status=status.HTTP_201_CREATE  )
            except User.DoesNotExist:
                return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)
            except Group.DoesNotExist:
                return Response({"error": "Group not found."}, status=status.HTTP_404_NOT_FOUND)
        return Response({"error": "Username is required."}, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request):
        username = request.data.get('username')
        if username:
            try:
                user = User.objects.get(username=username)
                group = Group.objects.get(name='Delivery crew') 
                group.user_set.remove(user)
                return Response({"message": "User removed from delivery crew."}, status=status.HTTP_200_OK)
            except User.DoesNotExist:
                return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)
            except Group.DoesNotExist:
                return Response({"error": "Group not found."}, status=status.HTTP_404_NOT_FOUND)
        return Response({"error": "Username is required."}, status=status.HTTP_400_BAD_REQUEST)

class CartView(generics.ListCreateAPIView):
    throttle_classes = [AnonRateThrottle, UserRateThrottle]
    serializer_class = CartSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Cart.objects.filter(user=self.request.user)

    def post(self, request, *args, **kwargs):
        serialized_item = Add_To_Cart_Serializer(data=request.data)
        serialized_item.is_valid(raise_exception=True)
        id = request.data['menuitem']
        quantity = request.data['quantity']
        item = get_object_or_404(MenuItem, id=id)
        price = int(quantity) * item.price
        try:
            Cart.objects.create(user=request.user, quantity=quantity, unit_price=item.price, price=price, menuitem_id=id)
        except:
            return Response({'message':'Item is in cart!'}, status.HTTP_409_CONFLICT)
        return Response({'message':'Item added to cart!'}, status.HTTP_201_CREATED)
    
    def delete(self, request, *args, **kwargs):
        if request.data['menuitem']:
           serialized_item = Remove_From_Cart_Serializer(data=request.data)
           serialized_item.is_valid(raise_exception=True)
           menuitem = request.data['menuitem']
           cart = get_object_or_404(Cart, user=request.user, menuitem=menuitem )
           cart.delete()
           return Response({'message':'Item was removed from cart'}, status.HTTP_200_OK)
        else:
            Cart.objects.filter(user=request.user).delete()
            return Response({'message':'All Items were removed from cart'}, status.HTTP_200_OK)

class OrderView(generics.ListCreateAPIView):
    throttle_classes = [AnonRateThrottle, UserRateThrottle]
    serializer_class = OrderSerializer

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser or user.groups.filter(name="Managers").exists():
            return Order.objects.all()
        elif user.groups.filter(name='Delivery Crew').exists():
            return Order.objects.filter(delivery_crew = user) 
        else:
            return Order.objects.filter(user=user)

    def permission(self):
        if self.request.method == "GET" or "POST":
            permission_classes = [IsAuthenticated]
        else:
            permission_classes = [IsAuthenticated, Authorized_Manager| IsAdminUser]
        return [permission() for permission in permission_classes]
    
    def post(self, request, *args, **kwargs):
        cart = Cart.objects.filter(user=request.user)
        value_list=cart.values_list()
        if len(value_list) == 0:
            return HttpResponseBadRequest()
        total = math.fsum([float(value[-1]) for value in value_list])
        order = Order.objects.create(user=request.user, status=False, total=total, date=date.today())
        for i in cart.values():
            menuitem = get_object_or_404(MenuItem, id=i['menuitem_id'])
            orderitem = OrderItem.objects.create(order=order, menuitem=menuitem, quantity=i['quantity'])
            orderitem.save()
        cart.delete()
        return Response({'message':'Your order has been placed. Your id is {}'.format(str(order.id))}, status.HTTP_201_CREATED)

class SingleOrderView(generics.RetrieveUpdateAPIView):
    throttle_classes = [AnonRateThrottle, UserRateThrottle]
    serializer_class = SingleOrderSerializer
    
    def permission(self):
        user = self.request.user
        method = self.request.method
        order = Order.objects.get(pk=self.kwargs['pk'])
        if user == order.user and method == 'GET':
            permission_classes = [IsAuthenticated]
        elif method == 'PUT' or method == 'DELETE':
            permission_classes = [IsAuthenticated, Authorized_Manager | IsAdminUser]
        else:
            permission_classes = [IsAuthenticated, Authorized_Delivery_Crew | Authorized_Manager| IsAdminUser]
        return[permission() for permission in permission_classes] 

    def get_queryset(self, *args, **kwargs):
            query = OrderItem.objects.filter(order_id=self.kwargs['pk'])
            return query


    def patch(self, request, *args, **kwargs):
        order = Order.objects.get(pk=self.kwargs['pk'])
        order.status = not order.status
        order.save()
        return Response({'message':'Status of order #{} changed to {}'.format(str(order.id), str(order.status))}, status.HTTP_201_CREATED)

    def put(self, request, *args, **kwargs):
        serialized_item = DeliveryOrderSerializer(data=request.data)
        serialized_item.is_valid(raise_exception=True)
        order_pk = self.kwargs['pk']
        crew_pk = request.data['delivery_crew'] 
        order = get_object_or_404(Order, pk=order_pk)
        crew = get_object_or_404(User, pk=crew_pk)
        order.delivery_crew = crew
        order.save()
        return Response({'message':str(crew.username)+' was assigned to order #'+str(order.id)}, status.HTTP_201_CREATED)

    def delete(self, request, *args, **kwargs):
        order = Order.objects.get(pk=self.kwargs['pk'])
        order_number = str(order.id)
        order.delete()
        return Response({'message':f'Order #{order_number} was deleted'}, status.HTTP_200_OK)