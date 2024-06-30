import os
import json

from fastapi import FastAPI
from openai import OpenAI
from dotenv import load_dotenv
from pydantic import BaseModel

load_dotenv()


class UserQuery(BaseModel):
    user_query: str


app = FastAPI()
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

with open('feeds.json', 'r', encoding='utf-8') as file:
    news_database = json.load(file)

@app.post('/gpt')
def prompt(user_query: UserQuery):
    completion = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system",
             "content": f"You are an avid news reader which has a news database in this JSON file which contains a list of news in a list of Python dictionaries: {str(news_database)}. The news database contains news title, url or link to the news, summary of the news, author of the news, publication date of the news, and tags or categories of the news. Based on the following user's requirements: {user_query.user_query}, return any relevant news from the news database JSON file given to you. If the user asks for some categories or tags of news which do not exist in the database, tell them that such news are not in the database. If the user asks for more number of news than what the database has, only return whatever relevant news the news database and/or certain tags/ categories have. If the user asks anything which is totally not relevant to the news database, tell them that this service is to help them read the news in the news database quickly and ask them to re-enter their query."},
            {"role": "user",
             "content": user_query.user_query}
        ]
    )

    return completion.choices[0]
