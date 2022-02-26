# 添加和读取数据到数据库中
import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "movie.settings")
import asyncio

import aiohttp
import pandas as pd


async def write_images(name, image_link, image_name):
    print('write images....', image_link)
    async with aiohttp.ClientSession()as session:
        async with session.get(image_link) as response:
            if response.status == 404:
                print('404', name)
            # assert response.status == 200
            with open('movie_images/' + image_name, 'wb')as opener:
                while True:
                    chunk = await response.content.read(1024)
                    if not chunk:
                        break
                    opener.write(chunk)


tasks = []


def envent_loop():
    df1 = pd.read_csv('../csv_data/movies_2000.csv')
    df2 = pd.read_csv('../csv_data/movies_250.csv')
    urls1 = df1['image_link'].tolist()
    urls2 = df2['image_link'].tolist()
    names1 = df1['title'].tolist()
    names2 = df2['title'].tolist()
    names1.extend(names2)
    urls1.extend(urls2)
    for name, url in zip(names1, urls1):
        title = url.split('/')[-1]
        if os.path.exists('movie_images/' + title):
            print('exists')
            continue
        print(url, title)
        tasks.append(write_images(name, url, title))
    loop = asyncio.get_event_loop()
    loop.run_until_complete(asyncio.wait(tasks))


if __name__ == '__main__':
    envent_loop()
