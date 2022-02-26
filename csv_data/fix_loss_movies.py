# coding=utf-8
import pandas as pd
import requests
from bs4 import BeautifulSoup

from crawler.get_details import Movie


def parse_movie_page(html):
    soup = BeautifulSoup(html, 'html.parser')
    title = soup.find('span', {'property': 'v:itemreviewed'}).text
    image_link = soup.find('a', {'class': 'nbgnbg'}).find('img')['src']
    info = soup.find('div', {'id': 'info'})
    director = info.find_all('a', {'rel': 'v:directedBy'})
    if director is not None and len(director) > 0:
        director = director[0].text
    leader = [a.text for a in info.find_all('a', {'rel': 'v:starring'})]
    tags = [a.text for a in info.find_all('span', {'property': 'v:genre'})]
    country = info.find('span', string='制片国家/地区:').next_sibling
    language = info.find('span', string='语言:')
    if language is not None:
        language = language.next_sibling
    show_time = info.find('span', {'property': 'v:initialReleaseDate'}).text
    # time_length = info.find('span', {'property': 'v:runtime'}).text
    # imdb_link = info.find('span', string='IMDb链接:').fetchNextSiblings()[0]['href']
    description = soup.find('span', {'property': 'v:summary'})
    if description is not None:
        description = description.text
    star = soup.find('strong', {'property': 'v:average'}).text
    # comments = soup.find_all('div', {'class': 'comment-item'})
    return Movie(image_link=image_link, title=title, star=star, leader=leader, tags=tags, country=country, director_description=director, years=show_time, id=index, description=description, time_length=0, imdb_link='None', language=language)


df = pd.read_csv('movie_links.csv', header=None)
df2 = pd.read_csv('movies_3.csv')
print(df2.columns)
df2.drop(df2.columns[13], axis=1, inplace=True)

links = df.iloc[:, 0].tolist()
print(len(links))
exist_index = df2['id'].tolist()
# uuids = [l.split('/')[-2] for l in links]
# print(uuids)
# print(exist_index)
user_agent = "Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1; AcooBrowser; .NET CLR 1.1.4322; .NET CLR 2.0.50727)"

headers = {'User-Agent': user_agent}


def fetch_html(url):
    res = requests.get(url, headers=headers)
    if res.status_code == 200:
        print('fetch success!')
        return res.text

    print('error', res.status_code, url)


df3 = pd.DataFrame()
for index, value in df.iterrows():
    if index in exist_index:
        continue
    print('loss', index, value)
    url = value.loc[0]
    text = fetch_html(url)
    print('parsing ....', value)
    movie = parse_movie_page(text)
    # id,title ,image_link ,country ,years ,director_description,leader,star ,description,tags,imdb,language,time_length,Unnamed: 13,country,image_link,star,years

    data = {'id': index, 'title': movie.title, 'image_link': movie.image_link, 'country': movie.country, 'years': movie.years, 'director_description': movie.director_description, 'leader': movie.leader, 'star': movie.star, 'description': movie.description, 'tags': '/'.join(movie.tags), 'imdb': movie.imdb_link, 'language': movie.language, 'time_length': movie.time_length}
    data_list = list(data.values())
    print(data_list)
    series_obj = pd.Series(data_list,
                           index=df2.columns)
    df2 = df2.append(series_obj, ignore_index=True)
df2 = df2.sort_values(['id'])
df2.to_csv('fix_movie.csv', index=False)
