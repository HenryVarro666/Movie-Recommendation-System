import os

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "movie.settings")
django.setup()
# Read the whole text.
# Generate a word cloud image

# Display the generated image:
# the matplotlib way:

from wordcloud import WordCloud
from collections import Counter

wc = WordCloud(font_path='/System/Library/fonts/PingFang.ttc', width=800, height=600, background_color='white')

counts_all = Counter()

import pandas as pd


def generate_comment():
    files = os.listdir('comment')
    print(files)
    for file in files:
        file_id = file.split('.')[0]
        pic_dir = 'media/comment/{}.jpg'.format(file_id)
        if os.path.exists(pic_dir):
            print('exists')
            continue
        file_path = os.path.join('comment', file)
        df = pd.read_csv(file_path)
        comments = df.iloc[:, 2].dropna().tolist()
        com = ''.join(comments)
        counts_line = wc.process_text(com)
        wc.generate_from_frequencies(counts_line)
        wc.to_file(pic_dir)
        print('success', file_id)


# def generate_hotel_info():
#     import django
#     os.environ.setdefault("DJANGO_SETTINGS_MODULE", "hotel.settings")
#     from user.models import Movie
#     django.setup()
#     hotels = Movie.objects.all()
#     for hotel in hotels:
#         intro = hotel.intro
#         counts_line = wc.process_text(intro)
#         counts_all.update(counts_line)
#     wc.generate_from_frequencies(counts_all)
#     wc.to_file('media/comment.png')
#     print('generate clound success')

# for line in reader:  # Here you can also use the Cursor
#     if line[1] != '':
#         comment = line[1]
#         counts_line = wc.process_text(comment)
#         counts_all.update(counts_line)
# wc.generate_from_frequencies(counts_all)
# wc.to_file('comment.png')
# print('success')
generate_comment()
