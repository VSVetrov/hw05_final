from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import Group, Post

User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовая группа',
        )

    def test_models_have_correct_object_names(self):
        group = self.group
        expected_object_name = group.title
        post = PostModelTest.post
        self.assertEqual(expected_object_name, str(group))
        self.assertEqual(post.text[:15], str(post))

    def test_title_label(self):
        task = PostModelTest.group
        verbose = task._meta.get_field('title').verbose_name
        self.assertEqual(verbose, 'Имя')

    def test_title_help_text(self):
        task = PostModelTest.group
        help_text = task._meta.get_field('title').help_text
        self.assertEqual(help_text, '')
