import json
import requests
from datetime import datetime, timedelta
from newsapi import NewsApiClient
from bs4 import BeautifulSoup
import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()

# Setup
genai.configure(api_key=os.environ["GEMINI_API_KEY"])
system_instruction = (
        "You are a professional news reporter bot. "
        "Generate a concise summary and a headline from the provided CNN content. "
        "Ignore ads and promotions. Return ONLY a valid JSON object with keys: headline, summary, url."
    )
model = genai.GenerativeModel(
    model_name="gemini-2.5-flash-lite",  # Use a stable model for production
    system_instruction=system_instruction
)


def get_news_data(count=5):
    """Fetches URLs and Images in a single dict structure."""
    api = NewsApiClient(api_key=os.environ["NEWS_API_KEY"])
    yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')

    response = api.get_everything(from_param=yesterday, sources='cnn', language='en')
    articles = response.get('articles', [])[:count]

    # Use a dictionary to keep data paired correctly
    return [{"url": a['url'], "img": a['urlToImage']} for a in articles]


def scrape_article_text(url):
    """Scrapes a single URL and returns cleaned text."""
    try:
        res = requests.get(url, timeout=10)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, 'html.parser')
            # Target CNN specifically
            content = soup.find("div", class_='article__content')
            return content.text.strip() if content else None
    except Exception as e:
        print(f"Scrape error for {url}: {e}")
    return None


def process_single_article(article_info):
    """Processes one article through Gemini."""
    text = scrape_article_text(article_info['url'])
    if not text:
        return None

    try:
        response = model.generate_content(
            f"URL: {article_info['url']}\nText: {text}",  # Limit text length
            generation_config={"response_mime_type": "application/json"}
        )
        data = json.loads(response.text)
        data['img'] = article_info['img']
        return data
    except Exception as e:
        print(f"LLM Error: {e}")
        return None