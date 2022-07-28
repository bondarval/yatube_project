from django import forms

from .models import Post, Comment


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        verbose_name = 'Сообщение'
        verbose_name_plural = 'Сообщения'
        fields = ['text', 'group', 'image']


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        verbose_name = 'Комментарий'
        verbose_name_plural = 'Комментарии'
        fields = ['text']
