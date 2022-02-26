from rest_framework import serializers

from user.models import Rate, Movie, Comment


class RateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rate

    def to_representation(self, instance):
        return {'电影名': instance.movie.name, '评分': instance.mark, '创建时间': instance.create_time.strftime('%Y-%m-%d %H:%M:%S')}


class CommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment

    def to_representation(self, instance):
        return {'电影名': instance.movie.name, 'comment': instance.content, '创建时间': instance.create_time.strftime('%Y-%m-%d %H:%M:%S'), '点赞数': instance.likecomment_set.count()}


class CollectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Movie

    def to_representation(self, instance):
        return {'电影名': instance.name, '导演': instance.director, '上映时间': instance.years, '浏览量': instance.num}


class MovieSerializer(serializers.ModelSerializer):
    class Meta:
        model = Movie
        fields = ['name', 'image_link', 'id', 'years', 'd_rate', 'director']
