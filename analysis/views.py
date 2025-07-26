from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required

from .models import DataSet
from .forms import DataSetForm
from.utils import generate_response

import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO
import base64

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
            preview_dataset = df.head().to_string()

            gpt_response = generate_response(df)
            # Generate chart from first numeric column
            numeric_cols = df.select_dtypes(include=['number']).columns
            chart = None
            if len(numeric_cols) > 0:
                plt.figure(figsize=(10, 6))
                df[numeric_cols[0]].head(10).plot(kind='bar')
                plt.title(f"Sample of {numeric_cols[0]} Data")

                buffer = BytesIO()
                plt.savefig(buffer, format='png')
                buffer.seek(0)
                image_png = buffer.getvalue()
                buffer.close()
                chart = base64.b64encode(image_png).decode('utf-8')
            # Preview first few rows of the dataset
            return render(request, 'analysis/result.html', {
                            'dataset': dataset,
                            'gpt_response': gpt_response,
                            'chart': chart
                        })
    else:
        form = DataSetForm()
    return render(request, 'analysis/upload.html', {'form': form})
def home(request):
    return render(request, 'analysis/home.html')

# Create your views here.
