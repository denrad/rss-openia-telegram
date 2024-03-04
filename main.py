from openai import OpenAI
import feedparser
import requests
import os
from dotenv import load_dotenv

RSS = [
    "https://gcheb.cap.ru/rss/news/news",
    "http://xn--80adtqegosnyo.xn--p1ai/feed",
    "https://tr.ru/taxonomy/term/59/all/feed",
]
NEWS_FILE = "processed_news"

load_dotenv()
bot_token = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
client = OpenAI()


def read_processed_news(file_path: str) -> set:
    """
    Читает файл с обработанными новостями и возвращает их как множество.

    :param file_path: Путь к файлу с обработанными новостями.
    :return: Множество URL обработанных новостей.
    """
    if os.path.exists(file_path):
        with open(file_path, 'r') as file:
            return set(file.read().split("\n"))
    return set()


def write_processed_news(file_path: str, processed_news: set):
    """
    Записывает обработанные новости в файл.

    :param file_path: Путь к файлу для записи.
    :param processed_news: Множество URL обработанных новостей.
    """
    with open(file_path, 'w') as file:
        file.write("\n".join(processed_news))


def get_rss_feed_titles(url: str) -> dict[str, str]:
    """
    Парсит RSS-ленту и возвращает список заголовков.

    :param url: URL RSS-ленты
    :return: Словарь, где ключ - URL новости, значение - заголовок новости.
    """
    xml = requests.get(url).text
    feed = feedparser.parse(xml)
    return {entry.link: entry.title.strip() for entry in feed.entries}


def is_transport_news(news: str) -> bool:
    """
    Определяет, относится ли новость к транспорту и благоустройству.

    :param news: Текст новости.
    :return: True, если новость относится к транспорту, иначе False.
    """
    completion = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": "Скажи, относится ли данная новость к транспорту и благоустройству в Чебоксарах и Чувашии. Отвечай да или нет. \n" + news,
            }
        ],
        model="gpt-3.5-turbo",
    )
    answer = str(completion.choices[0].message.content)
    return answer.lower().startswith("да")


def send_telegram_message(chat_id: str, message_text: str):
    """
    Отправляет сообщение через Telegram бота.

    :param bot_token: Токен вашего Telegram бота
    :param chat_id: ID чата для отправки сообщения
    :param message_text: Текст сообщения
    """
    send_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    params = {
        "chat_id": chat_id,
        "text": message_text,
    }
    response = requests.post(send_url, data=params)
    return response.json()  # Возвращает результат в формате JSON


def main():
    processed_news = read_processed_news(NEWS_FILE)

    news = {}
    for url in RSS:
        print(f"Загружаем новости {url}...")
        titles = get_rss_feed_titles(url)
        print(f"Новостей загружено: {len(titles)}")
        for title_url, title in titles.items():
            if title_url in processed_news:
                print(f"Новость '{title}' уже обработана.")
                continue
            print(f"Обрабатываем новость '{title}'...")
            if is_transport_news(title):
                print(f"Новость '{title}' относится к транспорту.")
                news[title_url] = title
                send_telegram_message(CHAT_ID, f"📰 {title}\n🔗 {title_url}")
            processed_news.add(title_url)

    write_processed_news(NEWS_FILE, processed_news)


if __name__ == "__main__":
    main()
