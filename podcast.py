import os
import json
import asyncio
import aiohttp
from openai import OpenAI
from dotenv import load_dotenv
from datetime import datetime
import spacy

load_dotenv()

nlp = spacy.load('en_core_web_sm')

api_key = os.environ.get("OPENAI_API_KEY")

client = OpenAI(api_key=api_key)

with open('feeds.json', 'r', encoding='utf-8') as file:
    news_database = json.load(file)

def extract_category(question):
    doc = nlp(question)
    query_tokens = [token.text.lower() for token in doc if token.pos_ in {"NOUN", "PROPN", "ADJ"}]

    for token in query_tokens:
        for news in news_database:
            for tag in news['tags']:
                if token in tag.lower():
                    return tag

    return None

async def expand_article_summary(session, article, topic):
    prompt = f"""
    You are creating content for a podcast about {topic}. Based on the following news article title and summary, create an expanded version that provides more depth and details. The expanded version should be about 2-3 paragraphs long, maintain a neutral, informative tone, and be relevant to the podcast topic.
    Please make sure that the entire podcast script can last at least 3 minutes up to maximum 5 minutes. Lengthen the summaries if the whole script is too short to last for at least 3 minutes. Shorten the summaries if the whole script is too long for 5 minutes.

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
    category = extract_category(topic)

    if not category:
        print(f"No relevant category found for topic: {topic}")
        return ""

    relevant_articles = [article for article in news_database if
                         any(category.lower() in tag.lower() for tag in article['tags'])]

    if not relevant_articles:
        print(f"No articles found for category: {category}")
        return ""

    script = f"Welcome to today's {topic} podcast. Here are the top stories for {datetime.now().strftime('%B %d, %Y')}.\n\n"

    async with aiohttp.ClientSession() as session:
        tasks = []
        for article in relevant_articles:
            tasks.append(expand_article_summary(session, article, topic))

        expanded_summaries = await asyncio.gather(*tasks)

        for article, expanded_summary in zip(relevant_articles, expanded_summaries):
            script += f"{article['title']}\n{expanded_summary}\n\n"

    script += "That's all for today's briefing. Thank you for listening, and we'll see you next time."

    return script


topic = "Today's politics"
podcast_script = asyncio.run(create_podcast_script(topic))
if podcast_script:
    print(podcast_script)
else:
    print("Failed to generate podcast script.")

#ToDo: refactor the codes to run all functions/ modules in main.py on a single click if possible