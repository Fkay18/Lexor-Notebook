import re

from django.conf import settings
from django.core import mail
from django.contrib.auth.models import User
from django.test import TestCase, override_settings

from rest_framework.test import APIClient

from .models import Note


class PublicHomeAndAuthenticationTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='reader',
            email='reader@example.com',
            password='Good-Password-123!',
        )

    def test_logged_out_homepage_explains_the_app_and_offers_auth_links(self):
        response = self.client.get('/')

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Your thoughts, in one place.')
        self.assertContains(response, 'Preview of a private notebook')
        self.assertContains(response, 'href="/accounts/sign-up/"')
        self.assertContains(response, 'href="/accounts/sign-in/"')
        self.assertNotContains(response, 'your-email@example.com')
        self.assertNotContains(response, 'Your space')
        self.assertContains(response, 'Lexor Notebook')
        self.assertContains(response, '&middot;')

    def test_login_accepts_username_or_case_insensitive_email(self):
        for identifier in ('reader', 'READER@example.com'):
            with self.subTest(identifier=identifier):
                self.client.logout()
                response = self.client.post(
                    '/accounts/sign-in/',
                    {'username': identifier, 'password': 'Good-Password-123!'},
                )

                self.assertRedirects(response, '/')
                self.assertEqual(self.client.session['_auth_user_id'], str(self.user.pk))
                self.assertContains(self.client.get('/'), 'My Notes')

    def test_signup_uses_plain_username_help_and_password_visibility_controls(self):
        response = self.client.get('/accounts/sign-up/')

        self.assertContains(
            response,
            'Choose up to 150 characters using letters, numbers, and @ . + - _.',
        )
        self.assertNotContains(response, 'Required. 150 characters or fewer.')
        self.assertContains(response, 'data-password-toggle="id_password1"')
        self.assertContains(response, 'data-password-toggle="id_password2"')

    def test_signup_logs_user_in_and_returns_to_their_notes(self):
        response = self.client.post(
            '/accounts/sign-up/',
            {
                'username': 'new-reader',
                'email': 'new-reader@example.com',
                'password1': 'Good-Password-456!',
                'password2': 'Good-Password-456!',
            },
        )

        self.assertRedirects(response, '/')
        self.assertContains(self.client.get('/'), 'My Notes')
        self.assertTrue(User.objects.filter(username='new-reader').exists())


class NoteCrudTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username='owner', password='test-password')
        self.other_user = User.objects.create_user(username='other', password='test-password')
        self.note = Note.objects.create(
            owner=self.owner,
            title='A private note',
            content='Only the owner should see this.',
        )

    def test_list_contains_only_the_signed_in_users_notes(self):
        self.client.force_login(self.owner)
        response = self.client.get('/')

        self.assertContains(response, 'A private note')
        self.assertNotContains(response, 'Other user note')
        page = response.content.decode()
        menu_start = page.index('<details class="nav-menu">')
        menu_end = page.index('</details>', menu_start)
        menu = page[menu_start:menu_end]
        self.assertIn('aria-label="Open menu"', menu)
        self.assertIn('M4 6h16M4 12h16M4 18h16', menu)
        self.assertIn('id="theme-toggle"', menu)
        self.assertIn('>Log out</button>', menu)

        Note.objects.create(owner=self.other_user, title='Other user note', content='Hidden')
        response = self.client.get('/')
        self.assertNotContains(response, 'Other user note')

    def test_detail_and_edit_are_limited_to_the_owner(self):
        self.client.force_login(self.other_user)
        self.assertEqual(self.client.get(f'/notes/{self.note.pk}/').status_code, 404)
        self.assertEqual(self.client.get(f'/notes/{self.note.pk}/edit/').status_code, 404)

        self.client.force_login(self.owner)
        self.assertContains(self.client.get(f'/notes/{self.note.pk}/edit/'), 'Save changes')
        response = self.client.post(
            f'/notes/{self.note.pk}/edit/',
            {'title': 'Updated title', 'content': 'Updated content'},
        )
        self.assertRedirects(response, f'/notes/{self.note.pk}/')
        self.note.refresh_from_db()
        self.assertEqual(self.note.title, 'Updated title')
        self.assertEqual(self.note.content, 'Updated content')

    def test_create_assigns_current_user_as_owner(self):
        self.client.force_login(self.owner)
        response = self.client.get('/notes/new/')
        self.assertContains(response, 'note-save-status')
        self.assertContains(response, 'Create note')
        self.assertContains(response, 'note_editor.')
        response = self.client.post(
            '/notes/new/',
            {
                'title': 'New note',
                'content': 'A note from me',
                'owner': self.other_user.pk,
            },
        )

        note = Note.objects.get(title='New note')
        self.assertRedirects(response, '/')
        self.assertContains(self.client.get('/'), 'New note')
        self.assertEqual(note.owner, self.owner)

    def test_note_routes_require_login(self):
        paths = [
            '/notes/new/',
            '/notes/autosave/',
            f'/notes/{self.note.pk}/',
            f'/notes/{self.note.pk}/edit/',
            f'/notes/{self.note.pk}/delete/',
        ]
        for path in paths:
            with self.subTest(path=path):
                response = self.client.get(path)
                self.assertRedirects(response, f'/accounts/sign-in/?next={path}')

    def test_autosave_creates_note_for_signed_in_owner(self):
        self.client.force_login(self.owner)
        response = self.client.post(
            '/notes/autosave/',
            {'title': 'Autosaved note', 'content': 'Saved while writing'},
        )

        self.assertEqual(response.status_code, 200)
        note = Note.objects.get(title='Autosaved note')
        self.assertEqual(response.json()['detail_url'], f'/notes/{note.pk}/')
        self.assertEqual(note.owner, self.owner)
        self.assertEqual(note.content, 'Saved while writing')

    def test_autosave_updates_only_owned_notes(self):
        self.client.force_login(self.other_user)
        self.assertEqual(
            self.client.post(
                '/notes/autosave/',
                {'note_id': self.note.pk, 'title': 'Stolen', 'content': 'No'},
            ).status_code,
            404,
        )

        self.client.force_login(self.owner)
        response = self.client.post(
            '/notes/autosave/',
            {'note_id': self.note.pk, 'title': 'Autosaved edit', 'content': 'Updated as I type'},
        )
        self.assertEqual(response.status_code, 200)
        self.note.refresh_from_db()
        self.assertEqual(self.note.title, 'Autosaved edit')
        self.assertEqual(self.note.content, 'Updated as I type')

    def test_autosave_does_not_create_empty_notes_and_reports_invalid_data(self):
        self.client.force_login(self.owner)
        response = self.client.post('/notes/autosave/', {'title': '', 'content': '   '})
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()['saved'])
        self.assertFalse(Note.objects.filter(owner=self.owner, title='Untitled note').exists())

        response = self.client.post(
            '/notes/autosave/',
            {'title': 'x' * 201, 'content': 'Too long title'},
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn('errors', response.json())

    def test_delete_requires_confirmation_and_is_limited_to_the_owner(self):
        self.client.force_login(self.other_user)
        self.assertEqual(self.client.get(f'/notes/{self.note.pk}/delete/').status_code, 404)
        self.assertEqual(self.client.post(f'/notes/{self.note.pk}/delete/').status_code, 404)

        self.client.force_login(self.owner)
        response = self.client.get(f'/notes/{self.note.pk}/delete/')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Note.objects.filter(pk=self.note.pk).exists())

        response = self.client.post(f'/notes/{self.note.pk}/delete/')
        self.assertRedirects(response, '/')
        self.assertFalse(Note.objects.filter(pk=self.note.pk).exists())


class NoteAPIAuthenticationTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='api-user', password='test-password')
        self.note = Note.objects.create(
            owner=self.user,
            title='API note',
            content='Visible only to the owner.',
        )

    def test_only_jwt_and_session_authentication_are_configured(self):
        self.assertEqual(
            settings.REST_FRAMEWORK['DEFAULT_AUTHENTICATION_CLASSES'],
            [
                'rest_framework_simplejwt.authentication.JWTAuthentication',
                'rest_framework.authentication.SessionAuthentication',
            ],
        )

    def test_unauthenticated_api_requests_receive_bearer_challenge(self):
        response = APIClient().get('/api/notes/')

        self.assertEqual(response.status_code, 401)
        self.assertTrue(response['WWW-Authenticate'].startswith('Bearer '))

    def test_jwt_authentication_can_access_notes(self):
        token_response = APIClient().post(
            '/api/token/',
            {'username': 'api-user', 'password': 'test-password'},
            format='json',
        )
        self.assertEqual(token_response.status_code, 200)

        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {token_response.data['access']}")
        response = client.get('/api/notes/')

        self.assertEqual(response.status_code, 200)
        self.assertEqual([note['id'] for note in response.data], [self.note.pk])

    def test_session_authentication_can_access_notes(self):
        client = APIClient()
        self.assertTrue(client.login(username='api-user', password='test-password'))

        response = client.get('/api/notes/')

        self.assertEqual(response.status_code, 200)
        self.assertEqual([note['id'] for note in response.data], [self.note.pk])


@override_settings(
    SECURE_SSL_REDIRECT=True,
    SECURE_PROXY_SSL_HEADER=('HTTP_X_FORWARDED_PROTO', 'https'),
)
class RailwayHTTPSRedirectTests(TestCase):
    def test_forwarded_https_request_is_not_redirected_again(self):
        response = self.client.get(
            '/accounts/sign-in/',
            HTTP_X_FORWARDED_PROTO='https',
        )

        self.assertEqual(response.status_code, 200)


@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
class PasswordResetTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='reset-user',
            email='reset@example.com',
            password='Old-Test-Password-123!',
        )

    def test_login_has_password_reset_link(self):
        response = self.client.get('/accounts/sign-in/')

        self.assertContains(response, 'Forgot your password?')
        self.assertContains(response, 'href="/accounts/password-reset/"')

    def test_account_pages_render_from_accounts_template_folder(self):
        login_response = self.client.get('/accounts/sign-in/')
        signup_response = self.client.get('/accounts/sign-up/')
        reset_response = self.client.get('/accounts/password-reset/')

        self.assertEqual(login_response.status_code, 200)
        self.assertEqual(signup_response.status_code, 200)
        self.assertEqual(reset_response.status_code, 200)

    def test_password_reset_email_link_changes_password(self):
        response = self.client.post(
            '/accounts/password-reset/',
            {'email': self.user.email},
        )

        self.assertRedirects(response, '/accounts/password-reset/done/')
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, [self.user.email])
        self.assertEqual(mail.outbox[0].from_email, settings.DEFAULT_FROM_EMAIL)
        reset_url = re.search(
            r'http://testserver(/accounts/reset/[\w-]+/[\w-]+/)',
            mail.outbox[0].body,
        )
        self.assertIsNotNone(reset_url)

        response = self.client.get(reset_url.group(1))
        self.assertEqual(response.status_code, 302)
        confirm_url = response['Location']
        self.assertContains(self.client.get(confirm_url), 'name="new_password1"')

        response = self.client.post(
            confirm_url,
            {
                'new_password1': 'New-Test-Password-456!',
                'new_password2': 'New-Test-Password-456!',
            },
        )
        self.assertRedirects(response, '/accounts/reset/done/')
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('New-Test-Password-456!'))

    def test_unknown_email_does_not_reveal_account_existence(self):
        response = self.client.post(
            '/accounts/password-reset/',
            {'email': 'unknown@example.com'},
        )

        self.assertRedirects(response, '/accounts/password-reset/done/')
        self.assertEqual(mail.outbox, [])
