from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

urlpatterns = [
    path('', views.note_list, name='note_list'),
    path('notes/new/', views.note_create, name='note_create'),
    path('notes/autosave/', views.note_autosave, name='note_autosave'),
    path('notes/<int:pk>/', views.note_detail, name='note_detail'),
    path('notes/<int:pk>/edit/', views.note_update, name='note_update'),
    path('notes/<int:pk>/delete/', views.note_delete, name='note_delete'),
    path('accounts/sign-up/', views.sign_up, name='sign_up'),
    path(
        'accounts/password-reset/',
        auth_views.PasswordResetView.as_view(
            template_name='noteapp/accounts/password_reset_form.html',
            email_template_name='noteapp/accounts/password_reset_email.html',
            subject_template_name='noteapp/accounts/password_reset_subject.txt',
        ),
        name='password_reset',
    ),
    path(
        'accounts/password-reset/done/',
        auth_views.PasswordResetDoneView.as_view(
            template_name='noteapp/accounts/password_reset_done.html',
        ),
        name='password_reset_done',
    ),
    path(
        'accounts/reset/<uidb64>/<token>/',
        auth_views.PasswordResetConfirmView.as_view(
            template_name='noteapp/accounts/password_reset_confirm.html',
        ),
        name='password_reset_confirm',
    ),
    path(
        'accounts/reset/done/',
        auth_views.PasswordResetCompleteView.as_view(
            template_name='noteapp/accounts/password_reset_complete.html',
        ),
        name='password_reset_complete',
    ),
    path(
        'accounts/sign-in/',
        auth_views.LoginView.as_view(
            template_name='noteapp/accounts/login.html',
            redirect_authenticated_user=True,
        ),
        name='login',
    ),
    path('accounts/sign-out/', auth_views.LogoutView.as_view(next_page='note_list'), name='logout',),
]
