from django.urls import path
from user import views

urlpatterns = [
    path("", views.index, name="index"),
    path("login/", views.login, name="login"),
    path("register/", views.register, name="register"),
    path("logout/", views.logout, name="logout"),
    path("movie/<int:movie_id>/", views.movie, name="movie"),
    path("score/<int:movie_id>/", views.score, name="score"),
    path("comment/<int:movie_id>/", views.make_comment, name="comment"),
    path("like_comment/<int:comment_id>/<int:movie_id>/", views.like_comment, name="like_comment"),
    path("unlike_comment/<int:comment_id>/<int:movie_id>/", views.unlike_comment, name="unlike_comment"),
    path("collect/<int:movie_id>/", views.collect, name="collect"),
    path("decollect/<int:movie_id>/", views.decollect, name="decollect"),
    path("personal/", views.personal, name="personal"),
    path("delete_comment/<int:comment_id>", views.delete_comment, name="delete_comment"),
    path("delete_rate/<int:rate_id>", views.delete_rate, name="delete_rate"),
    path("search/", views.search, name="search"),
    path("all_tags/", views.all_tags, name="all_tags"),
    path("choose_tags/", views.choose_tags, name="choose_tags"),
    path("clear_cache/", views.clear_cache, name="clear_cache"),
]
