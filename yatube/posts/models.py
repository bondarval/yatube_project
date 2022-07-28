from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class Group(models.Model):
    title = models.CharField("Название группы", max_length=200)
    slug = models.SlugField("Сокращенное название группы", unique=True)
    description = models.TextField("Описание группы")

    def __str__(self) -> str:
        return self.title


class Post(models.Model):
    text = models.TextField(
        "Текст сообщения",
        help_text="Введите свое сообщение тут"
    )
    pub_date = models.DateTimeField("date published", auto_now_add=True)
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name="Автор",
        related_name="posts"
    )
    group = models.ForeignKey(
        Group,
        on_delete=models.SET_NULL,
        verbose_name="Группа",
        related_name="group",
        blank=True,
        null=True
    )
    image = models.ImageField(upload_to='posts/', blank=True, null=True)

    def __str__(self) -> str:
        return self.text[:15]


class Comment(models.Model):
    text = models.TextField(
        "Текст комментария",
        help_text="Оставьте свой комментарий",
        blank=False
    )
    created = models.DateTimeField("date published", auto_now_add=True)
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name="Автор комментария",
        related_name="comments"
    )
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        verbose_name="Комментируемое сообщение",
        related_name="comments"
    )

    class Meta:
        ordering = ['created']

    def __str__(self) -> str:
        return self.text


class Follow(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name="Пользователь",
        related_name="follower"
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name="Автор сообщений",
        related_name="following"
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'author'],
                name='unique_follow'
            ),
        ]

    def __str__(self) -> str:
        return f'{self.user} подписан на {self.author}'
