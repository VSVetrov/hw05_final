from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from ..forms import PostForm
from ..models import Group, Post

User = get_user_model()


class PostCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='username')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовая группа',
            group=cls.group,
        )
        cls.form = PostForm()
        cls.post_edit_url = reverse(
            'posts:post_edit',
            args=[cls.post.id]
        )
        cls.add_comment_url = reverse(
            'posts:add_comment',
            args=[cls.post.id]
        )

    def setUp(self):
        self.auth_client = Client()
        self.auth_client.force_login(self.user)

    def test_post_create(self):
        posts_count = Post.objects.count()
        form_data = {
            'title': 'Заголовок из формы',
            'text': 'Текст из формы',
        }
        response = self.auth_client.post(
            reverse('posts:post_create'),
            data=form_data,
        )
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertEqual(response.status_code, 302)

    def test_post_edit(self):
        posts_count = Post.objects.count()
        form_data = {
            'title': 'Заголовок из формы',
            'text': 'text',
            'slug': 'first',
        }
        response = self.auth_client.post(
            self.post_edit_url,
            data=form_data,
            follow=True
        )
        edited_post = Post.objects.last()
        self.assertEqual(edited_post.text, 'text')
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertEqual(response.status_code, 200)

    def test_add_comment(self):
        form_data = {
            'text': 'text',
            'slug': 'first',
        }
        response = self.auth_client.post(
            self.add_comment_url,
            data=form_data,
            follow=True
        )
        comments_post = Post.objects.last()
        self.assertEqual(comments_post.text, 'Тестовая группа')
        self.assertEqual(response.status_code, 200)
