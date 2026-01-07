
from datetime import datetime, timedelta
from flask import Flask, render_template
from api import get_news_data, process_single_article

app = Flask(__name__)

# Simple in-memory cache
cache = {
    "data": None,
    "last_updated": None
}

def refresh_news():
    """Logic to refresh news only when needed."""
    print("Updating news via API and LLM...")
    raw_articles = get_news_data(count=5)
    processed_list = []

    for art in raw_articles:
        result = process_single_article(art)
        if result:
            processed_list.append(result)

    cache["data"] = processed_list
    cache["last_updated"] = datetime.now()
    return processed_list


@app.route('/')
def index():
    # Check if cache exists and is less than 1 hour old
    if cache["data"] and (datetime.now() - cache["last_updated"]).seconds < 3600:
        return render_template('index.html', data=cache["data"])

    # Otherwise, update the cache
    news_data = refresh_news()
    return render_template('index.html', data=news_data)


if __name__ == '__main__':
    app.run(debug=True, port=8080)