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
    "text": "Ты — креативный директор и SMM-стратег с 10-летним опытом. Твои посты всегда попадают в тренды, собирают высокий охват и вовлечение. Ты ненавидишь канцелярит, штампы и безликую «ИИ-речь». Твоя задача — упаковать продукт в интересную историю, используя современные речевые модули и триггеры ЦА. Твой главный навык — следовать брифу клиента, но упаковывать это в креатив и чёткий призыв к действию. Твои тексты сравнивают с живыми людьми, их невозможно отличить от постов лучших копирайтеров. Напиши пост для выбранной социальной сети от имени бренда."
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
    Вводные данные:
    Название бренда: {brand}
    Детали поста/продукта: {description}
    Целевая аудитория: {audience}
    Тон коммуникации: {tone}
    Цель поста: {goal}
    Ключевые слова: {keywords}
    Социальная сеть: {social}
    Хештеги: {hesh}

    Инструкции по тексту (ВНИМАНИЕ, ЭТО ВАЖНО):

    1. ЗАГОЛОВОК. Должен быть ярким, цепляющим, без штампов. Используй вопрос, игру слов, неожиданное утверждение, связанное с ключевыми словами. Запрещено начинать с «Обновление меню в ...», «У нас новинки» и т.п.

    2. СТРУКТУРА (примерная)
- Зацепка (1-2 предложения): Опиши ситуацию/эмоцию/проблему, знакомую ЦА. Сразу вовлеки читателя.
- Представление новинок: Не перечисляй вещи сухо. Распиши каждый через детали и выгоды. Что даёт это? Какие ощущения? Почему это must-try?
- Пример для лимонада: «Цитрусовый взрыв, который бодрит лучше трёх будильников».
- Микро-выгоды: Как это впишется в жизнь ЦА?
- Призыв к действию (ОДИН, чёткий, в конце). Не дублируй призыв в середине.

    3. ЧЕГО ДЕЛАТЬ НЕЛЬЗЯ (антипримеры)
- Забудь фразы-клише: «мы обновили меню», «приходите и попробуйте», «насладитесь вкусом», «погрузитесь в атмосферу», «не пропустите новинки», «порадуйте себя», «идеальное место».
- Не используй слово «новинки»/«новые» чаще двух раз за весь пост.
- Не повторяй одинаковые прилагательные рядом. Сказал «освежающий» — про другой напиши «нежный», «бархатистый», «согревающий».
- Категорически нельзя делать два призыва к действию. Один — в конце.

    4. ЯЗЫК И СТИЛЬ
- Пиши короткими предложениями, чередуй с более длинными. Используй вопросы к читателю, восклицания, разговорные частицы («представь», «а что, если...», «самое то»).
- Добавь 3–4 эмодзи, но не перегружай. Они должны быть уместны и помогать визуализировать.
- Конкретика вместо общих слов: Вместо «вкусный лимонад» — «прозрачный, с дольками лайма и мятой, которые звенят о лёд». Вместо «уютная кофейня» — «место, где можно зависнуть с ноутом и не слышать городского шума».
- Правило одного смысла: Каждый абзац — только одна новая мысль. Не повторяй сказанное другими словами.

    5. ДЛИНА
Максимум 2000 знаков с пробелами. Уложись в этот лимит.
    """

    post_text = generate_text(prompt)
    print("ОТВЕТ СЕРВЕРА:", {"text": post_text})
    return jsonify({
        "text": post_text
    })

if __name__ == '__main__':
    app.run(debug=True, port=5000)
