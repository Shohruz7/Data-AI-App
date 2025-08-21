from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from .models import DataSet
from .forms import DataSetForm
from .utils import generate_response, answer_question, generate_chat_title

import matplotlib
matplotlib.use('Agg')  # Use a non-interactive backend for matplotlib
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO
import base64
import json
from datetime import datetime
from copy import deepcopy


def _ensure_chats_initialized(session):
    # Migrate old single chat_history if present
    if 'chats' not in session:
        session['chats'] = []
    if 'active_chat_id' not in session:
        session['active_chat_id'] = None
    if session.get('active_chat_id') is None:
        # If legacy chat_history exists, migrate it into the first chat
        legacy_history = session.get('chat_history', [])
        legacy_file = session.get('last_uploaded_file')
        first_chat = {
            'id': 1,
            'title': 'Chat 1',
            'messages': legacy_history if legacy_history else [],
            'last_uploaded_file': legacy_file if legacy_file else None,
            'saved': False,
        }
        session['chats'] = [first_chat]
        session['active_chat_id'] = 1
        # Clean legacy keys to avoid confusion
        if 'chat_history' in session:
            del session['chat_history']
        if 'last_uploaded_file' in session:
            del session['last_uploaded_file']


def _get_active_chat(session):
    active_id = session.get('active_chat_id')
    for chat in session.get('chats', []):
        if chat['id'] == active_id:
            return chat
    return None


def _save_chat(session, updated_chat):
    chats = session.get('chats', [])
    for idx, chat in enumerate(chats):
        if chat['id'] == updated_chat['id']:
            chats[idx] = updated_chat
            session['chats'] = chats
            return


def _delete_chat(session, chat_id: int):
    chats = session.get('chats', [])
    chats = [c for c in chats if c['id'] != chat_id]
    session['chats'] = chats
    # Reset active chat if needed
    if session.get('active_chat_id') == chat_id:
        if chats:
            session['active_chat_id'] = chats[-1]['id']
        else:
            # create a new empty chat to keep UI functional
            new_id = 1
            new_chat = {'id': new_id, 'title': 'Chat 1', 'messages': [], 'last_uploaded_file': None, 'saved': False}
            session['chats'] = [new_chat]
            session['active_chat_id'] = new_id


@login_required
def home(request):
    _ensure_chats_initialized(request.session)

    # Prepare defaults
    gpt_response = None
    chart = None
    question_answer = None
    form = DataSetForm()

    if request.method == 'POST':
        form_type = request.POST.get('form_type')
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

        # Handle new chat creation (only if current active chat has at least one message)
        if form_type == 'new_chat':
            active_chat = _get_active_chat(request.session)
            if not active_chat or len(active_chat.get('messages', [])) == 0:
                if is_ajax:
                    return JsonResponse({'success': False, 'error': 'Finish your current chat (upload a dataset or ask a question) before starting a new one.'})
            chats = request.session.get('chats', [])
            new_id = (max([c['id'] for c in chats]) + 1) if chats else 1
            new_chat = {
                'id': new_id,
                'title': f'Chat {new_id}',
                'messages': [],
                'last_uploaded_file': None,
                'saved': False,
            }
            chats.append(new_chat)
            request.session['chats'] = chats
            request.session['active_chat_id'] = new_id
            if is_ajax:
                return JsonResponse({
                    'success': True,
                    'active_chat_id': new_id,
                    'chats': [{'id': c['id'], 'title': c['title'], 'saved': c.get('saved', False)} for c in chats],
                    'messages': []
                })

        # Handle chat switching
        if form_type == 'switch_chat':
            try:
                chat_id = int(request.POST.get('chat_id'))
            except (TypeError, ValueError):
                chat_id = None
            chats = request.session.get('chats', [])
            found = any(c['id'] == chat_id for c in chats)
            if found:
                request.session['active_chat_id'] = chat_id
                active = next(c for c in chats if c['id'] == chat_id)
                if is_ajax:
                    return JsonResponse({
                        'success': True,
                        'active_chat_id': chat_id,
                        'messages': active['messages']
                    })
            else:
                if is_ajax:
                    return JsonResponse({'success': False, 'error': 'Chat not found'})

        # Save chat
        if form_type == 'save_chat':
            try:
                chat_id = int(request.POST.get('chat_id'))
            except (TypeError, ValueError):
                chat_id = None
            chats = request.session.get('chats', [])
            target = next((c for c in chats if c['id'] == chat_id), None)
            if not target:
                if is_ajax:
                    return JsonResponse({'success': False, 'error': 'Chat not found'})
            else:
                target['saved'] = True
                _save_chat(request.session, target)
                if is_ajax:
                    return JsonResponse({
                        'success': True,
                        'chats': [{'id': c['id'], 'title': c['title'], 'saved': c.get('saved', False)} for c in request.session.get('chats', [])]
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
            _delete_chat(request.session, chat_id)
            chats = request.session.get('chats', [])
            active = _get_active_chat(request.session)
            if is_ajax:
                return JsonResponse({
                    'success': True,
                    'chats': [{'id': c['id'], 'title': c['title'], 'saved': c.get('saved', False)} for c in chats],
                    'active_chat_id': active['id'] if active else None,
                    'messages': active['messages'] if active else []
                })

        # Upload handler (operate on active chat)
        if form_type == 'upload':
            active_chat = _get_active_chat(request.session)
            form = DataSetForm(request.POST, request.FILES)
            if form.is_valid() and active_chat is not None:
                try:
                    dataset = form.save(commit=False)
                    dataset.user = request.user
                    # Set dataset name from filename (without path)
                    try:
                        dataset.name = dataset.file.name.split('/')[-1]
                    except Exception:
                        pass
                    dataset.save()

                    df = pd.read_csv(dataset.file.path)
                    active_chat['last_uploaded_file'] = dataset.file.path
                    gpt_response = generate_response(df)

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

                    active_chat['messages'].append({
                        'type': 'analysis',
                        'content': gpt_response,
                        'chart': chart if chart else None,
                    })

                    # Generate AI title for chat based on file and preview
                    try:
                        ai_title = generate_chat_title(df, dataset.file.name or dataset.name)
                        if ai_title:
                            active_chat['title'] = ai_title
                    except Exception:
                        # Fallback to dataset name if AI title fails
                        try:
                            active_chat['title'] = dataset.name or active_chat['title']
                        except Exception:
                            pass

                    _save_chat(request.session, active_chat)

                    if is_ajax:
                        # Return updated chats for sidebar so title updates
                        chats_min = [{'id': c['id'], 'title': c['title'], 'saved': c.get('saved', False)} for c in request.session.get('chats', [])]
                        return JsonResponse({
                            'success': True,
                            'gpt_response': gpt_response,
                            'chart': chart,
                            'active_chat_id': active_chat['id'],
                            'chats': chats_min,
                        })
                except Exception as e:
                    if is_ajax:
                        return JsonResponse({'success': False, 'error': str(e)})

        # Question handler (operate on active chat)
        if form_type == 'question':
            active_chat = _get_active_chat(request.session)
            question = request.POST.get('question')
            if active_chat and active_chat.get('last_uploaded_file'):
                try:
                    df = pd.read_csv(active_chat['last_uploaded_file'])
                    question_answer = answer_question(question, df)
                    active_chat['messages'].append({
                        'type': 'question',
                        'content': question,
                        'response': question_answer
                    })
                    _save_chat(request.session, active_chat)

                    if is_ajax:
                        return JsonResponse({
                            'success': True,
                            'question_answer': question_answer,
                            'active_chat_id': active_chat['id']
                        })
                except Exception as e:
                    if is_ajax:
                        return JsonResponse({'success': False, 'error': str(e)})
            else:
                if is_ajax:
                    return JsonResponse({'success': False, 'error': 'No dataset uploaded to answer the question.'})
                question_answer = "No dataset uploaded to answer the question."

    # Render template for GET (or non-AJAX fallbacks)
    active_chat = _get_active_chat(request.session)
    chats_min = [{'id': c['id'], 'title': c['title'], 'saved': c.get('saved', False)} for c in request.session.get('chats', [])]
    chat_history = active_chat['messages'] if active_chat else []

    return render(request, 'analysis/home.html', {
        'form': form,
        'gpt_response': gpt_response,
        'chart': chart,
        'question_answer': question_answer,
        'chat_history': chat_history,
        'chats': chats_min,
        'active_chat_id': active_chat['id'] if active_chat else None,
    })
