import feedparser
import json


def fetch_news(rss):
    feed = feedparser.parse(rss)

    # print(feed)
    # print(feed.keys())
    # print(feed.entries) -> list of dicts

    feed_dicts_list = []

    for entry in feed.entries:
        # print(entry)
        # print(entry.keys())

        # for i in entry.get('tags', []):
        #     print(entry.tags)

        feed_dicts_list.append(
            {
                'title': entry.title,
                'link': entry.link,
                'summary': entry.summary,
                'author': entry.author,
                'published': entry.published,
                'tags': [tag['term'] for tag in entry.get('tags', [])]
            }
        )

    # print(feed_dicts_list)

    with open('feeds.json', 'w', encoding='utf-8') as file:
        json.dump(feed_dicts_list, file, indent=2, ensure_ascii=False)


fetch_news('https://rss.nytimes.com/services/xml/rss/nyt/World.xml')
