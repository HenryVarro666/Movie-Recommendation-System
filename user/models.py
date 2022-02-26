from django.db import models
from django.db.models import Avg


class User(models.Model):
    username = models.CharField(max_length=255, unique=True, verbose_name="Account")
    password = models.CharField(max_length=255, verbose_name="Password")
    email = models.EmailField(verbose_name="Mailbox")

    class Meta:
        verbose_name_plural = "User"
        verbose_name = "User"

    def __str__(self):
        return self.username


class Tags(models.Model):
    name = models.CharField(max_length=255, verbose_name="Tag", unique=True)

    class Meta:
        verbose_name = "Tag"
        verbose_name_plural = "Tag"

    def __str__(self):
        return self.name


class UserTagPrefer(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, blank=True, verbose_name="User id",
    )
    tag = models.ForeignKey(Tags, on_delete=models.CASCADE, verbose_name='Tag')
    score = models.FloatField(default=0)

    class Meta:
        verbose_name = "User Preference"
        verbose_name_plural = "Preference"

    def __str__(self):
        return self.user.username + str(self.score)


class Movie(models.Model):
    tags = models.ManyToManyField(Tags, verbose_name='tag', blank=True)
    collect = models.ManyToManyField(User, verbose_name="Collector", blank=True)
    name = models.CharField(verbose_name="Movie Name", max_length=255, unique=True)
    director = models.CharField(verbose_name="Director's Name", max_length=255)
    country = models.CharField(verbose_name="Country", max_length=255)
    years = models.DateField(verbose_name='Release Time')
    leader = models.CharField(verbose_name="Actors", max_length=1024)
    d_rate_nums = models.IntegerField(verbose_name="Douban rating number")
    d_rate = models.CharField(verbose_name="Douban rating", max_length=255)
    intro = models.TextField(verbose_name="Descriptions")
    num = models.IntegerField(verbose_name="Views", default=0)
    origin_image_link = models.URLField(verbose_name='Douban Pictures Link', max_length=255, null=True)
    image_link = models.FileField(verbose_name="Cover pic", max_length=255, upload_to='movie_cover')
    imdb_link = models.URLField(null=True)
    douban_link = models.URLField(verbose_name='Douban Link')
    douban_id = models.CharField(verbose_name='Douban id',max_length=128,null=True)

    @property
    def movie_rate(self):
        movie_rate = Rate.objects.filter(movie_id=self.id).aggregate(Avg('mark'))['mark__avg']
        return movie_rate or 'Nothing'

    class Meta:
        verbose_name = "Name"
        verbose_name_plural = "Name"

    def __str__(self):
        return self.name


class Rate(models.Model):
    movie = models.ForeignKey(
        Movie, on_delete=models.CASCADE, blank=True, null=True, verbose_name="Movie id"
    )
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, blank=True, null=True, verbose_name="User id",
    )
    mark = models.FloatField(verbose_name="Rating")
    create_time = models.DateTimeField(verbose_name="Release Time", auto_now_add=True)

    @property
    def avg_mark(self):
        average = Rate.objects.all().aggregate(Avg('mark'))['mark__avg']
        return average

    class Meta:
        verbose_name = "Rating Information"
        verbose_name_plural = verbose_name


class Comment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="User")
    content = models.CharField(max_length=255, verbose_name="Content")
    create_time = models.DateTimeField(auto_now_add=True)
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, verbose_name="Movie")

    class Meta:
        verbose_name = "comment"
        verbose_name_plural = verbose_name


class LikeComment(models.Model):
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, verbose_name='comment')
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='User')

    class Meta:
        verbose_name = "Click Like"
        verbose_name_plural = verbose_name
