from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser
from .models import DataSet

class DataSetForm(forms.ModelForm):
    class Meta:
        model = DataSet
        fields = ['name', 'file']