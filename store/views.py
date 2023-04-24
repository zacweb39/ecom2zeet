from django.shortcuts import render, get_object_or_404, redirect
from django.views import View
from .models import Category, Product, Cart, CartItem, Order, OrderItem, Contact, Review
from django.core.exceptions import ObjectDoesNotExist
from .forms import PaymentForm, SignUpForm, ContactForm
from django.http import HttpRequest, HttpResponse
from django.views.decorators.csrf import csrf_protect, csrf_exempt
from django.contrib.auth.models import Group, User
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import login, authenticate, logout
import requests
import json
from django.contrib.auth.decorators import login_required
from random import randint

def home(request, category_slug=None):
    category_page = None
    product = None
    if  category_slug!=None:
         category_page = get_object_or_404(Category,slug=category_slug)
         products = Product.objects.filter(category=category_page, available=True)
    else:
        products = Product.objects.all().filter(available=True)
    return render(request, 'home.html', {'category': category_page, 'products': products})

def productPage(request, category_slug, product_slug):
    try:
        product = Product.objects.get(category__slug=category_slug, slug=product_slug)
    except Exception as e:
        raise e

    if request.method == 'POST' and request.user.is_authenticated and request.POST['content'].strip() != '':
        Review.objects.create(product=product, user=request.user, content=request.POST['content'])

    reviews = Review.objects.filter(product=product)

    return render(request, 'product.html', {'product': product, 'reviews': reviews})

def _cart_id(request):
    cart = request.session.session_key
    if not cart:
        cart = request.session.create()
    return cart

def add_cart(request, product_id):
    product = Product.objects.get(id=product_id)
    try:
        cart = Cart.objects.get(cart_id=_cart_id(request))
    except Cart.DoesNotExist:
        cart = Cart.objects.create(
                cart_id = _cart_id(request)
        )
    cart.save()
    try:
        cart_item = CartItem.objects.get(product=product, cart=cart)
        if cart_item.quantity < cart_item.product.stock:
            cart_item.quantity += 1
        cart_item.save()
    except CartItem.DoesNotExist:
        cart_item = CartItem.objects.create(
                    product = product,
                    quantity = 1,
                    cart = cart
            )
        cart_item.save()

    return redirect('cart_detail')

def cart_detail(request, total=0, counter=0, cart_items=None):
    try:
        cart = Cart.objects.get(cart_id=_cart_id(request))
        cart_items = CartItem.objects.filter(cart=cart, active=True)
        for cart_item in cart_items:
            total += (cart_item.product.price * cart_item.quantity)
            counter += cart_item.quantity
            amount = float(total)
            reference = randint(0, 1000000)
        payment_form = PaymentForm(request.POST)
        if payment_form.is_valid():
            name= payment_form.cleaned_data.get("name")
            email= payment_form.cleaned_data.get("email")
            phone= payment_form.cleaned_data.get("phone")

            data = json.dumps({
                "username": "",
                "password": "",
                "action": "mmdeposit",
                "amount": amount,
                "currency": "UGX",
                "phone": phone,
                "reference": reference,
                "reason": "Payment"
            })

            response = requests.post("https://www.easypay.co.ug/api/", data = data)
            status = response.text

            try:
                order_details = Order.objects.create(
                    name=name,
                    emailAddress=email,
                    phone=phone,
                    total=total,
                    status=status
                )
                order_details.save()

                for order_item in cart_items:
                    or_item = OrderItem.objects.create(
                            product = order_item.product.name,
                            quantity = order_item.quantity,
                            price = order_item.product.price,
                            order = order_details
                        )
                    or_item.save()

                    #reduce stock
                    products = Product.objects.get(id=order_item.product.id)
                    products.stock = int(order_item.product.stock - order_item.quantity)
                    products.save()
                    order_item.delete()

            except ObjectDoesNotExist:
                    pass
            return redirect('thanks_page', order_details.id)

    except  ObjectDoesNotExist:
        pass
    return render(request, 'cart.html', dict(cart_items=cart_items, total=total, counter=counter, payment_form=payment_form))

def cart_remove(request, product_id):
    cart = Cart.objects.get(cart_id=_cart_id(request))
    product = get_object_or_404(Product, id=product_id)
    cart_item = CartItem.objects.get(product=product, cart=cart)
    if cart_item.quantity > 1:
        cart_item.quantity -= 1
        cart_item.save()
    else:
        cart_item.delete()
    return redirect('cart_detail')

def cart_remove_product(request, product_id):
    cart = Cart.objects.get(cart_id=_cart_id(request))
    product = get_object_or_404(Product, id=product_id)
    cart_item = CartItem.objects.get(product=product, cart=cart)
    cart_item.delete()
    return redirect('cart_detail')

def signupView(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            signup_user = User.objects.get(username=username)
            customer_group =Group.objects.get(name='Customer')
            customer_group.user_set.add(signup_user)
    else:
        form = SignUpForm()
    return render(request, 'signup.html', {'form': form})

def signinView(request):
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            username = request.POST['username']
            password = request.POST['password']
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('home')
            else:
                return redirect('signup')
    else:
        form = AuthenticationForm()
    return render(request, 'signin.html', {'form':form})

def signoutView(request):
    logout(request)
    return redirect('signin')

@csrf_exempt
def webhookView(request):
    message = request.body
    record = Order.objects.get(id=6)
    record.status = "message"
    record.save(update_fields=['status'])
    return redirect('home')

@login_required(redirect_field_name='next', login_url='signin')
def orderHistory(request):
    if request.user.is_authenticated:
        email = str(request.user.email)
        order_details = Order.objects.filter(emailAddress=email)
    return render(request, 'order_list.html', {'order_details':order_details})

@login_required(redirect_field_name='next', login_url='signin')
def viewOrder(request, order_id):
    if request.user.is_authenticated:
        email = str(request.user.email)
        order = Order.objects.get(id=order_id, emailAddress=email)
        order_items = OrderItem.objects.filter(order=order)
    return render(request, 'order_detail.html', {'order':order, 'order_items': order_items})

def thanks_page(request, order_id):
    if order_id:
        customer_order = get_object_or_404(Order, id=order_id)
    return render(request, 'thankyou.html', {'customer_order': customer_order})

def search(request):
    products = Product.objects.filter(name__contains=request.GET['name'])
    return render(request, 'home.html', {'products': products})

def contact(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            subject = form.cleaned_data.get('subject')
            from_email = form.cleaned_data.get('from_email')
            message = form.cleaned_data.get('message')
            name = form.cleaned_data.get('name')
            phone = form.cleaned_data.get('phone')

            try:
                contact_details = Contact.objects.create(
                    subject=subject,
                    from_email=from_email,
                    message=message,
                    name=name,
                    phone=phone
                )
                contact_details.save()
            except ObjectDoesNotExist:
                pass
            return render(request, 'contact_success.html')
    else:
        form = ContactForm()
    return render(request, 'contact.html', {'form': form})

def about(request):
    return render(request, 'about.html')






# Create your views here.
