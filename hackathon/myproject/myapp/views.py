from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Claim


def index(request):
    # Just render the homepage with forms
    return render(request, 'pages/index.html')


def register_view(request):

    # note username = email.
    # title = user claim.
    # status this are the state it's in.
    # email = user email.
    # first_name = user full name.

    if request.method == "POST":
        full_name = request.POST.get("full_name")
        email = request.POST.get("email")
        password = request.POST.get("password")
        c_password = request.POST.get("c_password")

        if password != c_password:
            messages.error(request, "Passwords do not match.")
            print("Passwords do not match.")
            return redirect('index')

        if User.objects.filter(username=email).exists():
            messages.error(request, "User already exists.")
            print("User already exists.")
            return redirect('index')

        # Create user
        user = User.objects.create_user(
            username=email,
            email=email,
            password=password,
            first_name=full_name
        )
        # this is a dummy claim for db testing
        Claim.objects.create(
            user=user,
            title="Demo Claim",
            description="This is a demo claim created automatically.",
            claim_amount=0.0,
            status='pending',
            ai_risk_score=0.0
        )

        messages.success(request, "Account created successfully. You can now log in.")
        print("Account created successfully.")
        return redirect('index')
    else:
        return redirect('index')


def login_view(request):
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")

        user = authenticate(request, username=email, password=password)
        if user is not None:
            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, "Invalid email or password. or account does not exist.")
            print("Invalid email or password.")
            return redirect('index')
    else:
        return redirect('index')


@login_required(login_url='login')
def dashboard(request):
    claims = Claim.objects.filter(user=request.user)
    contex = {
        'claims': claims
        }
    return render(request, 'pages/dashboard.html',contex)


def logout_view(request):
    logout(request)
    return redirect('index')
