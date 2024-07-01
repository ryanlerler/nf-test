import os
import json
import spacy

from fastapi import FastAPI
from openai import OpenAI
from dotenv import load_dotenv
from pydantic import BaseModel

load_dotenv()

nlp = spacy.load("en_core_web_sm")

def extract_entities(question):
    doc = nlp(question)
    print(doc.ents)
    entities = [ent.text.lower() for ent in doc.ents]
    return entities

class UserQuery(BaseModel):
    user_query: str


app = FastAPI()
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

with open('feeds.json', 'r', encoding='utf-8') as file:
    news_database = json.load(file)

# Possible queries:
# ONE condition
# ask for certain no of articles
# ask for articles in certain category/ies
# ask for articles published on certain day(s)

# TWO conditions
# ask for certain no of articles in certain category/ies
# ask for articles in certain category/ies published on certain day(s)
# ask for certain no of articles published on certain day(s)

# THREE conditions
# ask for certain no of articles in certain category/ies published on certain day(s)

# Out-of-scope queries
# ask for too many articles
# ask for articles out of the available category/ies
# ask for articles out of the available published dates
# ask for too many articles AND articles out of the available category/ies
# ask for too many articles AND articles out of the published dates
# ask for articles out of the available category/ies AND articles out of the published dates
# ask for anything which is not related to the news database


@app.post('/gpt')
def prompt(user_query: UserQuery):
    entities = extract_entities(user_query.user_query.lower())
    print(entities)

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