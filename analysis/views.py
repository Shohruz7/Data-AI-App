from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required

from .models import DataSet
from .forms import DataSetForm
from.utils import generate_response, answer_question

import matplotlib
matplotlib.use('Agg')  # Use a non-interactive backend for matplotlib
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO
import base64

@login_required
def home(request):
    if 'chat_history' not in request.session:
        request.session['chat_history'] = []
    # Initialize variables
    chat_history = request.session['chat_history']
    gpt_response = None
    chart = None
    question_answer = None
    if request.method == 'POST':
        if 'dataset' in request.FILES:
            form = DataSetForm(request.POST, request.FILES)
            if form.is_valid():
                dataset = form.save(commit=False)
                dataset.user = request.user
                dataset.save()
                # Process the uploaded dataset file
                df = pd.read_csv(dataset.file.path)
                request.session['last_uploaded_file'] = dataset.file.path  # Store file path in session
                gpt_response = generate_response(df)
                # Generate chart from first numeric column
                numeric_cols = df.select_dtypes(include=['number']).columns
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
                    chat_history.append({
                        'type': 'analysis',
                        'content': gpt_response,
                    })
        elif 'question' in request.POST:
            question = request.POST.get('question')
            file_path = request.session.get('last_uploaded_file')
            if file_path:
                df = pd.read_csv(file_path)
                question_answer = answer_question(question, df)
                chat_history.append({
                        'type': 'question',
                        'content': question,
                        'response': question_answer
                })
            request.session['chat_history'] = chat_history # Save chat history to session
            if not file_path:
                question_answer = "No dataset uploaded to answer the question."
    else:
        form = DataSetForm()
    return render(request, 'analysis/home.html', {
        'form': DataSetForm(),
        'gpt_response': gpt_response,
        'chart': chart,
        'question_answer': question_answer
    })
