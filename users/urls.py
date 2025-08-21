from django.urls import path
from django.contrib.auth import views as auth_views
from django.views.decorators.cache import never_cache
from django.contrib.auth.views import LoginView
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path(
        'login/',
        never_cache(LoginView.as_view(
            template_name='users/login.html',
            redirect_authenticated_user=True
        )),
        name='login',
    ),
    path('logout/', views.logout_view, name='logout'),
    path('account/', views.account, name='account'),
    path('demo/', views.demo, name='demo'),
    path('contact/', views.contact, name='contact'),
]