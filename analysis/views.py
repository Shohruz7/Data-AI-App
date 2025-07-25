from django.shortcuts import render, redirect
from .models import DataSet
from .forms import DataSetForm
import pandas as pd
from django.contrib.auth.decorators import login_required
@login_required
def upload_dataset(request):
    if request.method == 'POST':
        form = DataSetForm(request.POST, request.FILES)
        if form.is_valid():
            dataset = form.save(commit=False)
            dataset.user = request.user
            dataset.save()
            # Process the uploaded dataset file
            df = pd.read_csv(dataset.file.path)
            preview_data = df.head()  # Preview first few rows of the dataset
            return render(request, 'analysis/dataset_preview.html', {'dataset': dataset, 'preview_data': preview_data})
    else:
        form = DataSetForm()
    return render(request, 'analysis/upload.html', {'form': form})


# Create your views here.
