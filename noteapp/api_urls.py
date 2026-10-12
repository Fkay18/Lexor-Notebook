from django.urls import path

from . import api_views

app_name = 'api'

urlpatterns = [
    path('notes/', api_views.NoteListCreateAPIView.as_view(), name='note-list-create'),
    path('notes/<int:pk>/', api_views.NoteDetailAPIView.as_view(), name='note-detail'),
]
