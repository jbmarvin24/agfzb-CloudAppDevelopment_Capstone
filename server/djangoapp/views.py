from django.shortcuts import render
from django.http import HttpResponseRedirect, HttpResponse
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse
from .models import CarMake, CarModel
# from .restapis import related methods
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from datetime import datetime
import logging
import json
import dateutil.parser as dateParser

from .restapis import get_dealer_from_cf, get_dealer_reviews_from_cf, get_dealers_from_cf, post_request

# Get an instance of a logger
logger = logging.getLogger(__name__)


# Create your views here.


# Create an `about` view to render a static about page
def about(request):
    context = {}
    if request.method == "GET":
        return render(request, 'djangoapp/about.html', context)


# Create a `contact` view to return a static contact page
def contact(request):
    context = {}
    if request.method == "GET":
        return render(request, 'djangoapp/contact_us.html', context)

# Create a `login_request` view to handle sign in request
def login_request(request):
    context = {}
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['psw']
        user = authenticate(username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('djangoapp:index')
        else:
            context['message'] = "Invalid username or password."
            return render(request, 'djangoapp/user_login_bootstrap.html', context)
    else:
        return render(request, 'djangoapp/user_login_bootstrap.html', context)

# Create a `logout_request` view to handle sign out request
def logout_request(request):
    logout(request)
    return redirect('djangoapp:index')

# Create a `registration_request` view to handle sign up request
def registration_request(request):
    context = {}
    if request.method == 'GET':
        return render(request, 'djangoapp/registration.html', context)
    elif request.method == 'POST':
        # Check if user exists
        username = request.POST['username']
        password = request.POST['psw']
        first_name = request.POST['firstname']
        last_name = request.POST['lastname']
        user_exist = False
        try:
            User.objects.get(username=username)
            user_exist = True
        except:
            logger.error("New user")
        if not user_exist:
            user = User.objects.create_user(username=username, first_name=first_name, last_name=last_name,
                                            password=password)
            login(request, user)
            return redirect("djangoapp:index")
        else:
            context['message'] = "User already exists."
            return render(request, 'djangoapp/registration.html', context)


# Update the `get_dealerships` view to render the index page with a list of dealerships
def get_dealerships(request):
    context = {}
    if request.method == "GET":
        url = "https://us-south.functions.appdomain.cloud/api/v1/web/b3a18e7c-ebeb-4141-93d1-c859b10e80aa/dealership-package/get-dealership"
        # Get dealers from the URL
        dealerships = get_dealers_from_cf(url)
        context["dealerships"] = dealerships
        return render(request, 'djangoapp/index.html', context)


# Create a `get_dealer_details` view to render the reviews of a dealer
def get_dealer_details(request, dealer_id):
    context = {}
    if request.method == "GET":
        url = "https://us-south.functions.appdomain.cloud/api/v1/web/b3a18e7c-ebeb-4141-93d1-c859b10e80aa/dealership-package/review"
        # Get dealers from the URL
        reviews = get_dealer_reviews_from_cf(url, dealerId=dealer_id)

        dealer_name = get_dealer(dealer_id)

        context["review_list"] = reviews
        context["dealer_name"] = dealer_name
        context["dealer_id"] = dealer_id
        return render(request, 'djangoapp/dealer_details.html', context)


# Create a `add_review` view to submit a review
def add_review(request, dealer_id):
    if request.user.is_authenticated:
        context = {}
        print(request)
        if request.method == "GET":
            cars = CarModel.objects.all()
            dealer_name = get_dealer(dealer_id)
            context["cars"] = cars
            context["dealer_id"] = dealer_id
            context["dealer_name"] = dealer_name
            return render(request, 'djangoapp/add_review.html', context)
        elif request.method == "POST":
            # print(request.POST)
            formDto = request.POST
            user = request.user

            review = {}
            review["time"] = datetime.utcnow().isoformat()
            review["name"] = user.first_name + " " + user.last_name
            review["dealership"] = dealer_id
            review["review"] = formDto["content"]
            review["purchase"] = True if "purchasecheck" in formDto and formDto["purchasecheck"] == "on" else False

            purchase_date = formDto["purchasedate"]
            if purchase_date is not None and purchase_date != "":
                review["purchase_date"]  = dateParser.parse(purchase_date).isoformat()

            # Get the Car
            car_id_dto = formDto["car"]
            if car_id_dto != "":
                car = CarModel.objects.get(id=car_id_dto)
                review["car_make"] = car.make.name
                review["car_model"] = car.name
                review["car_year"]  = car.year.strftime("%Y")

            # print(review)

            json_payload = {}
            json_payload["review"] = review

            post_request(url="https://us-south.functions.appdomain.cloud/api/v1/web/b3a18e7c-ebeb-4141-93d1-c859b10e80aa/dealership-package/review"
                     , json_payload=json_payload)
            
            # return render(request, 'djangoapp/add_review.html', context)
            return redirect("djangoapp:dealer_details", dealer_id=dealer_id)


            
def get_dealer(id):
    return get_dealer_from_cf("https://us-south.functions.appdomain.cloud/api/v1/web/b3a18e7c-ebeb-4141-93d1-c859b10e80aa/dealership-package/get-dealership", id=id)
        


