from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Group, Post

User = get_user_model()


class StaticURLTests(TestCase):
    def setUp(self):
        self.guest_client = Client()

    def test_homepage(self):
        response = self.guest_client.get('/')
        self.assertEqual(response.status_code, 200)

    def test_author(self):
        response = self.guest_client.get('/about/author/')
        self.assertEqual(response.status_code, 200)

    def test_tech(self):
        response = self.guest_client.get('/about/tech/')
        self.assertEqual(response.status_code, 200)


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='username')
        cls.user1 = User.objects.create_user(username='leo')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовая группа',
        )
        cls.index_url = ('posts:index', 'posts/index.html', None)
        cls.group_url = (
            'posts:group_list', 'posts/group_list.html', (cls.group.slug,))
        cls.detail = (
            'posts:post_detail', 'posts/post_detail.html', (cls.post.id,))
        cls.profile = (
            'posts:profile', 'posts/profile.html', (cls.post.author,))
        cls.create = ('posts:post_create', 'posts/create_post.html', None)
        cls.edit = (
            'posts:post_edit', 'posts/create_post.html', (cls.post.id,))

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_urls_uses_correct_template(self):
        urls = (
            self.index_url,
            self.group_url,
            self.detail,
            self.profile,
            self.create,
            self.edit
        )
        for url, template, args in urls:
            with self.subTest(template=template):
                response = self.authorized_client.get(reverse(url, args=args))
                self.assertTemplateUsed(response, template)

    def test_posts_edit_url_uses_correct_template(self):
        response = self.guest_client.get(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id})
        )
        self.assertRedirects(
            response, (f'/auth/login/?next=/posts/{self.post.id}/edit/')
        )

    def test_posts_create_url_uses_correct_template(self):
        response = self.guest_client.get(reverse('posts:post_create'))
        self.assertRedirects(response, ('/auth/login/?next=/create/'))

    def test_posts_edit_another_id_post(self):
        response = self.authorized_client.get(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}),
            username=self.user.id, author=self.user1.id
        )
        self.assertEqual(response.status_code, 200)

    def test_posts_edit_not_existing_post(self):
        response = self.authorized_client.get('/posts/452/edit/')
        self.assertEqual(response.status_code, 404)

    def test_add_comment_authorized(self):
        response = self.guest_client.get(
            reverse('posts:add_comment', kwargs={'post_id': self.post.id})
        )
        self.assertRedirects(
            response, (f'/auth/login/?next=/posts/{self.post.id}/comment')
        )

    def test_follow(self):
        response = self.authorized_client.get(
            reverse('posts:profile_follow',
            kwargs={'username': self.user.username})
        )
        self.assertRedirects(
            response, (f'/profile/{self.user}/'))

    def test_unfollow(self):
        response = self.authorized_client.get(
            reverse('posts:profile_unfollow',
            kwargs={'username': self.user.username})
        )
        self.assertRedirects(
            response, (f'/profile/{self.user}/'))
