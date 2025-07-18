
from django.shortcuts import redirect, render, get_object_or_404
from django.http import HttpResponse
from django.contrib import messages  
from .models import Customer, Restaurant, Item, Cart 

import razorpay
from django.conf import settings

# Create your views here.
def index(request):
    return render(request, 'delivery/index.html')

def open_signin(request):
    return render(request, 'delivery/signin.html')

def open_signup(request):
    return render(request, 'delivery/signup.html')

def signup(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        email = request.POST.get('email')
        mobile = request.POST.get('mobile')
        address = request.POST.get('address')

        try:
            Customer.objects.get(username = username)
            messages.error(request, "Username already exists. Please choose a different one.") # Using messages framework
            return render(request, 'delivery/signup.html', {'error_message': "Duplicate username!"}) # Pass error for display
        except Customer.DoesNotExist: # Use specific exception for clarity
            Customer.objects.create(
                username = username,
                password = password,
                email = email,
                mobile = mobile,
                address = address,
            )
            messages.success(request, "Account created successfully! Please sign in.") # Using messages framework
            return render(request, 'delivery/signin.html')
    return render(request, 'delivery/signup.html') # Render signup page if not POST request


def signin(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        try:
            customer = Customer.objects.get(username=username, password=password) # Get the customer object
            if username == 'admin':
                return render(request, 'delivery/admin_home.html')
            else:
                restaurantList = Restaurant.objects.all()
                # Redirect to customer_home passing username in URL
                return redirect('customer_home', username=username) # Use redirect with args
        except Customer.DoesNotExist:
            messages.error(request, "Invalid username or password.") # Using messages framework
            return render(request, 'delivery/fail.html')
    return render(request, 'delivery/signin.html') # Render signin page if not POST

def open_add_restaurant(request):
    return render(request, 'delivery/add_restaurant.html')

def add_restaurant(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        picture = request.POST.get('picture')
        cuisine = request.POST.get('cuisine')
        rating = request.POST.get('rating')

        try:
            Restaurant.objects.get(name = name)
            messages.error(request, "Restaurant with this name already exists!") # Using messages framework
            return render(request, 'delivery/add_restaurant.html', {'error_message': "Duplicate restaurant!"}) # Pass error
        except Restaurant.DoesNotExist: # Use specific exception for clarity
            Restaurant.objects.create(
                name = name,
                picture = picture,
                cuisine = cuisine,
                rating = rating,
            )
            messages.success(request, "Restaurant added successfully!") # Using messages framework
    return render(request, 'delivery/admin_home.html') # Always render admin home after add attempt


def open_show_restaurant(request):
    restaurantList = Restaurant.objects.all()
    return render(request, 'delivery/show_restaurants.html',{"restaurantList" : restaurantList})

def open_update_restaurant(request, restaurant_id):
    restaurant = get_object_or_404(Restaurant, id = restaurant_id) # Use get_object_or_404
    return render(request, 'delivery/update_restaurant.html', {"restaurant" : restaurant})

def update_restaurant(request, restaurant_id):
    restaurant = get_object_or_404(Restaurant, id = restaurant_id) # Use get_object_or_404
    if request.method == 'POST':
        name = request.POST.get('name')
        picture = request.POST.get('picture')
        cuisine = request.POST.get('cuisine')
        rating = request.POST.get('rating')

        restaurant.name = name
        restaurant.picture = picture
        restaurant.cuisine = cuisine
        restaurant.rating = rating

        restaurant.save()
        messages.success(request, f"{restaurant.name} updated successfully!") # Using messages framework

    restaurantList = Restaurant.objects.all()
    return render(request, 'delivery/show_restaurants.html',{"restaurantList" : restaurantList})


def delete_restaurant(request, restaurant_id):
    restaurant = get_object_or_404(Restaurant, id = restaurant_id) # Use get_object_or_404
    restaurant_name = restaurant.name # Store name before deleting
    restaurant.delete()
    messages.success(request, f"{restaurant_name} deleted successfully!") # Using messages framework

    restaurantList = Restaurant.objects.all()
    return render(request, 'delivery/show_restaurants.html',{"restaurantList" : restaurantList})


def open_update_menu(request, restaurant_id):
    restaurant = get_object_or_404(Restaurant, id = restaurant_id) # Use get_object_or_404
    itemList = Item.objects.filter(restaurant=restaurant) # Filter by restaurant
    return render(request, 'delivery/update_menu.html',{"itemList" : itemList, "restaurant" : restaurant})

def update_menu(request, restaurant_id):
    restaurant = get_object_or_404(Restaurant, id = restaurant_id) # Use get_object_or_404

    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        price = request.POST.get('price')
        vegeterian = request.POST.get('vegeterian') == 'on'
        picture = request.POST.get('picture')

        try:
            # Check for duplicate item within the same restaurant
            Item.objects.get(name=name, restaurant=restaurant)
            messages.error(request, "Item with this name already exists in this restaurant!") # Using messages framework
            return HttpResponse("Duplicate item!") 
        except Item.DoesNotExist: 
            Item.objects.create(
                restaurant = restaurant,
                name = name,
                description = description,
                price = price,
                vegeterian = vegeterian,
                picture = picture,
            )
            messages.success(request, f"{name} added to {restaurant.name}'s menu!") # Using messages framework
    return render(request, 'delivery/admin_home.html')


def view_menu(request, restaurant_id, username):
    restaurant = get_object_or_404(Restaurant, id = restaurant_id) # Use get_object_or_404
    itemList = Item.objects.filter(restaurant=restaurant)
    # Store the last visited restaurant_id in session for 'Continue Shopping' in cart
    request.session['last_restaurant_id'] = restaurant_id
    request.session.modified = True
    return render(request, 'delivery/customer_menu.html',{"itemList" : itemList, "restaurant" : restaurant, "username":username})


def add_to_cart(request, item_id, username):
    item = get_object_or_404(Item, id=item_id)
    cart = request.session.get('cart', {})
    item_id_str = str(item.id)

    if item_id_str in cart:
        cart[item_id_str]['quantity'] += 1
        cart[item_id_str]['total_price'] = cart[item_id_str]['quantity'] * float(item.price)
    else:
        cart[item_id_str] = {
            'name': item.name,
            'price': float(item.price),
            'picture': item.picture if item.picture else '', 
            'quantity': 1,
            'total_price': float(item.price),
        }

    request.session['cart'] = cart
    request.session.modified = True

    messages.success(request, f"{item.name} added to cart!") 

    return redirect('view_menu', restaurant_id=item.restaurant.id, username=username)


# def show_cart(request, username):
#     cart = request.session.get('cart', {})
#     cart_items_list = []
#     cart_total = 0
#     for item_id, item_data in cart.items():
#         cart_items_list.append({
#             'id': item_id,
#             'name': item_data['name'],
#             'picture': item_data.get('picture', ''),
#             'price': item_data['price'],
#             'quantity': item_data['quantity'], 
#             'total_price': item_data['total_price'],
#         })
#         cart_total += item_data['total_price']
#     context = {
    #     'cart_items': cart_items_list,
    #     'cart_total': cart_total,
    #     'username': username,
    #     'restaurant_id': request.session.get('last_restaurant_id', None) # Use None for default if no last restaurant
    # }
    # return render(request, 'delivery/cart.html', context)


def show_cart(request, username):
    cart = request.session.get('cart', {})
    cart_items_list = []
    total_price = 0

    for item_id, item_data in cart.items():
        cart_items_list.append({
            'id': item_id,
            'name': item_data['name'],
            'picture': item_data.get('picture', ''),
            'price': item_data['price'],
            'quantity': item_data['quantity'],
            'total_price': item_data['total_price'],
            'description': item_data.get('description', 'No description')  # If you want description too
        })
        total_price += item_data['total_price']

    context = {
        'cart_items': cart_items_list,
        'total_price': total_price,
        'username': username,
        'restaurant_id': request.session.get('last_restaurant_id', None),
    }
    return render(request, 'delivery/cart.html', context)


    
def remove_from_cart(request, item_id, username):
    cart = request.session.get('cart', {})
    item_id_str = str(item_id)

    if item_id_str in cart:
        item_name = cart[item_id_str]['name']
        del cart[item_id_str]  # Remove the item from the cart
        request.session['cart'] = cart
        request.session.modified = True
        messages.info(request, f"{item_name} removed from cart.")
    else:
        messages.error(request, "Item not found in cart.")

    return redirect('show_cart', username=username)


# Checkout View - REWRITTEN TO USE SESSION CART
def checkout(request, username):
    cart = request.session.get('cart', {})
    cart_items_list = []
    cart_total = 0

    if not cart: # Check if cart is empty based on session
        messages.warning(request, "Your cart is empty. Please add items before checking out.")
        return redirect('show_cart', username=username) # Redirect back to empty cart page

    for item_id, item_data in cart.items():
        cart_items_list.append({
            'id': item_id,
            'name': item_data['name'],
            'picture': item_data.get('picture', ''),
            'price': item_data['price'],
            'quantity': item_data['quantity'],
            'total_price': item_data['total_price'],
        })
        cart_total += item_data['total_price']

    # Initialize Razorpay client
    client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

    # Create Razorpay order
    order_data = {
        'amount': int(cart_total * 100),  # Amount in paisa
        'currency': 'INR',
        'payment_capture': '1',  # Automatically capture payment
    }
    order = client.order.create(data=order_data)

    # Pass the order details to the frontend
    return render(request, 'delivery/checkout.html', {
        'username': username,
        'cart_items': cart_items_list, # Pass the list from session
        'total_price': cart_total, # Pass the calculated total from session
        'razorpay_key_id': settings.RAZORPAY_KEY_ID,
        'order_id': order['id'],  # Razorpay order ID
        'amount': cart_total, # Total amount
    })


# Orders Page - REWRITTEN TO USE SESSION CART
def orders(request, username):
    cart = request.session.get('cart', {})
    ordered_items = []
    total_paid = 0

    if not cart:
        messages.info(request, "You have no new orders to view (cart was empty).")
    else:
        for item_id, item_data in cart.items():
            ordered_items.append({
                'name': item_data['name'],
                'price': item_data['price'],
                'quantity': item_data['quantity'],
                'total_price': item_data['total_price'],
            })
            total_paid += item_data['total_price']

        # Clear the cart after "ordering" (simulating a successful order completion)
        request.session['cart'] = {}
        request.session.modified = True
        messages.success(request, "Your order has been placed successfully!")

    return render(request, 'delivery/orders.html', {
        'username': username,
        'ordered_items': ordered_items,
        'total_paid': total_paid,
    })


def customer_home(request, username):
    # Retrieve all restaurants to display on the customer home page
    restaurantList = Restaurant.objects.all()
    context = {
        'username': username,
        'restaurantList': restaurantList, # Pass restaurants to the template
    }
    return render(request, 'delivery/customer_home.html', context)