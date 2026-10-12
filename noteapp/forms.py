from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import Note


class SignUpForm(UserCreationForm):
    email = forms.EmailField(required=True, label='Email address')

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'email', 'password1', 'password2')

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('An account with this email address already exists.')
        return email


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
