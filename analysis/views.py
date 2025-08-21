from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.contrib import messages

from .models import DataSet, Chat, ChatMessage
from .forms import DataSetForm
from .utils import generate_response, answer_question, generate_chat_title, infer_chart_spec

import matplotlib
matplotlib.use('Agg')  # Use a non-interactive backend for matplotlib
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO
import base64
import json
from datetime import datetime
from copy import deepcopy
import logging

logger = logging.getLogger(__name__)


def _maybe_migrate_session_chats(request):
    # If legacy session-based chats exist, migrate them to DB and clear session
    session = request.session
    if 'chats' not in session:
        return
    chats = session.get('chats') or []
    active_id = session.get('active_chat_id')
    new_active_id = None
    for c in chats:
        chat = Chat.objects.create(user=request.user, title=c.get('title') or 'Chat')
        if c.get('saved'):
            chat.saved = True
            chat.save(update_fields=['saved'])
        # Messages
        for m in c.get('messages', []):
            ChatMessage.objects.create(
                chat=chat,
                type=m.get('type') or 'analysis',
                content=m.get('content') or '',
                response=m.get('response') or None,
                chart=m.get('chart') or None,
            )
        if c.get('id') == active_id:
            new_active_id = chat.id
    # Cleanup session keys
    if 'chats' in session:
        del session['chats']
    if 'chat_history' in session:
        del session['chat_history']
    if 'last_uploaded_file' in session:
        del session['last_uploaded_file']
    session['active_chat_id'] = new_active_id


def _ensure_active_chat_initialized(request):
    if request.session.get('active_chat_id'):
        return
    existing = Chat.objects.filter(user=request.user).order_by('-updated_at').first()
    if existing:
        request.session['active_chat_id'] = existing.id
    else:
        first = Chat.objects.create(user=request.user, title='Chat 1')
        request.session['active_chat_id'] = first.id


def _get_active_chat(request):
    active_id = request.session.get('active_chat_id')
    if not active_id:
        return None
    try:
        return Chat.objects.get(id=active_id, user=request.user)
    except Chat.DoesNotExist:
        latest = Chat.objects.filter(user=request.user).order_by('-updated_at').first()
        if latest:
            request.session['active_chat_id'] = latest.id
            return latest
        return None


def _serialize_chats(user):
    return [
        {'id': c.id, 'title': c.title, 'saved': c.saved}
        for c in Chat.objects.filter(user=user).order_by('created_at')
    ]


def _delete_chat(request, chat_id: int):
    try:
        chat = Chat.objects.get(id=chat_id, user=request.user)
        chat.delete()
    except Chat.DoesNotExist:
        return
    remaining = Chat.objects.filter(user=request.user).order_by('created_at')
    if remaining.exists():
        request.session['active_chat_id'] = remaining.last().id
    else:
        new_chat = Chat.objects.create(user=request.user, title='Chat 1')
        request.session['active_chat_id'] = new_chat.id


@login_required
def home(request):
    _maybe_migrate_session_chats(request)
    _ensure_active_chat_initialized(request)

    # Prepare defaults
    gpt_response = None
    chart = None
    question_answer = None
    form = DataSetForm()

    if request.method == 'POST':
        form = DataSetForm(request.POST, request.FILES)
        form_type = request.POST.get('form_type')
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

        # Handle new chat creation (only if current active chat has at least one message)
        if form_type == 'new_chat':
            active_chat = _get_active_chat(request)
            if not active_chat or not active_chat.messages.exists():
                if is_ajax:
                    return JsonResponse({'success': False, 'error': 'Finish your current chat (upload a dataset or ask a question) before starting a new one.'})
            count = Chat.objects.filter(user=request.user).count()
            new_chat = Chat.objects.create(user=request.user, title=f'Chat {count + 1}')
            request.session['active_chat_id'] = new_chat.id
            if is_ajax:
                return JsonResponse({
                    'success': True,
                    'active_chat_id': new_chat.id,
                    'chats': _serialize_chats(request.user),
                    'messages': []
                })

        # Handle chat switching
        if form_type == 'switch_chat':
            try:
                chat_id = int(request.POST.get('chat_id'))
            except (TypeError, ValueError):
                chat_id = None
            try:
                active = Chat.objects.get(id=chat_id, user=request.user)
                request.session['active_chat_id'] = active.id
                if is_ajax:
                    return JsonResponse({
                        'success': True,
                        'active_chat_id': active.id,
                        'messages': [
                            {
                                'type': m.type,
                                'content': m.content,
                                'response': m.response,
                                'chart': m.chart,
                            }
                            for m in active.messages.all()
                        ]
                    })
            except Chat.DoesNotExist:
                if is_ajax:
                    return JsonResponse({'success': False, 'error': 'Chat not found'})

        # Save chat
        if form_type == 'save_chat':
            try:
                chat_id = int(request.POST.get('chat_id'))
            except (TypeError, ValueError):
                chat_id = None
            try:
                target = Chat.objects.get(id=chat_id, user=request.user)
            except Chat.DoesNotExist:
                if is_ajax:
                    return JsonResponse({'success': False, 'error': 'Chat not found'})
            else:
                target.saved = True
                target.save(update_fields=['saved'])
                if is_ajax:
                    return JsonResponse({
                        'success': True,
                        'chats': _serialize_chats(request.user)
                    })

        # Delete chat
        if form_type == 'delete_chat':
            try:
                chat_id = int(request.POST.get('chat_id'))
            except (TypeError, ValueError):
                chat_id = None
            if chat_id is None:
                if is_ajax:
                    return JsonResponse({'success': False, 'error': 'Invalid chat id'})
            _delete_chat(request, chat_id)
            active = _get_active_chat(request)
            if is_ajax:
                return JsonResponse({
                    'success': True,
                    'chats': _serialize_chats(request.user),
                    'active_chat_id': active.id if active else None,
                    'messages': [
                        {
                            'type': m.type,
                            'content': m.content,
                            'response': m.response,
                            'chart': m.chart,
                        }
                        for m in (active.messages.all() if active else [])
                    ]
                })

        # Upload handler (operate on active chat)
        if form_type == 'upload':
            active_chat = _get_active_chat(request)
            if form.is_valid() and active_chat is not None:
                try:
                    # Comprehensive CSV validation
                    uploaded_file = request.FILES['file']
                    
                    # Check file extension
                    if not uploaded_file.name.lower().endswith('.csv'):
                        if is_ajax:
                            return JsonResponse({
                                'success': False,
                                'error': 'Please upload a valid CSV file. Only .csv files are allowed.'
                            })
                        messages.error(request, 'Please upload a valid CSV file. Only .csv files are allowed.')
                        return redirect('home')
                    
                    # Check file size (limit to 10MB)
                    if uploaded_file.size > 10 * 1024 * 1024:
                        if is_ajax:
                            return JsonResponse({
                                'success': False,
                                'error': 'File size must be less than 10MB. Your file is {:.1f}MB.'.format(uploaded_file.size / (1024 * 1024))
                            })
                        messages.error(request, f'File size must be less than 10MB. Your file is {uploaded_file.size / (1024 * 1024):.1f}MB.')
                        return redirect('home')
                    
                    # Check if file is empty
                    if uploaded_file.size == 0:
                        if is_ajax:
                            return JsonResponse({
                                'success': False,
                                'error': 'The uploaded file is empty. Please upload a file with data.'
                            })
                        messages.error(request, 'The uploaded file is empty. Please upload a file with data.')
                        return redirect('home')
                    
                    # Try to read CSV to validate content
                    try:
                        df = pd.read_csv(uploaded_file)
                        if df.empty:
                            if is_ajax:
                                return JsonResponse({
                                    'success': False,
                                    'error': 'CSV file appears to be empty or contains no data rows.'
                                })
                            messages.error(request, 'CSV file appears to be empty or contains no data rows.')
                            return redirect('home')
                        
                        # Check if dataframe has reasonable dimensions
                        if df.shape[0] > 100000:
                            if is_ajax:
                                return JsonResponse({
                                    'success': False,
                                    'error': 'CSV file has too many rows ({:,}). Please upload a file with fewer than 100,000 rows.'.format(df.shape[0])
                                })
                            messages.error(request, f'CSV file has too many rows ({df.shape[0]:,}). Please upload a file with fewer than 100,000 rows.')
                            return redirect('home')
                            
                        if df.shape[1] > 100:
                            if is_ajax:
                                return JsonResponse({
                                    'success': False,
                                    'error': 'CSV file has too many columns ({:,}). Please upload a file with fewer than 100 columns.'.format(df.shape[1])
                                })
                            messages.error(request, f'CSV file has too many columns ({df.shape[1]:,}). Please upload a file with fewer than 100 columns.')
                            return redirect('home')
                        
                        # Check for required data types (at least some numeric columns)
                        numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
                        if len(numeric_cols) == 0:
                            if is_ajax:
                                return JsonResponse({
                                    'success': False,
                                    'error': 'CSV file must contain at least some numeric data for analysis. Please upload a file with numeric columns.'
                                })
                            messages.error(request, 'CSV file must contain at least some numeric data for analysis. Please upload a file with numeric columns.')
                            return redirect('home')
                            
                    except UnicodeDecodeError:
                        if is_ajax:
                            return JsonResponse({
                                'success': False,
                                'error': 'CSV file encoding error. Please ensure the file is saved with UTF-8 encoding.'
                            })
                        messages.error(request, 'CSV file encoding error. Please ensure the file is saved with UTF-8 encoding.')
                        return redirect('home')
                        
                    except Exception as e:
                        if is_ajax:
                            return JsonResponse({
                                'success': False,
                                'error': f'Error reading CSV file: {str(e)}. Please ensure the file is a valid CSV format.'
                            })
                        messages.error(request, f'Error reading CSV file: {str(e)}. Please ensure the file is a valid CSV format.')
                        return redirect('home')
                    
                    # Reset file pointer for processing
                    uploaded_file.seek(0)
                    
                    # Create dataset
                    dataset = form.save(commit=False)
                    dataset.user = request.user
                    # Set dataset name from filename (without path)
                    try:
                        dataset.name = dataset.file.name.split('/')[-1]
                    except Exception:
                        pass
                    dataset.save()
                    
                    # Analyze data
                    df = pd.read_csv(dataset.file.path)
                    active_chat.last_dataset = dataset
                    active_chat.save(update_fields=['last_dataset', 'updated_at'])
                    gpt_response = generate_response(df)

                    # Generate chart
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
                        plt.close()
                    else:
                        chart = None
                        
                    # Save analysis message
                    ChatMessage.objects.create(
                        chat=active_chat,
                        type='analysis',
                        content=gpt_response,
                        response=None,
                        chart=chart if chart else None,
                    )

                    # Generate AI title for chat based on file and preview
                    try:
                        ai_title = generate_chat_title(df, dataset.file.name or dataset.name)
                        if ai_title:
                            active_chat.title = ai_title
                    except Exception:
                        # Fallback to dataset name if AI title fails
                        try:
                            active_chat.title = dataset.name or active_chat.title
                        except Exception:
                            pass
                    active_chat.save(update_fields=['title', 'updated_at'])

                    if is_ajax:
                        # Return updated chats for sidebar so title updates
                        chats_min = _serialize_chats(request.user)
                        return JsonResponse({
                            'success': True,
                            'gpt_response': gpt_response,
                            'chart': chart,
                            'active_chat_id': active_chat.id,
                            'chats': chats_min,
                        })

                except Exception as e:
                    logger.error(f"Error processing upload: {str(e)}")
                    if is_ajax:
                        return JsonResponse({'success': False, 'error': str(e)})
                    messages.error(request, f'An error occurred while processing your file: {str(e)}')
                    return redirect('home')

        # Question handler (operate on active chat)
        if form_type == 'question':
            active_chat = _get_active_chat(request)
            question = request.POST.get('question')
            if active_chat and active_chat.last_dataset and active_chat.last_dataset.file:
                try:
                    df = pd.read_csv(active_chat.last_dataset.file.path)
                    question_answer = answer_question(question, df)
                    # Try to infer a chart from the question
                    chart_b64 = None
                    try:
                        spec = infer_chart_spec(question, df)
                        if spec and isinstance(spec, dict):
                            plt.figure(figsize=(10, 6))
                            chart_type = spec.get('type')
                            title = spec.get('title') or 'Chart'
                            hue = spec.get('hue')
                            if chart_type == 'hist':
                                col = spec.get('x') or spec.get('y')
                                bins = spec.get('bins') or 20
                                if col and col in df.columns:
                                    df[col].plot(kind='hist', bins=bins)
                                    plt.title(title)
                            elif chart_type == 'pie':
                                col = spec.get('x') or spec.get('y')
                                if col and col in df.columns:
                                    df[col].value_counts().plot(kind='pie', autopct='%1.1f%%')
                                    plt.title(title)
                            elif chart_type == 'box':
                                col = spec.get('y')
                                if col and col in df.columns:
                                    df[[col]].plot(kind='box')
                                    plt.title(title)
                            elif chart_type in ['bar', 'line', 'scatter']:
                                x = spec.get('x')
                                y = spec.get('y')
                                if x and y and x in df.columns and y in df.columns:
                                    data = df
                                    agg = spec.get('agg')
                                    if chart_type == 'bar' and agg in ['sum','mean','count']:
                                        if agg == 'sum':
                                            data = df.groupby(x)[y].sum().reset_index()
                                        elif agg == 'mean':
                                            data = df.groupby(x)[y].mean().reset_index()
                                        elif agg == 'count':
                                            data = df.groupby(x)[y].count().reset_index()
                                    if chart_type == 'bar':
                                        data.plot(kind='bar', x=x, y=y)
                                    elif chart_type == 'line':
                                        data.plot(kind='line', x=x, y=y)
                                    elif chart_type == 'scatter':
                                        data.plot(kind='scatter', x=x, y=y)
                                    plt.title(title)
                            buffer = BytesIO()
                            plt.savefig(buffer, format='png')
                            buffer.seek(0)
                            image_png = buffer.getvalue()
                            buffer.close()
                            chart_b64 = base64.b64encode(image_png).decode('utf-8')
                            plt.close()
                    except Exception:
                        chart_b64 = None

                    ChatMessage.objects.create(
                        chat=active_chat,
                        type='question',
                        content=question,
                        response=question_answer,
                        chart=chart_b64,
                    )
                    active_chat.save(update_fields=['updated_at'])

                    if is_ajax:
                        return JsonResponse({
                            'success': True,
                            'question_answer': question_answer,
                            'chart': chart_b64,
                            'active_chat_id': active_chat.id
                        })
                except Exception as e:
                    if is_ajax:
                        return JsonResponse({'success': False, 'error': str(e)})
            else:
                if is_ajax:
                    return JsonResponse({'success': False, 'error': 'No dataset uploaded to answer the question.'})
                question_answer = "No dataset uploaded to answer the question."

    # Render template for GET (or non-AJAX fallbacks)
    active_chat = _get_active_chat(request)
    chats_min = _serialize_chats(request.user)
    chat_history = [
        {
            'type': m.type,
            'content': m.content,
            'response': m.response,
            'chart': m.chart,
        }
        for m in (active_chat.messages.all() if active_chat else [])
    ]

    return render(request, 'analysis/home.html', {
        'form': DataSetForm(),
        'gpt_response': gpt_response,
        'chart': chart,
        'question_answer': question_answer,
        'chat_history': chat_history,
        'chats': chats_min,
        'active_chat_id': active_chat.id if active_chat else None,
    })
