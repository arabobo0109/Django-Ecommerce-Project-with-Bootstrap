from django.shortcuts import render,redirect,get_object_or_404
from django.http import HttpResponse
from django.core.exceptions import ObjectDoesNotExist

# import from the project
from store.models import Product
from .models import Cart,CartItem
from store.models import Variation

# obtains the cart id = session_key
def _cart_id(request):
	cart = request.session.session_key
	if not cart:
		cart = request.session.create()
	return cart


# add item in the cart
def add_cart(request,product_id):
	# get the product using the product_id
	product = Product.objects.get(id = product_id)

	product_variation = []
	# recieve the variation details of the product from the POST Request.
	if request.method == "POST":
		for item in request.POST:
			key = item
			value = request.POST[key]
			try:
				variation = Variation.objects.get(product = product,variation_category__iexact=key, variation_value__iexact = value)
				product_variation.append(variation)
			except:
				pass
	print(product_variation)
	# cart
	try:
		# get the cart_id present in the session
		cart = Cart.objects.get(cart_id = _cart_id(request))
	except Cart.DoesNotExist:
		cart = Cart.objects.create(
			cart_id = _cart_id(request)
		)
	cart.save()

	# first, check if the item we are looking for exists in the cart or not
	is_cart_item_exists = CartItem.objects.filter(product = product, cart = cart).exists()
	if is_cart_item_exists:
		cart_item = CartItem.objects.filter(product = product,cart = cart)
		# so, what are we doing here ?

		#we are trying to match the existing_variations from database with the curret_variations

		#IN case, it matches we will increament the product quantity or else create a new cart item
		ex_var_list = []
		id = []
		for item in cart_item:
			existing_variations = item.variations.all()
			ex_var_list.append(list(existing_variations))
			id.append(item.id)

		print(ex_var_list)


		# for debugging
		# print("pv", product_variation)
		# print("evl", ex_var_list)

		# checks if the selected variation is in the cart
		if product_variation in ex_var_list:
			# print("true")
			index = ex_var_list.index(product_variation)
			item_id = id[index]
			item = CartItem.objects.get(product = product,id = item_id)
			item.quantity +=1
			item.save()

		# adds a new item
		else:
			# print("false")
			item = CartItem.objects.create(product = product,quantity = 1,cart = cart)
			if len(product_variation) > 0:
				item.variations.clear()
				item.variations.add(*product_variation)
			item.save()

	else:
		cart_item = CartItem.objects.create(
			product = product,
			quantity = 1,
			cart = cart,
		)

		if len(product_variation) > 0:
			cart_item.variations.clear()
			cart_item.variations.add(*product_variation)
		cart_item.save()

	# return HttpResponse(cart_item.product.product_name)
	return redirect('cart')

# remove/decreament the product quantity
def remove_cart(request,product_id,cart_item_id):
	cart = Cart.objects.get(cart_id = _cart_id(request))
	product = get_object_or_404(Product,id = product_id)
	try:
		cart_item = CartItem.objects.get(product=product,cart = cart,id = cart_item_id)
		if cart_item.quantity > 1:
			cart_item.quantity -=1
			cart_item.save()
		else:
			cart_item.delete()
	except:
		pass
	return redirect('cart')

def remove_cart_item(request,product_id,cart_item_id):
	cart = Cart.objects.get(cart_id = _cart_id(request))
	product = get_object_or_404(Product,id = product_id)
	cart_item = CartItem.objects.get(product=product,cart = cart,id = cart_item_id)
	cart_item.delete()
	return redirect('cart')

# Info to be displayed in the cart page
def cart(request,total=0,quantity = 0,cart_items = None):
	try:
		tax = 0
		grand_total = 0
		cart = Cart.objects.get(cart_id = _cart_id(request))
		cart_items = CartItem.objects.filter(cart = cart,is_active = True)
		for cart_item in cart_items:
			total += cart_item.product.price*cart_item.quantity
			quantity +=cart_item.quantity

		# calculate the tax and grand total
		tax = (18*total) /100
		grand_total = total + tax

	except cart.ObjectDoesNotExist:
		pass

	context = {
		'total':total,
		'quantity':quantity,
		'cart_items':cart_items,
		'tax':round(tax),
		'grand_total': round(grand_total),
	}

	return render(request,'store/cart.html',context)