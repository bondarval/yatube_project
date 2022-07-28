from django.contrib.auth import get_user_model
from django.test import TestCase

from posts.models import Group, Post

User = get_user_model()


class PostsModelsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            title='Заголовок тестовой группы',
            slug='test-group',
            description='Тестовый текст'
        )
        cls.author = User.objects.create(username='BondarV')
        cls.post = Post.objects.create(
            text='Тестовый текст',
            author=cls.author,
            group=cls.group
        )

    def test_group_name_is_title_field(self):
        group = PostsModelsTest.group
        expected_object_name = group.title
        self.assertEqual(expected_object_name, str(group))

    def test_post_name_is_title_field(self):
        post = PostsModelsTest.post
        expected_object_name = post.text
        self.assertEqual(expected_object_name, str(post))
