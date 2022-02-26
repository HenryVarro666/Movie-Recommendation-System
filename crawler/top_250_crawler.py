import asyncio

import aiohttp
from bs4 import BeautifulSoup

base_url = 'https://movie.douban.com/top250'
results = {}
new_url = 'https://www.douban.com/doulist/30299/?start=0&sort=seq&playable=0&sub_type='
ids = 0
import csv

tasks = []


class Movie:
    def __init__(self, id, title, description, star, leader, tags, years, country, director_description, image_link):
        self.id = id
        self.star = star
        self.description = description
        self.title = title
        self.leader = leader
        self.tags = tags
        self.years = years
        self.country = country
        self.director_description = director_description
        self.image_link = image_link


async def fetch(url):
    async with aiohttp.ClientSession()as session:
        async with session.get(url) as response:
            assert response.status == 200
            return await response.text()


async def write_images(image_link, image_name):
    print('write images....', image_link)
    async with aiohttp.ClientSession()as session:
        async with session.get(image_link) as response:
            assert response.status == 200
            with open('movie_images/' + image_name + '.png', 'wb')as opener:
                while True:
                    chunk = await response.content.read(1024)
                    if not chunk:
                        break
                    opener.write(chunk)


async def parse_list(html):
    soup = BeautifulSoup(html, 'html.parser')
    movies = soup.find_all('div', {'class': 'doulist-item'})
    movie_list = []

    for movie in movies:
        try:
            title = movie.find('div', {'class': 'title'}).text.strip().replace('/', '_')
        except Exception as e:
            print(movie)
            print(e)
            continue
        try:
            image_link = movie.find('div', {'class': 'post'}).find('img')
            if image_link is None:
                continue
            else:
                image_link = image_link['src']
                await write_images(image_link, title)
            rate = movie.find('div', {'class': 'rating'})
            dou_rate = rate.find('span', {'class': 'rating_nums'})
            if dou_rate is None:
                dou_rate = '0'
            else:
                dou_rate = dou_rate.text
            # rate_num = rate.find_all('span')[-1].text
            abstract = movie.find('div', {'class': 'abstract'}).text.strip().split('\n')
            tags = country = leader = year = director_ = ''
            for ab in abstract:
                if len(ab.strip()) == 0:
                    continue
                ab_list = ab.split(':')
                key = ab_list[0].strip()
                value = ab_list[1].strip()
                if key == '导演':
                    director_ = value
                elif key == '主演':
                    leader = value
                elif key == '年份':
                    year = value
                elif key == '制片国家/地区':
                    country = value
                elif key == '类型':
                    tags = value
        except Exception as e:
            print(movie)
            raise e
        global ids
        ids += 1
        movie_list.append(Movie(image_link=image_link, title=title, star=dou_rate, leader=leader, tags=tags, country=country, director_description=director_, years=year, id=ids, description=''))
    new_link = soup.find('span', {'class': 'next'})
    if new_link is not None:
        try:
            new_link = new_link.a['href']
        except Exception:
            new_link = None
    return movie_list, new_link


async def parse_250(html):
    soup = BeautifulSoup(html, 'html.parser')
    movies_info = soup.find('ol', {'class': 'grid_view'})
    movies = []
    for movie_info in movies_info.find_all('li'):
        pic = movie_info.find('div', {'class': 'image_link'})
        picture_url = pic.find('img').attrs['src']
        movie_id = pic.find('em').text
        url = movie_info.find('div', {"class": "info"})
        title = url.find('span', {'class': 'title'}).text
        # 保存图片文件到本地
        print('write image ', picture_url)
        await write_images(picture_url, title)
        info = url.find('div', {'class': 'bd'})
        movie_detail = info.find('p')
        quote = info.find('p', {'class': 'quote'})
        if quote is not None:
            description = quote.find('span').text
        else:
            description = ''
            print(title + 'description is None')
        star = info.find('div', {"class": 'star'}).find('span', {'class': 'rating_num'}).text
        tags = movie_detail.text.strip().split('\n')[-1].split('/')[-1].split(' ')
        tags = [tag.strip() for tag in tags]
        years = movie_detail.text.strip().split('\n')[-1].split('/')[0].strip()
        country = movie_detail.text.strip().split('\n')[-1].split('/')[1].strip()
        temp = movie_detail.text.strip().split('\n')
        try:
            director_description = temp[0].split('/')[0].strip().split('\xa0')[0].split(':')[1]
        except IndexError:
            director_description = ''
        try:
            leader = temp[0].split('/')[0].strip().split('\xa0')[-1].split(':')[1]
        except IndexError:
            leader = ''
        assert title is not None
        assert star is not None
        assert leader is not None
        assert years is not None
        assert country is not None
        assert director_description is not None
        assert tags is not None
        assert picture_url is not None
        assert movie_id is not None
        movies.append(Movie(title=title, description=description, star=star, leader=leader, years=years, country=country, director_description=director_description, tags=tags, image_link=picture_url,
                            id=movie_id
                            )
                      )
    next_page = soup.find('link', {'rel': 'next'})
    if next_page is not None and next_page.attrs.get('href'):
        next_link = base_url + next_page.attrs['href']
    else:
        print('finished!')
        next_link = None
    return movies, next_link


def write_movies(movies):
    print('write movies..')
    with open('movies_2.csv', 'a+')as opener:
        writer = csv.writer(opener)
        if opener.tell() == 0:
            writer.writerow(['id', 'title ', 'image_link ', 'country ', 'years ', 'director_description', 'leader', 'star ', 'description', 'tags'])
        for movie in movies:
            writer.writerow([str(movie.id), movie.title, movie.image_link, movie.country, movie.years, movie.director_description, movie.leader, movie.star, movie.description, '/'.join(movie.tags)])


async def parse_movie_link(url):
    content = await fetch(url)
    soup = BeautifulSoup(content, 'html.parser')
    movies_info = soup.find('ol', {'class': 'grid_view'})
    for movie_info in movies_info.find_all('li'):
        url = movie_info.find('div', {"class": "info"}).find('div', {'class': 'hd'}).find('a')['href']
        print('write', url)
        with open('top250_link.csv', 'a+')as opener:
            opener.write(url + '\n')


def get_movie_link_event_loop():
    loop = asyncio.get_event_loop()
    base_url = 'https://movie.douban.com/top250?start={}&filter='
    for i in range(0, 250, 25):
        url = base_url.format(i)
        print('add url to queue', url)
        tasks.append(parse_movie_link(url))
    loop.run_until_complete(asyncio.wait(tasks))


get_movie_link_event_loop()
