import os
import random

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "movie.settings")

django.setup()
strs = 'abcdefghijk_mnopqrstuvwxyz'
from user.models import *


# 随机生成username
def random_user_name(length=5):
    return ''.join(random.choices(strs, k=length))


def random_phone():
    res = ''.join([str(random.randint(0, 9)) for _ in range(11)])
    return res


def random_movie_id(num=5):
    book_nums = Movie.objects.all().order_by('?').values('id')[:num]
    print(book_nums)
    return [book['id'] for book in book_nums]


def random_mark():
    return random.randint(1, 5)


def populate_user_rating(user_numbers):
    for i in range(user_numbers):
        user_name = random_user_name()
        print(user_name)
        try:
            user, created = User.objects.get_or_create(username=user_name,
                                                       defaults={'password': user_name, "email": random_user_name() + '@163.com'})
            for movie_id in random_movie_id():
                Rate.objects.get_or_create(user=user, movie_id=movie_id, defaults={"mark": random_mark()})
        except Exception as e:
            raise e


def populate_rating(rating_number=100):
    user = User.objects.order_by('?').first()
    num = 0
    while num < rating_number:
        for movie_id in random_movie_id():
            num += 1
            try:
                rate = Rate.objects.create(user=user, movie_id=movie_id, mark=random_mark())
                print(rate, 'rate success')
            except Exception:
                pass

    # for i in range(user_numbers):
    #         user, created = User.objects.get_or_create(username=user_name,
    #                                                    defaults={'password': user_name, "email": random_user_name() + '@163.com'})
    #         for movie_id in random_movie_id():
    #             Rate.objects.get_or_create(user=user, movie_id=movie_id, defaults={"mark": random_mark()})
    #     except Exception as e:
    #         raise e


if __name__ == '__main__':
    # random_movie_id()
    # 随机生成用户打分 参数为生成数量
    populate_user_rating(200)
    populate_rating()
