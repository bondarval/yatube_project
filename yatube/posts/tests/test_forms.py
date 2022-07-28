import shutil
import tempfile

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Post, Group
from posts.forms import PostForm

User = get_user_model()


class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        settings.MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
        cls.author = User.objects.create(username='MrAnon')
        cls.group = Group.objects.create(
            title='Заголовок тестовой группы',
            slug='test-group',
            description='Тестовый текст'
        )
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x01\x00'
            b'\x01\x00\x00\x00\x00\x21\xf9\x04'
            b'\x01\x0a\x00\x01\x00\x2c\x00\x00'
            b'\x00\x00\x01\x00\x01\x00\x00\x02'
            b'\x02\x4c\x01\x00\x3b'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        cls.post = Post.objects.create(
            text='Just text',
            author=cls.author,
            group=cls.group,
            image=cls.uploaded
        )
        cls.form = PostForm()

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.author)

    def test_post_create(self):
        """Проверяет форму создания нового поста."""
        posts_count = Post.objects.count()
        form_data = {
            'text': self.post.text,
            'group': self.group.id,
            'image': self.post.image,
        }
        self.authorized_client.post(
            reverse('new_post'),
            data=form_data,
            follow=True
        )
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertTrue(Post.objects.filter(
            text=form_data['text'],
            group=form_data['group'],
            image=form_data['image'],
        ).exists()
        )

    def test_post_edit(self):
        """Проверяет внесение изменений в пост."""
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Just another',
            'group': self.group.id
        }
        self.authorized_client.post(
            reverse('post_edit', kwargs={
                'username': self.author.username,
                'post_id': self.post.id}
            ),
            data=form_data,
            follow=True
        )
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertTrue(Post.objects.filter(
            text=form_data['text'],
            group=form_data['group']
        ).exists()
        )

    def test_post_create_unauthorized(self):
        """Проверяет создание поста неавторизованным пользователем"""
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Just anything',
            'group': self.group.id
        }
        self.guest_client.post(
            reverse('new_post'),
            data=form_data,
            follow=True
        )
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertFalse(Post.objects.filter(
            text=form_data['text'],
            group=form_data['group']
        ).exists()
        )
