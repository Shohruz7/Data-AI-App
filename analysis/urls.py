from django.urls import path
from . import views

urlpatterns = [
    path('upload/', views.upload_dataset, name='upload'),
    # path('preview/', views.preview_dataset, name='preview'),
]
