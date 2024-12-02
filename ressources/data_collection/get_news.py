# this file is running every 4 hours currently
from sqlalchemy import create_engine, text
import requests
from bs4 import BeautifulSoup
import pandas as pd

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from keys import aiven_pwd 

sql_engine = create_engine(f"mysql+pymysql://avnadmin:{aiven_pwd}@mysql-nfl-mhoffmann-nfl.b.aivencloud.com:10448/nfl", pool_size=20, max_overflow=50)

def get_existing_ids(sql_engine, table, id_column):
    result = sql_engine.connect().execute(text(f"SELECT {id_column} FROM {table}"))
    df = pd.DataFrame(result.fetchall(), columns=[id_column])
    if df.empty:
        return set()  # Return an empty set if no rows are found
    return set(df[id_column].tolist())

def append_new_rows(dataframe, table, sql_engine, id_column):
    existing_ids_set = get_existing_ids(sql_engine, table, id_column)
    if not existing_ids_set:  # If there are no existing IDs in the SQL table
        dataframe.to_sql(table, con=sql_engine, if_exists='append', index=True, index_label=id_column)
    else:
        new_rows = dataframe[~dataframe.index.isin(existing_ids_set)]
        new_rows.to_sql(table, con=sql_engine, if_exists='append', index=True, index_label=id_column)

def get_news():
    urls = ["https://site.api.espn.com/apis/site/v2/sports/football/nfl/news?limit=150",
            "https://now.core.api.espn.com/v1/sports/news?limit=1000&sport=football",
            "https://site.api.espn.com/apis/site/v2/sports/football/nfl/news?team="]  # needs team_id
    existing_news = get_existing_ids(sql_engine, "news", "news_id")
    news = []
    article_links = set()
    try:
        news_response = requests.get(urls[0])
        news_data = news_response.json()
        articles_data = news_data.get('articles', [])
        for article_i in articles_data:
            article_link = article_i.get('links', {}).get('api', {}).get('news', {}).get('href', '')
            article_links.add(article_link)
            article_link = article_i.get('links', {}).get('api', {}).get('self', {}).get('href', '')
            article_links.add(article_link)
    except Exception as e:
        print(e)
    #article_links.add(urls[1])
    for team_id in range(1,35):
        try:
            news_response = requests.get(urls[2]+str(team_id))
            news_data = news_response.json()
            articles_data = news_data.get('articles', [])
            for article_i in articles_data:
                article_link = article_i.get('links', {}).get('api', {}).get('news', {}).get('href', '')
                article_links.add(article_link)
                article_link = article_i.get('links', {}).get('api', {}).get('self', {}).get('href', '')
                article_links.add(article_link)
        except Exception as e:
            print(e)
    cleaned_links = []
    for i in article_links:
        if ('sports/news' in i):
            cleaned_links.append(i)
    for article_link in cleaned_links:
        try:
            article_response = requests.get(article_link)
            article_data = article_response.json()
            headlines_data = article_data.get('headlines', [])
            for headline_i in headlines_data:
                headline_id = headline_i.get('id', None)
                if ( (not headline_id == None)and(not headline_id in existing_news) ):
                    new_news = {}
                    new_news['news_id'] = headline_id
                    new_news['headline'] = headline_i.get('headline', None)
                    new_news['description'] = headline_i.get('description', None)
                    new_news['published'] = headline_i.get('published', None)
                    story = headline_i.get('story', None)
                    story_soup = BeautifulSoup(story, 'html.parser')
                    story_plain = story_soup.get_text(separator=' ', strip=True)
                    new_news['story'] = story_plain
                    news.append(new_news)
        except Exception as e:
            print(e)
    if len(news)>0:
        news_df = pd.DataFrame(news)
        news_df['news_id'] = news_df['news_id'].astype('Int64')
        news_df.set_index('news_id', inplace=True)
        news_df['published'] = pd.to_datetime(news_df['published'])
        news_df = news_df.loc[~news_df.index.duplicated()]
        append_new_rows(news_df, 'news', sql_engine, 'news_id')
    else:
        print("No new news yet.")

get_news()


