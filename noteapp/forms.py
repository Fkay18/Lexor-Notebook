from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User

from .models import Note


class SignUpForm(UserCreationForm):
    username = forms.CharField(
        label='Username',
        max_length=150,
        validators=User._meta.get_field('username').validators,
        help_text='Choose up to 150 characters using letters, numbers, and @ . + - _.',
    )
    email = forms.EmailField(required=True, label='Email address')
    password1 = forms.CharField(
        label='Password',
        strip=False,
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password'}),
        help_text='Use at least 8 characters.',
    )
    password2 = forms.CharField(
        label='Confirm password',
        strip=False,
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password'}),
        help_text='',
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'email', 'password1', 'password2')

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError(
                'This email is already linked to an account. If it is yours, log in or reset your password.',
                code='email_in_use',
            )
        return email


class EmailOrUsernameAuthenticationForm(AuthenticationForm):
    username = forms.CharField(
        label='Username or email address',
        widget=forms.TextInput(attrs={
            'autofocus': True,
            'autocomplete': 'username',
            'placeholder': 'Username or email address',
        }),
    )

    def clean(self):
        identifier = self.cleaned_data.get('username')
        if identifier and '@' in identifier:
            user = get_user_model().objects.filter(
                email__iexact=identifier,
            ).only('username').first()
            if user:
                self.cleaned_data['username'] = user.get_username()
        return super().clean()


class NoteForm(forms.ModelForm):
    class Meta:
        model = Note
        fields = ('title', 'content')
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'note-input',
                'autofocus': True,
                'placeholder': 'Title',
                'maxlength': 200,
            }),
            'content': forms.Textarea(attrs={
                'class': 'note-input note-content-input',
                'rows': 12,
                'placeholder': 'Start writing...',
            }),
        }
