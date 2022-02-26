import json
import logging
from functools import wraps

from django.core.cache import cache
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from rest_framework.renderers import JSONRenderer

# from als_model import als_recommend_by_user_id
from cache_keys import USER_CACHE, ITEM_CACHE, ALS_CACHE
from recommend_movies import update_item_movie_sim_matrix, user_cf
from .forms import *

logger = logging.getLogger()
logger.setLevel(level=0)


def login_in(func):  # 验证用户是否登录
    @wraps(func)
    def wrapper(*args, **kwargs):
        request = args[0]
        is_login = request.session.get("login_in")
        if is_login:
            return func(*args, **kwargs)
        else:
            return redirect(reverse("login"))

    return wrapper


def movies_paginator(movies, page):
    paginator = Paginator(movies, 8)
    if page is None:
        page = 1
    movies = paginator.page(page)
    return movies


class JSONResponse(HttpResponse):
    def __init__(self, data, **kwargs):
        content = JSONRenderer().render(data)
        kwargs["content_type"] = "application/json"
        super(JSONResponse, self).__init__(content, **kwargs)


# 登录功能
def login(request):
    if request.method == "POST":
        form = Login(request.POST)
        if form.is_valid():
            username = form.cleaned_data["username"]
            password = form.cleaned_data["password"]
            result = User.objects.filter(username=username)
            if result:
                user = User.objects.get(username=username)
                if user.password == password:
                    request.session["login_in"] = True
                    request.session["user_id"] = user.id
                    request.session["name"] = user.username
                    # 用户第一次注册，让他选标签
                    new = request.session.get('new')
                    if new:
                        tags = Tags.objects.all()
                        print('user is new', tags)
                        return render(request, 'user/choose_tag.html', {'tags': tags})
                    return redirect(reverse("index"))
                else:
                    return render(
                        request, "user/new_login.html", {"form": form, "message": "Wrong Password!"}
                    )
            else:
                return render(
                    request, "user/new_login.html", {"form": form, "message": "Account does not exist!"}
                )
    else:
        form = Login()
        return render(request, "user/new_login.html", {"form": form})


# 注册功能
def register(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)
        error = None
        if form.is_valid():
            username = form.cleaned_data["username"]
            password = form.cleaned_data["password2"]
            email = form.cleaned_data["email"]
            User.objects.create(
                username=username,
                password=password,
                email=email,
            )
            request.session['new'] = 'true'
            # 根据表单数据创建一个新的用户
            return redirect(reverse("login"))  # 跳转到登录界面
        else:
            error = form.errors
            return render(
                request, "user/register.html", {"form": form, "error": error}
            )  # 表单验证失败返回一个空表单到注册页面
    form = RegisterForm()
    return render(request, "user/register.html", {"form": form})


def logout(request):
    if not request.session.get("login_in", None):  # 不在登录状态跳转回首页
        return redirect(reverse("index"))
    request.session.flush()  # 清除session信息
    return redirect(reverse("index"))


def index(request):
    tags = Tags.objects.all()
    order = request.GET.get('order')
    tag_id = request.GET.get('tag_id')
    if tag_id is not None:
        movies = Movie.objects.filter(tags__id=tag_id)
    else:
        movies = Movie.objects.all()
    #     评分排序
    if order == '1':
        movies = movies.annotate(marks=Avg('rate__mark')).order_by('-marks')
    #    收藏排序
    elif order == '2':
        movies = movies.annotate(user_collector=Count('collect')).order_by('-user_collector')
    #     时间排序
    elif order == '3':
        movies = movies.order_by('-years')
    elif order == '4':
        movies = movies.order_by('-num')
    #     默认
    paginator = Paginator(movies, 6)
    current_page = request.GET.get("page", 1)
    movies = paginator.page(current_page)
    return render(request, 'index.html', {'tags': tags, 'movies': movies})


def search(request):  # 搜索
    if request.method == "POST":  # 如果搜索界面
        key = request.POST["search"]
        request.session["search"] = key  # 记录搜索关键词解决跳页问题
    else:
        key = request.session.get("search")  # 得到关键词
    movies = Movie.objects.filter(
        Q(name__icontains=key) | Q(intro__icontains=key) | Q(director__icontains=key)
    )  # 进行内容的模糊搜索
    page_num = request.GET.get("page", 1)
    movies = movies_paginator(movies, page_num)
    return render(request, "index.html", {"movies": movies, 'title': "Search Results"})


# 请求单个电影数据时调用的接口
def movie(request, movie_id):
    movie = Movie.objects.get(pk=movie_id)
    movie.num += 1
    movie.save()
    comments = movie.comment_set.order_by("-create_time")
    user_id = request.session.get("user_id")
    movie_rate = Rate.objects.filter(movie=movie).all().aggregate(Avg('mark'))
    if movie_rate:
        movie_rate = movie_rate['mark__avg']
    else:
        movie_rate = 0
    if user_id is not None:
        user_rate = Rate.objects.filter(movie=movie, user_id=user_id).first()
        user = User.objects.get(pk=user_id)
        is_collect = movie.collect.filter(id=user_id).first()
    return render(request, "user/details.html", locals())


@login_in
# 给电影打分 在打分的时候清除缓存
def score(request, movie_id):
    user_id = request.session.get("user_id")
    user = User.objects.get(id=user_id)
    movie = Movie.objects.get(id=movie_id)
    score = float(request.POST.get("score"))
    get, created = Rate.objects.get_or_create(user_id=user_id, movie=movie, defaults={"mark": score})
    if created:
        for tag in movie.tags.all():
            prefer, created = UserTagPrefer.objects.get_or_create(user_id=user_id, tag=tag, defaults={'score': score})
            if not created:
                # 更新分数
                prefer.score += (score - 3)
                prefer.save()
        print('create data')
        # 清理缓存
        user_cache = USER_CACHE.format(user_id=user_id)
        item_cache = ITEM_CACHE.format(user_id=user_id)
        als_cache = ALS_CACHE.format(user_id=user_id)
        cache.delete(user_cache)
        cache.delete(item_cache)
        cache.delete(als_cache)
        print('cache deleted')
        update_item_movie_sim_matrix(movie_id, user_id)
        user_cf.update_all_user(user=user)
    return redirect(reverse("movie", args=(movie_id,)))


@login_in
# 给电影进行评论
def make_comment(request, movie_id):
    user = User.objects.get(id=request.session.get("user_id"))
    movie = Movie.objects.get(id=movie_id)
    # movie.score.com += 1
    # movie.score.save()
    comment = request.POST.get("comment")
    Comment.objects.create(user=user, movie=movie, content=comment)
    return redirect(reverse("movie", args=(movie_id,)))


# 给评论点赞
@login_in
def like_comment(request, comment_id, movie_id):
    user_id = request.session.get("user_id")
    LikeComment.objects.get_or_create(user_id=user_id, comment_id=comment_id)
    return redirect(reverse("movie", args=(movie_id,)))


# 取消点赞
@login_in
def unlike_comment(request, comment_id, movie_id):
    user_id = request.session.get("user_id")
    LikeComment.objects.filter(user_id=user_id, comment_id=comment_id).delete()
    return redirect(reverse("movie", args=(movie_id,)))


@login_in
def collect(request, movie_id):
    user = User.objects.get(id=request.session.get("user_id"))
    movie = Movie.objects.get(id=movie_id)
    movie.collect.add(user)
    movie.save()
    return redirect(reverse("movie", args=(movie_id,)))


@login_in
def decollect(request, movie_id):
    user = User.objects.get(id=request.session.get("user_id"))
    movie = Movie.objects.get(id=movie_id)
    movie.collect.remove(user)
    # movie.rate_set.count()
    movie.save()
    return redirect(reverse("movie", args=(movie_id,)))


@login_in
def personal(request):
    user = User.objects.get(id=request.session.get("user_id"))
    if request.method == "POST":
        form = Edit(instance=user, data=request.POST)
        if form.is_valid():
            form.save()
            return render(
                request, "personal.html", {"message": "Modified successfully!", "form": form}
            )
        else:
            return render(
                request, "personal.html", {"message": "Failure to modify", "form": form}
            )
    form = Edit(instance=user)
    return render(request, "personal.html", {"user": user, 'form': form})


@login_in
def mycollect(request):
    user = User.objects.get(id=request.session.get("user_id"))
    movie = user.movie_set.all()
    return render(request, "user/mycollect.html", {"item": movie})


@login_in
def myjoin(request):
    user_id = request.session.get("user_id")
    user = User.objects.get(id=user_id)
    user_actions = user.action_set.all()
    return render(request, "user/myaction.html", {"item": user_actions})


@login_in
# 展示我的评论的地方
def my_comments(request):
    user = User.objects.get(id=request.session.get("user_id"))
    comments = user.comment_set.all()
    print('comment:', comments)
    return render(request, "user/my_comment.html", {"item": comments})


@login_in
def delete_comment(request, comment_id):
    Comment.objects.get(pk=comment_id).delete()
    return redirect(reverse("my_comments"))


@login_in
def my_rate(request):
    user = User.objects.get(id=request.session.get("user_id"))
    rate = user.rate_set.all()
    return render(request, "message.html", {"item": rate})


def delete_rate(request, rate_id):
    Rate.objects.filter(pk=rate_id).delete()
    return redirect(reverse("my_rate"))


# 电影的标签页面
def all_tags(request):
    tags = Tags.objects.all()
    return render(request, "user/tags.html", {"tags": tags})


@login_in
@csrf_exempt
def choose_tags(request):
    tags_name = json.loads(request.body)
    user_id = request.session.get('user_id')
    for tag_name in tags_name:
        tag = Tags.objects.filter(name=tag_name.strip()).first()
        UserTagPrefer.objects.create(tag_id=tag.id, user_id=user_id, score=5)
    # request.session.pop('new')
    return redirect(reverse("index"))


@login_in
def clear_cache(request):
    cache.clear()
    return redirect(reverse('index'))
