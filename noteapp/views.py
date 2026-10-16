from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_http_methods, require_POST

from .forms import NoteForm, SignUpForm
from .models import Note


def note_list(request):
    if not request.user.is_authenticated:
        return render(request, 'noteapp/landing.html')

    notes = Note.objects.filter(owner=request.user)
    for note in notes:
        note.preview = next(
            (line.strip() for line in note.content.splitlines() if line.strip()),
            '',
        )
    return render(request, 'noteapp/note_list.html', {'notes': notes})


@login_required
def note_detail(request, pk):
    note = get_object_or_404(Note, pk=pk, owner=request.user)
    return render(request, 'noteapp/details.html', {'note': note})


@login_required
@require_http_methods(['GET', 'POST'])
def note_create(request):
    if request.method == 'POST':
        form = NoteForm(request.POST)
        if form.is_valid():
            note = form.save(commit=False)
            note.owner = request.user
            note.save()
            return redirect('note_list')
    else:
        form = NoteForm()

    return render(request, 'noteapp/note_form.html', {'form': form, 'is_edit': False})


@login_required
@require_POST
def note_autosave(request):
    note_id = request.POST.get('note_id')
    if note_id:
        try:
            note_id = int(note_id)
        except ValueError:
            return JsonResponse({'message': 'Invalid note.'}, status=400)
        note = get_object_or_404(Note, pk=note_id, owner=request.user)
    else:
        note = None

    data = request.POST.copy()
    title = data.get('title', '').strip()
    content = data.get('content', '')
    if not title and not content.strip():
        return JsonResponse({'saved': False, 'message': 'Start writing to save.'})
    data['title'] = title or 'Untitled note'

    form = NoteForm(data, instance=note)
    if not form.is_valid():
        return JsonResponse(
            {'message': 'Please fix the note before it can be saved.', 'errors': form.errors.get_json_data()},
            status=400,
        )

    note = form.save(commit=False)
    if note.pk is None:
        note.owner = request.user
    note.save()
    return JsonResponse({
        'saved': True,
        'note_id': note.pk,
        'detail_url': reverse('note_detail', kwargs={'pk': note.pk}),
        'message': 'Saved',
    })


@login_required
@require_http_methods(['GET', 'POST'])
def note_update(request, pk):
    note = get_object_or_404(Note, pk=pk, owner=request.user)
    if request.method == 'POST':
        form = NoteForm(request.POST, instance=note)
        if form.is_valid():
            form.save()
            return redirect('note_detail', pk=note.pk)
    else:
        form = NoteForm(instance=note)

    return render(
        request,
        'noteapp/note_form.html',
        {'form': form, 'is_edit': True, 'note': note},
    )


@login_required
@require_http_methods(['GET', 'POST'])
def note_delete(request, pk):
    note = get_object_or_404(Note, pk=pk, owner=request.user)
    if request.method == 'POST':
        note.delete()
        return redirect('note_list')

    return render(request, 'noteapp/note_confirm_delete.html', {'note': note})


def sign_up(request):
    if request.user.is_authenticated:
        return redirect('note_list')

    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('note_list')
    else:
        form = SignUpForm()

    return render(request, 'noteapp/accounts/signup.html', {'form': form})
