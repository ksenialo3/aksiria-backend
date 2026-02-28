import os
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app, origins=["https://aksiriatest1.tilda.ws"])

FOLDER_ID = os.getenv('YANDEX_FOLDER_ID')
print("FOLDER_ID repr:", repr(FOLDER_ID))
API_KEY = os.getenv('YANDEX_API_KEY')
GPT_MODEL = "yandexgpt-lite"
GPT_URL = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"

def generate_text(prompt):
    print("=== ОТЛАДКА ===")
    print("FOLDER_ID:", FOLDER_ID)
    print("API_KEY (первые 5 символов):", API_KEY[:5] if API_KEY else "None")
    print("PROMPT:", prompt)
    
    headers = {
        "Authorization": f"Api-Key {API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "modelUri": f"gpt://{FOLDER_ID}/{GPT_MODEL}",
        "completionOptions": {
            "stream": False,
            "temperature": 0.6,
            "maxTokens": 2000
        },
        "messages": [
            {
                "role": "system",
                "text": "Ты  профессиональный SMM-менеджер. Пиши посты для социальных сетей."
            },
            {
                "role": "user",
                "text": prompt
            }
        ]
    }
    print("REQUEST DATA:", data)
    try:
        response = requests.post(GPT_URL, headers=headers, json=data, timeout=60)
        response.raise_for_status()
        result = response.json()
        print("ОТВЕТ ОТ YANDEXGPT:", result)
        text = result['result']['alternatives'][0]['message']['text']
        return text
    except Exception as e:
        print("!!! Исключение:", e)
        if hasattr(e, 'response') and e.response is not None:
            print("!!! Тело ответа от Яндекса:", e.response.text)
        return f"Ошибка при обращении к YandexGPT: {str(e)}"

@app.route('/generate', methods=['POST'])
def generate():
    data = request.get_json()
    print("RECEIVED JSON:", data)
    if not data:
        return jsonify({"error": "Нет данных"}), 400

    brand = data.get('brand')
    description = data.get('description')
    audience = data.get('audience')
    tone = data.get('tone')
    keywords = data.get('keywords')
    social = data.get('social_network', 'VK')

    if not all([brand, description, audience]):
        return jsonify({"error": "Заполните обязательные поля: бренд, описание, ЦА"}), 400

    prompt = f"""
    Напиши пост для социальной сети {social} от имени бренда {brand}.
    Опиши продукт или услугу: {description}.
    Целевая аудитория: {audience}.
    Тон коммуникации: {tone}.
    Используй ключевые слова: {keywords}.
    Пост должен быть вовлекающим, содержать призыв к действию и хештеги.
    Длина: до 2000 знаков.
    """

    post_text = generate_text(prompt)
    print("ОТВЕТ СЕРВЕРА:", {"text": post_text})
    return jsonify({
        "text": post_text
    })

if __name__ == '__main__':
    app.run(debug=True, port=5000)
