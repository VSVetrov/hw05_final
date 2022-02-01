import shutil
import tempfile

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Group, Post

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='username')
        cls.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.image = SimpleUploadedFile(
            name='small.gif',
            content= cls.small_gif,
            content_type='image/gif',
        )
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовая группа',
            group=cls.group,
            image=cls.image,
        )
        cls.detail = (
            'posts:post_detail', 'posts/post_detail.html', (cls.post.id,))

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def test_home_page_show_correct_context(self):
        response = self.guest_client.get(reverse('posts:index'))
        self.assertEqual(len(response.context['page_obj']), 1)

    def test_group_list_page_show_correct_context(self):
        response = self.guest_client.get(reverse('posts:group_list', kwargs={
            'slug': 'test-slug'}))
        self.assertEqual(len(response.context['page_obj']), 1)

    def test_profile_page_show_correct_context(self):
        response = self.guest_client.get(reverse('posts:profile', kwargs={
            'username': self.post.author}))
        self.assertEqual(response.context['post_count'], 1)

    def test_post_detail_page_show_correct_context(self):
        response = self.authorized_client.get(reverse(
            'posts:post_detail', kwargs={'post_id': self.post.id}
        ))
        self.assertEqual(response.context['post_count'], 1)

    def test_post_edit_page_show_correct_context(self):
        response = self.authorized_client.get(reverse(
            'posts:post_edit', kwargs={'post_id': self.post.id}
        ))
        form_fields = {
            self.post.text: response.context['form']['text'].value(),
            self.post.group.id: response.context[
                'form']['group'].value(),
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                self.assertEqual(value, expected)

    def test_create_post_page_show_correct_context(self):
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
            'image':forms.fields.ImageField
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
            self.assertIsInstance(form_field, expected)

    def test_adding_comment(self):
        response = self.authorized_client.get(reverse('posts:add_comment'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
            'image':forms.fields.ImageField
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
            self.assertIsInstance(form_field, expected)

    def test_index_cache(self):
        cache.clear()
        response_1 = self.authorized_client.get(reverse('posts:index'))
        self.post.delete()
        response_2 = self.authorized_client.get(reverse('posts:index'))
        self.assertEqual(response_1.content, response_2.content)
        cache.delete('index_page')
        cache.clear()
        response_3 = self.authorized_client.get(reverse('posts:index'))
        self.assertNotEqual(response_1.content, response_3.content)

    def test_create_post(self):
        post_count = Post.objects.count()
        form_data = {
            'text': 'Тестовый текст новый',
            'group': self.group.id,
            'image': 'posts/small.gif',
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response, reverse('posts:profile',
                              kwargs={'username': self.user.username})
        )
        self.assertEqual(Post.objects.count(), post_count + 1)
        self.assertContains(response, 'image')

    def test_follow(self):
        response_1 = self.authorized_client.get(reverse('posts:profile_follow'), kwargs={
            'username': self.post.username})
        response_2 = self.authorized_client.get(reverse('posts:profile_unfollow'), kwargs={
            'username': self.post.username})
        self.assertEqual(response_1, reverse('posts:profile_follow',
                              kwargs={'username': self.post.username})
        )
        self.assertEqual(response_2, reverse('posts:profile_unfollow',
                              kwargs={'username': self.post.username})
        )

    def test_new_post_for_following(self):
        response = self.authorized_client.get(reverse('posts:follow_index'))
        self.assertEqual(response.context['page_obj'], 1)
        