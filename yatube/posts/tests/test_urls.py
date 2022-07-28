from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase, Client
from django.urls import reverse

from posts.models import Post, Group

User = get_user_model()


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            title='Заголовок тестовой группы',
            slug='test-group',
            description='Тестовый текст'
        )
        cls.author = User.objects.create(username='BondarV')
        cls.user = User.objects.create_user(username='MrAnon')
        cls.post = Post.objects.create(
            text='Тестовый текст',
            author=cls.author,
            group=cls.group
        )
        cls.index_url = ('index', 'index.html', None)
        cls.group_url = ('group', 'group.html', (cls.group.slug,))
        cls.profile_url = ('profile', 'profile.html', (cls.user.username,))
        cls.post_url = (
            'post_view',
            'post.html',
            (cls.author.username, cls.post.id,)
        )
        cls.new_post_url = ('new_post', 'new.html', None)
        cls.post_edit_url = (
            'post_edit',
            'new.html',
            (cls.author.username, cls.post.id)
        )

    def setUp(self):
        cache.clear()
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.authorized_client.force_login(self.author)

    def test_unauthorised_url(self):
        """
        Проверяется отображение страниц для неавторизованных пользователей.
        """
        url_addresses = {
            '/': HTTPStatus.OK,
            f'/group/{ self.group.slug }/': HTTPStatus.OK,
            f'/{ self.user.username }/': HTTPStatus.OK,
            f'/{ self.author.username }/{ self.post.id }/': HTTPStatus.OK,
            f'/{ self.author.username }'
            f'/{ self.post.id }/edit/': HTTPStatus.FOUND,
            '/follow/': HTTPStatus.FOUND,
            '/about/author/': HTTPStatus.OK,
            '/about/tech/': HTTPStatus.OK,
        }
        for address, HTTPStatus.value in url_addresses.items():
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertEqual(response.status_code, HTTPStatus.value)

    def test_authorized_url(self):
        """
        Проверяется отображение страниц,
        доступных в соответствии с авторизацией.
        """
        url_addresses = {
            f'/{ self.author.username }'
            f'/{ self.post.id }/edit/': HTTPStatus.FOUND,
            '/new/': HTTPStatus.OK,
        }
        for address, HTTPStatus.value in url_addresses.items():
            with self.subTest(address=address):
                self.authorized_client.force_login(self.user)
                response = self.authorized_client.get(address)
                self.assertEqual(response.status_code, HTTPStatus.value)

    def test_url_redirect_anonymous_on_login(self):
        """Страница перенаправит анонимного
        пользователя на страницу логина.
        """
        response = self.guest_client.get('/new/', follow=True)
        self.assertRedirects(response, '/auth/login/?next=/new/')

    def test_url_redirect_edit_anonymous_on_login(self):
        """Страница перенаправит анонимного
        пользователя co страницы редактирования на страницу логина.
        """
        response = self.guest_client.get(
            f'/{ self.author.username }/{ self.post.id }/edit/',
            follow=True
        )
        self.assertRedirects(
            response,
            f'/auth/login/?next='
            f'/{ self.author.username }/{ self.post.id }/edit/'
        )

    def test_edit_post_for_author(self):
        """
        Страница редактирования доступна для
        авторизованного пользователя-автора поста.
        """
        self.authorized_client.force_login(self.author)
        response = self.authorized_client.get(
            f'/{ self.author.username }/{ self.post.id }/edit/'
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates = (self.index_url, self.group_url, self.profile_url,
                     self.post_url, self.new_post_url, self.post_edit_url)
        for template in templates:
            with self.subTest(template=template):
                self.authorized_client.force_login(self.author)
                response = self.authorized_client.get(
                    reverse(template[0],
                            args=template[2])
                )
                self.assertEqual(response.status_code, HTTPStatus.OK)
                self.assertTemplateUsed(response, template[1])

    def test_return_404(self):
        """При ошибке "404" сервер возвращает заданный шаблон"""
        response = self.guest_client.get('/404/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.assertTemplateUsed(response, 'misc/404.html')
