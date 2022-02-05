from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse

from ..forms import PostForm
from ..models import Comment, Group, Post

User = get_user_model()


class PostCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='username')
        cls.user_auth = User.objects.create_user(username='test_auth_user')
        cls.another = Client()
        cls.another.force_login(cls.user_auth)
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
            content=cls.small_gif,
            content_type='image/gif',
        )
        cls.post_edit_url = reverse(
            'posts:post_edit',
            args=[cls.post.id]
        )
        cls.add_comment_url = reverse(
            'posts:add_comment',
            args=[cls.post.id]
        )
        cls.post_detail_url = reverse(
            'posts:post_detail', args=[cls.post.id]
        )

    def setUp(self):
        self.auth_client = Client()
        self.auth_client.force_login(self.user)

    def test_post_create(self):
        posts_count = Post.objects.count()
        form_data = {
            'title': 'Заголовок из формы',
            'text': 'Текст из формы',
            'image': self.image,
        }
        response = self.auth_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'image')

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
        comments_count = Comment.objects.count()
        all_comments = set(Comment.objects.all())
        form_data = {'text': 'Текстовый комментарий'}
        response = self.another.post(
            self.add_comment_url,
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response,
            self.post_detail_url
        )
        self.assertEqual(Comment.objects.count(), comments_count + 1)
        comments = set(Comment.objects.all()) - all_comments
        self.assertEqual(len(comments), 1)
        comment = comments.pop()
        self.assertEqual(comment.text, form_data['text'])
        self.assertEqual(comment.author, self.user_auth)
        self.assertEqual(comment.post, self.post)
