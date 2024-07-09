import os
import json
import spacy
from fastapi import FastAPI
from openai import OpenAI
from dotenv import load_dotenv
from pydantic import BaseModel
from datetime import datetime, timedelta

load_dotenv()

nlp = spacy.load("en_core_web_sm")


class UserQuery(BaseModel):
    user_query: str


app = FastAPI()

api_key = os.environ.get("OPENAI_API_KEY")

client = OpenAI(api_key=api_key)

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

# Dictionary to map number words to their integer equivalents
number_words = {
    "zero": 0, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
    "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
    "eleven": 11, "twelve": 12, "thirteen": 13, "fourteen": 14,
    "fifteen": 15, "sixteen": 16, "seventeen": 17, "eighteen": 18,
    "nineteen": 19, "twenty": 20, "thirty": 30, "forty": 40,
    "fifty": 50, "sixty": 60, "seventy": 70, "eighty": 80, "ninety": 90,
    "hundred": 100, "thousand": 1000, "million": 1000000
}


def word_to_number(word):
    word = word.lower()
    if word in number_words:
        return number_words[word]
    return None


def text_to_number(text):
    words = text.lower().replace('-', ' ').split()
    result = 0
    current = 0
    for word in words:
        number = word_to_number(word)
        if number is not None:
            if number >= 100:
                current = 1
                current *= number
            elif current == 0:
                current = number
            else:
                current += number
        elif word == "and":
            continue
        else:
            result += current
            current = 0
    result += current
    return result


def extract_number(question):
    doc = nlp(question)
    entities = []
    for token in doc:
        if token.like_num:
            try:
                num_value = int(token.text)
            except ValueError:
                num_value = text_to_number(token.text.lower())
            if num_value is not None:
                entities.append(num_value)
    return entities


def extract_date(question):
    doc = nlp(question)
    entities = []
    today = datetime.now().date()

    for ent in doc.ents:
        if ent.label_ == "DATE":
            if ent.text.lower() == "today":
                entities.append(today.strftime("%Y-%m-%d"))
            elif ent.text.lower() == "yesterday":
                yesterday = today - timedelta(days=1)
                entities.append(yesterday.strftime("%Y-%m-%d"))
            else:
                entities.append(ent.text)

    # Check for "today" and "yesterday" if not found as entities
    if "today" in question.lower() and not entities:
        entities.append(today.strftime("%Y-%B-%d"))
    elif "yesterday" in question.lower() and not entities:
        yesterday = today - timedelta(days=1)
        entities.append(yesterday.strftime("%Y-%B-%d"))

    return entities


def extract_category(question):
    doc = nlp(question)
    for token in doc:
        if token.pos_ == "NOUN" and token.text.lower() in [tag.lower() for news in news_database for tag in
                                                           news['tags']]:
            return token.text
    return None


def construct_specific_prompt(query, number_of_articles, date, category):
    prompt = f"Based on the following news database, "

    if number_of_articles:
        prompt += f"provide {number_of_articles} "
    else:
        prompt += "provide relevant "

    if category:
        prompt += f"{category} "

    prompt += "news articles "

    if date:
        prompt += f"published on {date} "

    prompt += f"that match the query: '{query}'. "
    prompt += "For each article, include the title, summary, URL, and publication date, in bullet-point format. "
    prompt += "If the requested information is not available, explain why."

    return prompt


def clean_and_structure_response(content):
    articles = []
    for article in content.split('\n\n-'):
        lines = article.strip().split('\n')
        if len(lines) >= 4:
            title = lines[0].strip('* ')
            summary = lines[1].strip(' *')
            url = lines[2].strip('[] ')
            try:
                date = lines[3].split(': ')[1]
            except IndexError:
                date = lines[3]
            articles.append({
                'title': title,
                'summary': summary,
                'url': url,
                'published': date
            })
    return articles


@app.post('/gpt')
def prompt(user_query: UserQuery):
    number_entity = extract_number(user_query.user_query.lower())
    number_of_articles = sum(number_entity) if number_entity else None # Only correct for numbers less than 100
    print('number_of_articles: ', number_of_articles)

    date_entity = extract_date(user_query.user_query.title())
    date = date_entity[0] if date_entity else None
    print('date: ', date_entity)

    category = extract_category(user_query.user_query)

    # Construct a more specific prompt
    specific_prompt = construct_specific_prompt(user_query.user_query, number_of_articles, date, category)

    completion = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system",
             "content": f"You are an AI assistant with access to a news database. The database contains the following articles: {str(news_database)}"},
            {"role": "user",
             "content": specific_prompt},
        ]
    )

    response = completion.choices[0].message.content
    structured_response = clean_and_structure_response(response)

    return response, structured_response
