import os

os.environ["DJANGO_SETTINGS_MODULE"] = "movie.settings"
import django

django.setup()
from user.models import *
from math import sqrt, pow
import operator
from django.db.models import Q, Count, Subquery
from collections import defaultdict
import pickle


# from django.shortcuts import render,render_to_response
class UserCf:

    # 获得初始化数据
    def __init__(self, all_user):
        self.all_user = all_user

    # 通过用户名获得商品列表，仅调试使用
    def getItems(self, username1, username2):
        return self.all_user[username1], self.all_user[username2]

    # 计算两个用户的皮尔逊相关系数
    def pearson(self, user1, user2):  # 数据格式为：商品id，浏览此
        sum_xy = 0.0  # user1,user2 每项打分的成绩的累加
        n = 0  # 公共浏览次数
        sum_x = 0.0  # user1 的打分总和
        sum_y = 0.0  # user2 的打分总和
        sumX2 = 0.0  # user1每项打分平方的累加
        sumY2 = 0.0  # user2每项打分平方的累加
        for movie1, score1 in user1.items():
            if movie1 in user2.keys():  # 计算公共的浏览次数
                n += 1
                sum_xy += score1 * user2[movie1]
                sum_x += score1
                sum_y += user2[movie1]
                sumX2 += pow(score1, 2)
                sumY2 += pow(user2[movie1], 2)
        if n == 0:
            # print("p氏距离为0")
            return 0
        molecule = sum_xy - (sum_x * sum_y) / n  # 分子
        denominator = sqrt((sumX2 - pow(sum_x, 2) / n) * (sumY2 - pow(sum_y, 2) / n))  # 分母
        if denominator == 0:
            return 0
        r = molecule / denominator
        return r

    # 计算与当前用户的距离，获得最临近的用户
    def nearest_user(self, current_user, n=1):
        distances = {}
        # 用户，相似度
        # 遍历整个数据集
        for user, rate_set in self.all_user.items():
            # 非当前的用户
            if user != current_user:
                distance = self.pearson(self.all_user[current_user], self.all_user[user])
                # 计算两个用户的相似度
                distances[user] = distance
        closest_distance = sorted(
            distances.items(), key=operator.itemgetter(1), reverse=True
        )
        # 最相似的N个用户
        # print("closest user:", closest_distance[:n])
        return closest_distance[:n]

    # 给用户推荐商品
    def recommend(self, username, n=3):
        recommend = {}
        nearest_user = self.nearest_user(username, n)
        for user, score in dict(nearest_user).items():  # 最相近的n个用户
            for movies, scores in self.all_user[user].items():  # 推荐的用户的商品列表
                if movies not in self.all_user[username].keys():  # 当前username没有看过
                    if movies not in recommend.keys():  # 添加到推荐列表中
                        recommend[movies] = scores
        # 对推荐的结果按照商品浏览次数排序
        return sorted(recommend.items(), key=operator.itemgetter(1), reverse=True)

    # 某个用户给电影打分后，更新all_user dict
    def update_all_user(self, user):
        rates = user.rate_set.all()
        rate = {}
        # 用户有给电影打分 在rate和all_user中进行设置
        if rates:
            for i in rates:
                rate.setdefault(str(i.movie.id), i.mark)
        all_user.setdefault(user.username, rate)


def get_all_user():
    all_user = {}
    users_rate = Rate.objects.values('user').annotate(mark_num=Count('user')).order_by('-mark_num')
    user_ids = [user_rate['user'] for user_rate in users_rate]
    # user_ids.append(user_id)
    users = User.objects.filter(id__in=user_ids)
    for user in users:
        rates = user.rate_set.all()
        rate = {}
        # 用户有给电影打分 在rate和all_user中进行设置
        if rates:
            for i in rates:
                rate.setdefault(str(i.movie.id), i.mark)
            all_user.setdefault(user.username, rate)
        else:
            # 用户没有为电影打过分，设为0
            all_user.setdefault(user.username, {})
    print('user_recommend initial finished')
    return all_user


# 入口函数
def recommend_by_user_id(user_id):
    user_prefer = UserTagPrefer.objects.filter(user_id=user_id).order_by('-score').values_list('tag_id', flat=True)
    current_user = User.objects.get(id=user_id)
    # 如果当前用户没有打分 则看是否选择过标签，选过的话，就从标签中找
    # 没有的话，就按照浏览度推荐15个
    if current_user.rate_set.count() == 0:
        if len(user_prefer) != 0:
            movie_list = Movie.objects.filter(tags__in=user_prefer)[:15]
        else:
            movie_list = Movie.objects.order_by("-num")[:15]
        return movie_list
    import random
    recommend_list = [each[0] for each in user_cf.recommend(current_user.username, 15)]
    movie_list = list(Movie.objects.filter(id__in=recommend_list))[:15]
    random.shuffle(movie_list)
    other_length = 15 - len(movie_list)
    if other_length > 0:
        fix_list = Movie.objects.filter(~Q(rate__user_id=user_id)).order_by('-num')
        for fix in fix_list:
            if fix not in movie_list:
                movie_list.append(fix)
            if len(movie_list) >= 15:
                break
    return movie_list


# item_based

class ItemBasedCF:
    # 初始化参数
    def __init__(self):
        # 找到相似的20部电影，为目标用户推荐10部电影
        self.n_sim_movie = 100
        self.n_rec_movie = 15

        # 用户相似度矩阵
        self.movie_sim_matrix = defaultdict(lambda: defaultdict(float))
        # 物品共现矩阵
        self.cooccur = defaultdict(lambda: defaultdict(int))
        self.movie_popular = defaultdict(int)
        self.movie_count = 0
        print('Similar user number = %d' % self.n_sim_movie)
        print('Recommended user number = %d' % self.n_rec_movie)
        self.calc_movie_sim()

    # 计算电影之间的相似度
    def calc_movie_sim(self):
        model_path = 'item_rec.pkl'
        # 已有的话，就不重新计算
        # try:
        # 重新计算
        # except FileNotFoundError:
        users = User.objects.all()
        for user in users:
            movies = Rate.objects.filter(user=user).values_list('movie_id', flat=True)
            for movie in movies:
                self.movie_popular[movie] += 1
        self.movie_count = len(self.movie_popular)
        print("Total user number = %d" % self.movie_count)
        for user in users:
            movies = Rate.objects.filter(user=user).values_list('movie_id', flat=True)
            for m1 in movies:
                for m2 in movies:
                    if m1 == m2:
                        continue
                    self.cooccur[m1][m2] += 1
                    # self.movie_sim_matrix[m1][m2] += 1
        print("Build co-rated users matrix success!")
        # 计算电影之间的相似性
        print("Calculating user similarity matrix ...")
        for m1, related_movies in self.cooccur.items():
            for m2, count in related_movies.items():
                # 注意0向量的处理，即某电影的用户数为0
                if self.movie_popular[m1] == 0 or self.movie_popular[m2] == 0:
                    self.movie_sim_matrix[m1][m2] = 0
                else:
                    # 根据公式计算w[i][j]
                    self.movie_sim_matrix[m1][m2] = count / sqrt(self.movie_popular[m1] * self.movie_popular[m2])
                    print('Calculate user similarity matrix success!')
        # 保存模型
        with open(model_path, 'wb')as opener:
            pickle.dump(dict(self.movie_sim_matrix), opener)
        print('保存模型成功!')

    # 针对目标用户U，找到K部相似的电影，并推荐其N部电影
    def recommend(self, user_id):
        K = self.n_sim_movie
        N = self.n_rec_movie
        rank = defaultdict(int)
        # user = User.objects.get(id=user_id)
        watched_movies = Rate.objects.filter(user_id=user_id).values_list('movie_id', 'mark')
        print('this is watched movies', watched_movies)
        watched_ids = [w[0] for w in watched_movies]
        try:
            for movie, rating in watched_movies:
                for related_movie, w in sorted(self.movie_sim_matrix[movie].items(), key=operator.itemgetter(1), reverse=True)[:K]:
                    # print('this is related', related_movie)
                    if related_movie in watched_ids:
                        continue
                    rank[related_movie] += w * float(rating)
        except KeyError:
            self.calc_movie_sim()
            return self.recommend(user_id)
        return sorted(rank.items(), key=operator.itemgetter(1), reverse=True)[:N]


# 在评分后去更新相似度矩阵
def update_item_movie_sim_matrix(movie_id, user_id):
    # 更新电影被喜欢的num
    item_cf.movie_popular[movie_id] += 1
    # 更新movie_sim_matrix
    movies = Rate.objects.filter(user_id=user_id).values_list('movie_id', flat=True)
    for m1 in movies:
        if m1 == movie_id:
            continue
        #     更新共现矩阵
        item_cf.cooccur[m1][movie_id] += 1
        item_cf.cooccur[movie_id][m1] += 1
    # 重新计算相似度矩阵
    for movie1_id, count in item_cf.cooccur[movie_id].items():
        if item_cf.movie_popular[movie1_id] == 0 or item_cf.movie_popular[movie_id] == 0:
            item_cf.movie_sim_matrix[movie_id][movie1_id] = 0
        else:
            # 根据公式计算w[i][j]
            # 更新相似度矩阵
            value = count / sqrt(item_cf.movie_popular[movie1_id] * item_cf.movie_popular[movie_id])
            item_cf.movie_sim_matrix[movie1_id][movie_id] = value
            item_cf.movie_sim_matrix[movie_id][movie1_id] = value
            print('update user similarity matrix success!')

    # 在更新完成后重新写入本地
    with open('item_rec.pkl', 'wb')as opener:
        pickle.dump(dict(item_cf.movie_sim_matrix), opener)
    print('保存更新成功!')


# 计算相似度
def similarity(movie1_id, movie2_id):
    movie1_set = Rate.objects.filter(movie_id=movie1_id)
    # movie1的打分用户数
    movie1_sum = movie1_set.count()
    # movie_2的打分用户数
    movie2_sum = Rate.objects.filter(movie_id=movie2_id).count()
    # 两者的交集
    common = Rate.objects.filter(user_id__in=Subquery(movie1_set.values('user_id')), movie=movie2_id).values('user_id').count()
    # 没有人给当前电影打分
    if movie1_sum == 0 or movie2_sum == 0:
        return 0
    similar_value = common / sqrt(movie1_sum * movie2_sum)
    return similar_value


#
def recommend_by_item_id(user_id, k=15):
    # 前三的tag
    user_prefer = UserTagPrefer.objects.filter(user_id=user_id).order_by('-score').values_list('tag_id', flat=True)
    user_prefer = list(user_prefer)[:3]
    current_user = User.objects.get(id=user_id)
    # 如果当前用户没有打分 则看是否选择过标签，选过的话，就从标签中找
    # 没有的话，就按照浏览度推荐15个
    if current_user.rate_set.count() == 0:
        if len(user_prefer) != 0:
            movie_list = Movie.objects.filter(tags__in=user_prefer)[:15]
        else:
            movie_list = Movie.objects.order_by("-num")[:15]
        print('from here')
        return movie_list
    # most_tags = Tags.objects.annotate(tags_sum=Count('name')).order_by('-tags_sum').filter(movie__rate__user_id=user_id).order_by('-tags_sum')
    # 选用户最喜欢的标签中的电影，用户没看过的30部，对这30部电影，计算距离最近
    un_watched = Movie.objects.filter(~Q(rate__user_id=user_id), tags__in=user_prefer).order_by('?')[:30]  # 看过的电影
    watched = Rate.objects.filter(user_id=user_id).values_list('movie_id', 'mark')
    distances = []
    names = []
    # 在未看过的电影中找到
    # 后续改进，选择top15
    for un_watched_movie in un_watched:
        for watched_movie in watched:
            if un_watched_movie not in names:
                names.append(un_watched_movie)
                distances.append((similarity(un_watched_movie.id, watched_movie[0]) * watched_movie[1], un_watched_movie))
    distances.sort(key=lambda x: x[0], reverse=True)
    print('this is distances', distances[:15])
    recommend_list = []
    for mark, movie in distances:
        if len(recommend_list) >= k:
            break
        if movie not in recommend_list:
            recommend_list.append(movie)
    # print('this is recommend list', recommend_list)
    # 如果得不到有效数量的推荐 按照未看过的电影中的热度进行填充
    print('recommend list', recommend_list)
    return recommend_list


import sys

all_user = get_all_user()
user_cf = UserCf(all_user=all_user)
if 'runserver' in sys.argv:
    # 在django启动时计算矩阵
    item_cf = ItemBasedCF()
