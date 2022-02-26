# Create your views here.
import random

from django.core.cache import cache
from django.db.models import Count
from rest_framework.decorators import api_view
from rest_framework.response import Response

from api.serializers import *
from cache_keys import USER_CACHE
from recommend_movies import recommend_by_user_id, recommend_by_item_id
from user.models import Rate, Movie, Comment, User


@api_view(['GET'])
def rate_detail(request, user_id):
    rate = Rate.objects.filter(user_id=user_id)
    # a=Rate.objects.first()
    serializer = RateSerializer(rate, many=True)
    return Response(serializer.data)


@api_view(['GET'])
def collect_detail(request, user_id):
    user = User.objects.get(id=user_id)
    collect_movies = user.movie_set.all()
    serializer = CollectSerializer(collect_movies, many=True)
    return Response(serializer.data)


@api_view(['GET'])
def comment_detail(request, user_id):
    rate = Comment.objects.filter(user_id=user_id)
    serializer = CommentSerializer(rate, many=True)
    return Response(serializer.data)


@api_view(['GET'])
def user_recommend(request, user_id=None):
    if user_id is None:
        movie_list = Movie.objects.order_by('?')
    else:
        cache_key = USER_CACHE.format(user_id=user_id)
        movie_list = cache.get(cache_key)
        if movie_list is None:
            movie_list = recommend_by_user_id(user_id)
            cache.set(cache_key, movie_list, 60 * 5)
            print('设置缓存')
        else:
            print('缓存命中!')
    movie_list = list(movie_list)
    random.shuffle(movie_list)
    serializer = MovieSerializer(movie_list, many=True)
    return Response(serializer.data)


@api_view(['GET'])
def item_recommend(request, user_id=None):
    if user_id is None:
        movie_list = Movie.objects.order_by('?')
    else:
        cache_key = USER_CACHE.format(user_id=user_id)
        movie_list = cache.get(cache_key)
        if movie_list is None:
            movie_list = recommend_by_item_id(user_id)
            cache.set(cache_key, movie_list, 60 * 5)
            print('设置缓存')
        else:
            print('缓存命中!')
    movie_list = list(movie_list)
    random.shuffle(movie_list)
    serializer = MovieSerializer(movie_list, many=True)
    return Response(serializer.data)


@api_view(['GET'])
def hotest_movie(request):
    movies = Movie.objects.annotate(user_collector=Count('collect')).order_by('-user_collector')[:10]
    serializer = MovieSerializer(movies, many=True)
    return Response(serializer.data)
