# Movie-Recommendation-System

基于django和协同过滤的电影推荐系统

## Windows版本问题：

- 可能需要手动安装restframework这个django package
- 报C++14依赖错误

https://stackoverflow.com/questions/64261546/python-cant-install-packages

安装或modify VS Studio里面的C++ build tool然后再重新安装包

---

Mac一步到位，暂没啥问题

## 运行

包在requirements.txt里面，venv或者conda都可以

```python
#安装包
pip install -r requirenments.txt
```


```python
#运行服务器
python manage.py runserver
```

本地地址：

 http://127.0.0.1:8000/

后台地址：

http://127.0.0.1:8000/admin

## 技术

### 后端

django + sqlite3

#### django的优势

https://www.runoob.com/django/django-intro.html

Django 是一个由 Python 编写的一个开放源代码的 Web 应用框架。

<u>Python 加 Django 是快速开发、设计、部署网站的最佳组合</u>

使用 Django，只要很少的代码，Python 的程序开发人员就可以轻松地完成一个正式网站所需要的大部分内容，并进一步开发出全功能的 Web 服务 Django 本身基于 MVC 模型，即 Model（模型）+ View（视图）+ Controller（控制器）设计模式，MVC 模式使后续对程序的修改和扩展简化，并且使程序某一部分的重复利用成为可能。

- 强大的数据库功能
- 自带强大的后台功能

#### Sqlite3的优势

https://www.runoob.com/sqlite/sqlite-intro.html

- 不需要一个单独的服务器进程或操作的系统（无服务器的）。
- SQLite 不需要配置，这意味着不需要安装或管理。
- 一个完整的 SQLite 数据库是存储在一个单一的跨平台的磁盘文件。
- SQLite 是非常小的，是轻量级的，完全配置时小于 400KiB，省略可选功能配置时小于250KiB。
- SQLite 是自给自足的，这意味着不需要任何外部的依赖。

### 数据

python爬虫爬豆瓣信息存储到本地csv文件

正则表达 + 八爪鱼。自己爬的话注意时间间隔，豆瓣有反爬机制容易ban ip。IP池没搞

### 架构

MVC（model-view-controller）架构

https://www.runoob.com/design-pattern/mvc-pattern.html

MVC 模式使后续对程序的修改和扩展简化，并且使程序某一部分的重复利用成为可能

![img](https://raw.githubusercontent.com/HenryVarro666/images/master/images/202202270156528.png)

![img](https://raw.githubusercontent.com/HenryVarro666/images/master/images/202202270156634.png)

### 前端

bootstrap3 css 框架 （真不熟）



## 基本功能

1. 登陆注册

2. 基于协同过滤的电影的分类，排序，搜索，排序功能。

3. 对电影进行打分，评论

4. 收藏喜爱的电影

5. 管理员后台进行管理

   ```python
   # 创建超级管理员
   python manage.py createsuperuser
   ```

6. 根据豆瓣评论生成词云

## 各个功能的实现

标签分类: 

​	数据库设计Movie通过外键关联Tags表，
电影搜索: 

​	在views.py search方法中。通过电影名，导演名，介绍去进行关键字搜索。
后台管理: 

​	通过django自带的admin后台加插件 在admins.py中注册数据库模型
推荐算法: 

​	在recommend_movies.py

- recommend_by_user_id为user-CF的入口函数
- recommend_by_item_id为item-CF的入口函数

网页显示：
前端: 

​	items.html
后端: 

​	views.py中 388行 user_recommend 传递数据到前端template
算法：

​	recommend_movies.py

## 基于启发式的协同过滤算法

recommend_movies.py

### 三个步骤：

1）收集用户偏好信息；
2）寻找相似的商品或者用户；
3）产生推荐

通过协调过滤计算和其他用户的距离，然后进行筛选。如果用户数量不足，推荐数目不够15条，就会自动从
所有未打分的电影中按照浏览数降序选一部分填充进去。

### 计算用户对未评分商品的预测分值

根据相似度计算，寻找用户u的邻居集N∈U，其中N表示邻居集，U表示用户集。然后，结合用户评分数据集，预测用户u对项i的评分

![img](https://raw.githubusercontent.com/HenryVarro666/images/master/images/202202270224851.webp)

​	s（u，u'）表示用户u和用户u'的相似度

### 基本点

1. 兴趣相近的用户可能会对同样的东西感兴趣
2. 用户可能较偏爱与其已购买的东西相类似的商品

### 基于用户的推荐

定义：用相似统计的方法得到具有相似爱好或者兴趣的相邻用户，所以称之为以用户为基础（User-based）的协同过滤或基于邻居的协同过滤(Neighbor-based Collaborative Filtering)。



1. 用户需要给电影打分。通过用户已打分的部分来计算相似度(采用<u>皮尔逊关系系数</u>或者<u>余弦相似度</u>),如果用户未打分，或者没有其他用户，则按照浏览数降序返回。

2. 通过pearson算法来计算用户之间的距离，找到距离最近的N个用户。将这些用户中已打分的电影(且要推荐的用户未看过的部分)返回。

   #### **皮尔逊相关系数**Correlation Coefficient的计算公式

   ![img](https://raw.githubusercontent.com/HenryVarro666/images/master/images/202202270221845.webp)

   #### **余弦相似度**Cosine-based Similarity的计算公式

   ![img](https://raw.githubusercontent.com/HenryVarro666/images/master/images/202202270222822.webp)

### 基于项目的推荐

1. 计算物品相似度矩阵
2. 遍历当前用户已打分的item，计算和未打分的item的相似距离。
3. 对相似距离进行排序返回

​	[推荐算法—协同过滤 - 简书](https://www.jianshu.com/p/5463ab162a58)

### 文章参考

[推荐算法—协同过滤 - 简书](https://www.jianshu.com/p/5463ab162a58)
[协同过滤和基于内容推荐有什么区别？ - 知乎](https://www.zhihu.com/question/19971859)

## 文件功能

1. api

   调用的端口

2. comment

   爬取的评论

3. crawler/ 

   爬虫文件

4. csv_data/ 

   需要爬取的数据

5. log/ 

   日志

6. media/ 

   静态文件（评论 和 电影封面）

7. movie/

   django的默认文件，负责设置的配置、url路由和部署

8. populate_data/

   1. 填充数据

      populate_movies.pypopulate_movies.py

   2. 清除数据

      clear_movies.py

   3. 更新图片

      update_pic.py

   4. 随机生成数据

      populate_user_rate.py


9. static/

   css文件和js文件保存处

10. user/

    主要文件夹，基本所有代码都在这里

    1. user/migrations/ 为自动生成的数据库迁移文件夹
    2. user/templates/ 为前端页面模板文件夹
    3. user/admins.py 为管理员后台代码 
    4. user/forms.py为前端表单代码 
    5. user/models.py为数据库orm模型 
    6. user/serializers.py为restful文件（不用管）
    7.  user/urls为路由注册文件 
    8. user/views为负责处理前端请求和与后端数据库交互的模块，也就是controller模块。

11. venv/

    虚拟环境以及包

12. cache.py 

    存放缓存的key值名称的文件（不用动）

13. db.sqlite3

    数据库文件

14. genrate_cloud.py

    生成词云的代码

15. manage.py

    运行主程序，从这里启动

16. recommend_movies.py

    推荐算法的代码

17. requirements.txt

    所需要的依赖包

18. *.mp4

    操作录屏

# 参考代码

https://github.com/Colaplusice/movie1_recommend

https://github.com/Colaplusice/movie_recommend
