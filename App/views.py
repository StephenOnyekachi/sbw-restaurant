

from django.contrib.auth.models import User
from django.http import HttpResponse,JsonResponse
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404, get_list_or_404
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required, user_passes_test
from django.urls import reverse
from django.db.models import Q, F, Sum
import random, time, datetime, requests
from decimal import Decimal, InvalidOperation
from django.contrib.auth.hashers import make_password, check_password
from django.db import transaction
from . models import *
import re
from django.conf import settings
from django.core.cache import cache

# for emails
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
import threading
from celery import shared_task

# Create your views here.

# deffine speruser function
def IsSuperuser(user):
    return user.is_superuser


# redirect user if not superuser
def CheckUser(view_func):
    return user_passes_test(
        IsSuperuser,
        login_url='dashboard',
        redirect_field_name=None
    )(view_func)


# celery task for sending email asynchronously
@shared_task(bind=True, max_retries=3)
def SendEmailTask(self, subject, html, email):
    import logging
    logger = logging.getLogger(__name__)

    try:
        logger.info(f"Sending email to {email}")

        from django.core.mail import EmailMultiAlternatives

        msg = EmailMultiAlternatives(
            subject=subject,
            body="This email requires HTML support.",
            to=[email]
        )
        msg.attach_alternative(html, "text/html")
        msg.send()

    except Exception as exc:
        logger.error(f"Failed to send email to {email}: {exc}")
        raise self.retry(exc=exc, countdown=60)


# for sending function
def SendMail(user, template_name, email_subject, extra_context=None):
    name = user.get_full_name() or user.username
    recipient_email = user.email

    context = {
        "name": name,
        "email": recipient_email,
    }

    if extra_context:
        context.update(extra_context)

    html_content = render_to_string(template_name, context)

    def send_mail():
        try:
            msg = EmailMultiAlternatives(
                subject=email_subject,
                body=html_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[recipient_email],
            )

            msg.attach_alternative(html_content, "text/html")

            result = msg.send(fail_silently=False)

            print("EMAIL SENT:", result)

        except Exception as e:
            print("EMAIL ERROR:", str(e))

    threading.Thread(
        target=send_mail
    ).start()


# logout user out after 24 hours
def AutoLogout(request, timeout_day = 1):
    # timeout_minues = timeout_hour * 60 # for 12 hour
    timeout_minues = timeout_day * 24 * 60 # for 24 hour
    now = datetime.datetime.now()
    try:
        last_activity = request.session['last_activity']
        last_activity = datetime.datetime.fromisoformat(last_activity)
        if(now - last_activity).total_seconds() / 60 > timeout_minues:
            logout(request)
    except KeyError:
        pass
    # request.session['last_active']=datetime.datetime.now()
    request.session['last_activity'] = now.isoformat()


# logout function
def UserLogout(request):
    user = request.user

    # logout user once
    logout(request)
    messages.success(
        request,
        "You have been logged out successfully"
    )

    return redirect("index")


# login function
def UserLogin(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:

            login(request, user)

            if user.is_superuser:
                messages.success(request, f"Welcome back {user.username}")
                return redirect('dashboard')

            messages.success(request, f"Welcome back {user.username}")
            return redirect('dashboard')
        
        messages.error(request, 'Incorrect username or password, please try again')
        return redirect('login')
    
    context={}

    return render(request,"login.html",context)
    # return HttpResponse('welcome to django')


# user signup
def Signup(request):
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        email = request.POST.get("email", "").strip().lower()
        password = request.POST.get("password")

        # verifing password
        if password:
            
            # # checking if email already exist
            # if User.objects.filter(email=email).exists():
            #     messages.error(request, 'Email have been used, try another email')
            #     return redirect("signup")
            
            # checking if username already exist
            if User.objects.filter(username=username).exists():
                messages.error(request, "Username already exists")
                return redirect("signup")
                
            # to prevent error occurance while creating account
            with transaction.atomic():
                
                # creating user
                profile = User.objects.create_user(
                    username=username,
                    email=email,
                    password=password,
                )
                
            # calling sending mail functionn here after creating account
            try:
                subject = 'Welcome to 🍽️ SBW Maison'
                extra_context = {
                    'user': profile
                }
                SendMail(profile, 'mails/welcomeMail.html', subject, extra_context)
            except Exception as e:
                print("EMAIL ERROR:", e)

            messages.success(
                request, f'you successfully created an with 🍽️ SBW Maison"{username}"'
            )
            return redirect("login")

        return redirect("signup")
    
    return render(request,"signup.html")


# for inex or landing page
def Index(request):

    context = {
        
    }
    return render(request, 'index.html', context)
    # return HttpResponse('welcome to django')


# for order page
def Order(request, pk):

    food = get_object_or_404(Food, id=pk)

    context = {
        'food':food,
    }
    return render(request, 'order.html', context)
    # return HttpResponse('welcome to django')


# for food menu
def Samples(request):

    # importing choices
    category = Food.CATEGORY_CHOICES

    # for filtered food
    filterFood = ''

    if request.method == 'POST':

        # searching for food(filtering)
        query = request.POST.get('query','')
        filterFood = Food.objects.filter(
            Q(name__icontains=query) |
            Q(amount__icontains=query) |
            Q(description__icontains=query) |
            Q(category__icontains=query)
        )

    # foods = Food.objects.filter(category=category)
    allfood = Food.objects.all()

    context = {
        'allfood':allfood,
        'filterFood':filterFood,
    }
    return render(request, 'samples.html', context)
    # return HttpResponse('welcome to django')


# for user or admin dashboard
@login_required(login_url='login')
@CheckUser
def Dashboard(request):

    # get all foods
    foods = Food.objects.all()

    context = {
        'foods':foods,
    }

    return render(request, 'admin/adminpage.html', context)


# for adding samples
@login_required(login_url='login')
@CheckUser
def AddFood(request):

    # importing choices
    category = Food.CATEGORY_CHOICES
    status = Food.STATUS_CHOICES

    # # get user
    if request.method == "POST":
        image = request.FILES.get('image')
        name = request.POST.get('title')
        amount = request.POST.get('price')
        description = request.POST.get('description')
        number = request.POST.get('number')

        status = request.POST.get('status')
        category = request.POST.get('category')

        # to prevent error occurance while creating account
        with transaction.atomic():

            if number:
                number = re.sub(r'\D', '', number)
                if number.startswith('0'):
                    number = number[1:]

            Food.objects.create(
                user=request.user,
                image=image,
                name=name,
                amount=amount,
                description=description,
                status=status,
                category=category,
                number=number,
            )

            messages.success(request, f"{name}, was added successfully")
            return redirect('dashboard')

    context = {
        'status':status,
        'category':category,
    }

    return render(request, 'admin/addsample.html', context)


# for adding samples
@login_required(login_url='login')
@CheckUser
def EditFood(request, pk):

    food = get_object_or_404(Food, id=pk)

    # importing choices
    category = Food.CATEGORY_CHOICES
    status = Food.STATUS_CHOICES

    # # get user
    if request.method == "POST":
        image = request.FILES.get('image')
        name = request.POST.get('title')
        amount = request.POST.get('price')
        description = request.POST.get('description')

        status = request.POST.get('status')
        category = request.POST.get('category')

        # to prevent error occurance while creating account
        with transaction.atomic():

            if image:
                food.image=image
            if name:
                food.name=name
            if amount:
                food.amount=amount
            if description:
                food.description=description
            if status:
                food.status=status
            if category:
                food.category=category

            food.save()
            messages.success(request, f"{name}, was edited successfully")
            return redirect('dashboard')

    context = {
        'food':food,
        'status':status,
        'category':category,
    }

    return render(request, 'admin/edit.html', context)


# for deleting samples
@login_required(login_url='login')
@CheckUser
def DeleteFood(request, pk):

    food = get_object_or_404(Food, id=pk)
    food.delete()
    messages.success(request, f"{food.name}, was deleted successfully")
    return redirect('dashboard')


# for viewing staff
@login_required(login_url='login')
@CheckUser
def Staffs(request):

    # get all foods
    users = User.objects.all()

    context = {
        'users':users,
    }

    return render(request, 'admin/users.html', context)


# for deleting staff
@login_required(login_url='login')
@CheckUser
def DeleteStaff(request, pk):

    staff = get_object_or_404(User, id=pk)
    staff.delete()
    messages.success(request, f"{staff.username}, was deleted successfully")
    return redirect('staffs')


# for adding new staff
@login_required(login_url='login')
@CheckUser
def AddStaff(request):

    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        email = request.POST.get("email", "").strip().lower()
        password = request.POST.get("password")

        # verifing password
        if password:
            
            # checking if username already exist
            if User.objects.filter(username=username).exists():
                messages.error(request, "Username already exists")
                return redirect("signup")
                
            # to prevent error occurance while creating account
            with transaction.atomic():
                
                # creating user
                profile = User.objects.create_user(
                    username=username,
                    email=email,
                    password=password,
                )
                
            # calling sending mail functionn here after creating account
            try:
                subject = 'Welcome to 🍽️ SBW Maison'
                extra_context = {
                    'user': profile
                }
                SendMail(profile, 'mails/welcomeMail.html', subject, extra_context)
            except Exception as e:
                print("EMAIL ERROR:", e)

            messages.success(
                request, f'you successfully created an account for {username} as a staff of 🍽️ SBW Maison'
            )
            return redirect("staffs")
        
    context = {}

    return render(request, 'admin/addstaff.html', context)
