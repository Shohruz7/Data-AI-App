from django.urls import path
from . import views

urlpatterns = [
    path('upload/', views.upload_dataset, name='upload'),
    path('home/', views.home, name='analysis-home'),
    # path('preview/', views.preview_dataset, name='preview'),
]
