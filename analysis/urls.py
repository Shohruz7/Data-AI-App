from django.urls import path
from . import views

urlpatterns = [
    path('home/', views.home, name='analysis-home'),
    # path('preview/', views.preview_dataset, name='preview'),
]
