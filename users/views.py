from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.urls import reverse
from .forms import CustomUserCreationForm

def redirect_if_authenticated(view_func):
    """Custom decorator to redirect authenticated users to analysis home"""
    def wrapper(request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('analysis-home')
        return view_func(request, *args, **kwargs)
    return wrapper

@redirect_if_authenticated
def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect(reverse('analysis-home'))
    else:
        form = CustomUserCreationForm()
    return render(request, 'users/register.html', {'form': form})

@redirect_if_authenticated
def home(request):
    return render(request, 'base.html')

@redirect_if_authenticated
def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        # Automatically log in the user after registration
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect(reverse('analysis-home'))
        else:
            messages.error(request, "Invalid username or password")
    else:
        form = AuthenticationForm()
    return render(request, 'users/login.html', {'form': form})

def logout_view(request):
    """Custom logout view that redirects to welcome page"""
    logout(request)
    return redirect('home')

@login_required
def account(request):
    return render(request, 'users/account.html')

def demo(request):
    return render(request, 'demo.html')

def contact(request):
    return render(request, 'contact.html')    