from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET

from .forms import PostForm, CommentForm
from .models import Group, Post, User, Follow


@require_GET
def index(request):
    post_list = cache.get('index_page')
    if post_list is None:
        post_list = Post.objects.all()
        cache.set('index_page', post_list, timeout=20)
    paginator = Paginator(post_list, settings.ITEMS_PER_PAGE)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(request, 'index.html', {'page': page})


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    posts = Post.objects.filter(group=group).order_by("-pub_date")
    paginator = Paginator(posts, settings.ITEMS_PER_PAGE)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(request, 'group.html', {'group': group, 'page': page})


def profile(request, username):
    author = get_object_or_404(User, username=username)
    post_list = Post.objects.filter(
        author__username=username).select_related('author')
    paginator = Paginator(post_list, settings.ITEMS_PER_PAGE)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    post_count = post_list.count()

    if request.user.is_authenticated and Follow.objects.filter(
            author=author, user=request.user
    ).exists():
        context = {
            'author': author,
            'post_count': post_count,
            'page': page,
            'following': True
        }
    else:
        context = {
            'author': author,
            'post_count': post_count,
            'page': page,
        }
    return render(request, 'profile.html', context)


def post_view(request, username, post_id):
    post_list = Post.objects.filter(
        author__username=username).select_related('author')
    post_count = post_list.count()
    author = get_object_or_404(User, username=username)
    post = get_object_or_404(post_list, id=post_id,
                             author__username=username)
    form = CommentForm(instance=None)
    comments = post.comments.select_related('author').all()
    followers_cnt = Follow.objects.filter(author=post.author).count()
    follow_cnt = Follow.objects.filter(user=post.author).count()
    context = {
        'post_count': post_count,
        'post': post,
        'comments': comments,
        'username': username,
        'author': author,
        'form': form,
        'followers_cnt': followers_cnt,
        'follow_cnt': follow_cnt,
    }
    return render(request, 'post.html', context)


@login_required
def new_post(request):
    form = PostForm(request.POST or None)
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect('index')
    return render(request, 'new.html', {'form': form, 'mode': 'create'})


@login_required
def post_edit(request, username, post_id):
    post = get_object_or_404(Post, id=post_id, author__username=username)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )
    if request.user != post.author:
        return redirect('post_view', username, post_id)
    if form.is_valid():
        post.save()
        return redirect('post_edit', username, post_id)
    return render(request, 'new.html', {'form': form, 'post': post})


@login_required
def add_comment(request, username, post_id):
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.post = post
        comment.author = request.user
        comment.save()
        return redirect(
            'post_view',
            username=post.author.username,
            post_id=post_id
        )
    return render(
        request,
        'includes/comments.html',
        {'form': form, 'username': username}
    )


def page_not_found(request, exception):
    return render(
        request,
        'misc/404.html',
        {"path": request.path},
        status=404
    )


def server_error(request):
    return render(request, "misc/500.html", status=500)


@login_required
def follow_index(request):
    username = request.user.username
    follow_posts_list = Post.objects.filter(
        author__following__user=request.user
    ).select_related('author').order_by("-pub_date")
    paginator = Paginator(follow_posts_list, settings.ITEMS_PER_PAGE)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    context = {
        'username': username,
        'page': page,
        'follow_posts_list': follow_posts_list,
    }
    return render(
        request,
        "follow.html",
        context
    )


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    username = request.user.username
    if request.user != author:
        Follow.objects.get_or_create(author=author, user=request.user)
        return redirect('index')
    context = {
        'username': username,
        'author': author,
    }
    return redirect('profile_follow', context)


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    if request.user != author:
        Follow.objects.filter(author=author, user=request.user).delete()
        return redirect('index')
    context = {
        'username': username,
        'author': author,
    }
    return redirect('profile_unfollow', context)
