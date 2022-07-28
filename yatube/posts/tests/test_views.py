import shutil
import tempfile
from http import HTTPStatus

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, Client
from django.urls import reverse

from posts.forms import PostForm
from posts.models import Group, Post, Follow, Comment

User = get_user_model()


class StaticViewsTests(TestCase):
    """Тестируются статичные страницы."""

    def setUp(self):
        self.guest_client = Client()

    def test_about_page_accessible_by_name(self):
        """URL, генерируемый при помощи имен, доступен."""
        urls = {
            '/about/author/': HTTPStatus.OK,
            '/about/tech/': HTTPStatus.OK,
        }
        for address, HTTPStatus.value in urls.items():
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertEqual(response.status_code, HTTPStatus.value)

    def test_about_page_uses_correct_template(self):
        """При запросе к страницам применяются корректные шаблоны."""
        templates = {
            'about/author.html': reverse('about:author'),
            'about/tech.html': reverse('about:tech'),
        }
        for template, reverse_name in templates.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.guest_client.get(reverse_name)
                self.assertTemplateUsed(response, template)


class PostPagesTests(TestCase):
    """
    Тестируются шаблоны, контекст и пагинация
    на страницах сайта.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            title='Заголовок тестовой группы',
            slug='test-group',
            description='Тестовый текст'
        )
        cls.author = User.objects.create(username='MrSmith')
        cls.user = User.objects.create(username='MrAnon')
        for _ in range(13):
            cls.post = Post.objects.create(
                text='Тестовый пост',
                author=cls.author,
                group=cls.group
            )

    def setUp(self):
        cache.clear()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.authorized_client.force_login(self.author)

    def test_pages_use_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_page_names = {
            'index.html': reverse('index'),
            'group.html': reverse('group', kwargs={'slug': self.group.slug}),
            'new.html': reverse('new_post'),
        }
        for template, reverse_name in templates_page_names.items():
            with self.subTest(template=template):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_main_page_shows_correct_context(self):
        """Шаблон главной страницы сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('index'))
        first_object = response.context['page'][0]
        post_text_0 = first_object.text
        self.assertEqual(post_text_0, 'Тестовый пост')

    def test_group_page_shows_correct_context(self):
        """Шаблон страницы группы сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('group', kwargs={'slug': self.group.slug})
        )
        contexts = {
            'group': self.group,
        }
        for i, context in contexts.items():
            with self.subTest(context=context):
                self.assertEqual(response.context[i], context)

    def test_post_create_page_shows_correct_context(self):
        """
        Шаблон страницы создания поста сформирован
        с правильным контекстом.
        """
        response = self.authorized_client.post(reverse('new_post'))
        form_data = {
            'text': 'Тестовый пост',
            'group': self.group,
        }
        for value, data in form_data.items():
            with self.subTest(value=value):
                self.assertIn('form', response.context)
                self.assertIsInstance(response.context['form'], PostForm)

    def test_post_edit_page_shows_correct_context(self):
        """
        Шаблон страницы редактирования поста сформирован
        с правильным контекстом.
        """
        self.authorized_client.force_login(self.author)
        response = self.authorized_client.post(reverse(
            'post_edit',
            kwargs={
                'username': self.author.username,
                'post_id': self.post.id
            }
        ))
        form_data = {
            'text': 'Тестов пост',
            'group': self.group,
        }
        for value, data in form_data.items():
            with self.subTest(value=value):
                self.assertIn('form', response.context)
                self.assertIsInstance(response.context['form'], PostForm)

    def test_profile_shows_correct_context(self):
        """
        Шаблон профиля пользователя сформирован
        с правильным контекстом.
        """
        self.authorized_client.force_login(self.user)
        response = self.authorized_client.post(reverse(
            'profile',
            kwargs={'username': self.author.username}
        ))
        first_object = response.context['page'][0]
        post_text_0 = first_object.text
        self.assertEqual(post_text_0, 'Тестовый пост')

    def test_post_view_page_shows_correct_context(self):
        """
        Шаблон страницы просмотра отдельного поста сформирован
        с правильным контекстом.
        """
        self.authorized_client.force_login(self.author)
        response = self.authorized_client.post(reverse(
            'post_view',
            kwargs={
                'username': self.author.username,
                'post_id': self.post.id,
            }
        ))
        self.assertEqual(response.context['username'], self.author.username)
        self.assertEqual(response.context['post'], self.post)
        self.assertEqual(response.context['post_count'], 13)

    def test_created_post_on_group_correct(self):
        """На главной странице отображается пост конкретной группы."""
        response = self.client.get(reverse('index'))
        first_object = response.context['page'][0]
        group = first_object.group
        post_text = first_object.text
        post_group_slug = first_object.group.slug
        self.assertEqual(group, first_object.group)
        self.assertEqual(post_text, first_object.text)
        self.assertEqual(post_group_slug, first_object.group.slug)

    def test_created_post_on_related_page_group_correct(self):
        """На странице группы отображается пост этой группы."""
        response = self.client.get(reverse(
            'group', kwargs={'slug': self.group.slug}))
        first_object = response.context['page'][0]
        group = first_object.group
        post_text = first_object.text
        post_group_slug = first_object.group.slug
        self.assertEqual(group, first_object.group)
        self.assertEqual(post_text, first_object.text)
        self.assertEqual(post_group_slug, first_object.group.slug)

    def test_first_main_page_contains_ten_records(self):
        """На главной странице отображается заданное количество постов."""
        response = self.client.get(reverse('index'))
        self.assertEqual(len(response.context.get('page').object_list), 10)

    def test_first_page_group_contains_ten_records(self):
        """На странице группы отображается заданное количество постов."""
        response = self.client.get(reverse(
            'group',
            kwargs={'slug': self.group.slug})
        )
        self.assertEqual(len(response.context.get('page').object_list), 10)

    def test_first_page_profile_contains_ten_records(self):
        """На странице профиля отображается заданное количество постов."""
        response = self.client.get(reverse(
            'profile',
            kwargs={'username': self.author.username})
        )
        self.assertEqual(len(response.context.get('page').object_list), 10)

    def test_second_page_main_contains_three_records(self):
        """Деление на страницы на главной странице работает корректно."""
        response = self.client.get(reverse('index') + '?page=2')
        self.assertEqual(len(response.context.get('page').object_list), 3)

    def test_second_page_group_contains_three_records(self):
        """Деление на страницы на странице группы работает корректно."""
        response = self.client.get(reverse(
            'group',
            kwargs={'slug': self.group.slug}) + '?page=2')
        self.assertEqual(len(response.context.get('page').object_list), 3)

    def test_second_page_profile_contains_three_records(self):
        """Деление на страницы на странице профиля работает корректно."""
        response = self.client.get(reverse(
            'profile',
            kwargs={'username': self.author.username}) + '?page=2')
        self.assertEqual(len(response.context.get('page').object_list), 3)


class PostImageTest(TestCase):
    """
    Тестируется корректность передачи изображения на страницах.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        settings.MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
        cls.user = User.objects.create_user(username='MrAnon')
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
            text='Тестовый пост',
            author=cls.user,
            group=cls.group,
            image=cls.uploaded
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        cache.clear()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_index_page_shows_correct_context(self):
        """Проверяется передача изображения на главной странице."""
        response = self.authorized_client.get(reverse('index'))
        self.assertEqual(response.context.get('page').object_list[0].image,
                         self.post.image)

    def test_profile_page_shows_correct_context(self):
        """Проверяется передача изображения на странице профиля."""
        response = self.authorized_client.get(
            reverse(
                'profile',
                kwargs={'username': self.user.username}
            ))
        self.assertEqual(response.context.get('page').object_list[0].image,
                         self.post.image)

    def test_group_page_shows_correct_context(self):
        """Проверяется передача изображения на странице группы."""
        response = self.authorized_client.get(reverse(
            'group',
            kwargs={'slug': self.group.slug}
        )
        )
        self.assertEqual(
            response.context.get('page').object_list[0].image,
            self.post.image
        )

    def test_post_view_page_shows_correct_context(self):
        """
        Проверяется передача изображения на странице
        просмотра отдельного поста.
        """
        self.authorized_client.force_login(self.user)
        response = self.authorized_client.post(reverse(
            'post_view',
            kwargs={
                'username': self.user.username,
                'post_id': self.post.id,
            }
        ))
        self.assertEqual(response.context['post'].image, self.post.image)

    def test_new_post_page_shows_correct_context(self):
        """Проверяется передача изображения в форме создания поста."""
        self.authorized_client.force_login(self.user)
        posts_count = Post.objects.count()
        form_data = {
            'text': self.post.text,
            'image': self.post.image,
        }
        response = self.authorized_client.post(
            path=reverse("new_post"),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse("index"))
        self.assertEqual(Post.objects.count(), posts_count + 1)


class PostFollowTests(PostPagesTests, TestCase):
    """
    Тестируется корректность работы системы подписок и комментирования.
    """

    def setUp(self):
        cache.clear()
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.authorized_client.force_login(self.author)

    def test_follow(self):
        """Подписка на автора работает корректно."""
        Follow.objects.get_or_create(author=self.author, user=self.user)
        self.authorized_client.get(reverse(
            'profile_follow',
            kwargs={'username': f'{self.author.username}'}
        ))
        following = Follow.objects.filter(
            author=self.author,
            user=self.user).exists()
        self.assertEqual(following, True)
        for _ in range(3):
            self.authorized_client.get(reverse(
                'profile_follow',
                kwargs={'username': f'{self.author.username}'}
            ))
        self.assertEqual(Follow.objects.all().count(), 1)

    def test_follow_user(self):
        """
        Подписка на автора работает для авторизованного пользователя.
        """
        self.authorized_client.force_login(self.user)
        count = Follow.objects.filter(user=self.user).count()
        self.authorized_client.get(reverse(
            'profile_follow',
            kwargs={'username': f'{self.author.username}'}
        ))
        follow_count = Follow.objects.filter(user=self.user).count()
        self.assertEqual(follow_count, count + 1)

    def test_follower(self):
        """Система подписок работает корректно."""
        Follow.objects.get_or_create(author=self.author, user=self.user)
        self.authorized_client.get(reverse(
            'profile_follow',
            kwargs={'username': f'{self.author.username}'}
        ))
        follower = Follow.objects.last()
        data_to_compare = (
            (follower.user, self.user),
            (follower.author, self.author),
        )
        for attributes, expected in data_to_compare:
            with self.subTest(attributes=attributes):
                self.assertEqual(attributes, expected)

    def test_follow_delete(self):
        """
        Отписка от автора работает корректно.
        """
        self.authorized_client.force_login(self.user)
        Follow.objects.get_or_create(author=self.author, user=self.user)
        self.authorized_client.get(reverse(
            'profile_unfollow',
            kwargs={'username': f'{self.author.username}'}
        ))
        following = Follow.objects.filter(
            author=self.author,
            user=self.user).exists()
        self.assertNotEqual(following, True)
        self.assertEqual(Follow.objects.all().count(), 0)

    def test_comment_authorized(self):
        """Только авторизированный пользователь может комментировать посты."""
        comment_count = Comment.objects.filter(author=self.user).count()
        self.guest_client.post(reverse(
            'post_view',
            kwargs={
                'username': self.author.username,
                'post_id': self.post.id,
            }
        ))
        Comment.objects.get_or_create(author=self.user, post_id=self.post.id)
        self.assertEqual(comment_count, 0)


class PostCacheTests(TestCase):
    """
    Тестируется корректность работы кеширования на страницах.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            title='Заголовок тестовой группы',
            slug='test-group',
            description='Тестовый текст'
        )
        cls.author = User.objects.create(username='MrSmith')
        cls.user = User.objects.create_user(username='MrAnon')
        cls.post = Post.objects.create(
            text='Тестовый пост',
            author=cls.user,
            group=cls.group,
        )

    def setUp(self):
        cache.clear()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.authorized_client.force_login(self.author)

    def test_cache_index(self):
        response = self.authorized_client.get(reverse('index'))
        number_posts = len(response.context.get('page').object_list)
        self.post.delete()
        response = self.authorized_client.get(reverse('index'))
        self.assertEqual(
            len(response.context.get('page').object_list),
            number_posts
        )
        cache.clear()
        response = self.authorized_client.get(reverse('index'))
        self.assertEqual(len(
            response.context.get('page').object_list),
            number_posts - 1
        )
