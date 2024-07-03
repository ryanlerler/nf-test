import os
import json
import asyncio
import aiohttp
from openai import OpenAI
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

api_key = os.environ.get("OPENAI_API_KEY")

client = OpenAI(api_key=api_key)

with open('feeds.json', 'r', encoding='utf-8') as file:
    news_database = json.load(file)


async def expand_article_summary(session, article, topic):
    prompt = f"""
    You are creating content for a podcast about {topic}. Based on the following news article title and summary, create an expanded version that provides more depth and details. The expanded version should be about 2-3 paragraphs long, maintain a neutral, informative tone, and be relevant to the podcast topic.

    Podcast Topic: {topic}
    Article Title: {article['title']}
    Summary: {article['summary']}
    Date: {article['published']}
    Source: {article['link']}

    Please include:
    1. A brief introduction to the article's relevance to the podcast topic
    2. Key points from the original summary
    3. Any relevant background information or context
    4. Potential implications or future developments related to the podcast topic
    5. A smooth transition to the next story or a concluding remark if it is already the last article at the end of the podcast
    """

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    data = {
        "model": "gpt-3.5-turbo",
        "messages": [
            {"role": "system",
             "content": "You are a professional news writer, tasked with expanding brief news summaries into more detailed reports."},
            {"role": "user", "content": prompt}
        ]
    }

    async with session.post("https://api.openai.com/v1/chat/completions", headers=headers, json=data) as response:
        if response.status == 200:
            result = await response.json()
            return result['choices'][0]['message']['content']
        else:
            return "Failed to generate expanded summary."


async def create_podcast_script(topic):
    if not news_database:
        print("No articles loaded from the news database.")
        return ""

        # Limit the number of articles to fit the 3 to 5 minutes duration
    max_articles = 5
    limited_news_database = news_database[:max_articles]

    script = f"Welcome to today's {topic} podcast. Here are the top stories for {datetime.now().strftime('%B %d, %Y')}.\n\n"

    async with aiohttp.ClientSession() as session:
        tasks = []
        for article in limited_news_database:
            tasks.append(expand_article_summary(session, article, topic))

        expanded_summaries = await asyncio.gather(*tasks)

        for article, expanded_summary in zip(limited_news_database, expanded_summaries):
            script += f"{article['title']}\n{expanded_summary}\n\n"

    script += "That's all for today's briefing. Thank you for listening, and we'll see you next time."

    return script


topic = "Today's Business Brief"
podcast_script = asyncio.run(create_podcast_script(topic))
if podcast_script:
    print(podcast_script)
else:
    print("Failed to generate podcast script.")
