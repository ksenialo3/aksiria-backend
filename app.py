import os
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import datetime
import json
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash

load_dotenv()

app = Flask(__name__)
CORS(app)

basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'aksiria.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.path.join(basedir, 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(200), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    company_name = db.Column(db.String(200), nullable=False)
    industry = db.Column(db.String(100))
    other_industry = db.Column(db.String(200))
    target_audience = db.Column(db.Text)
    target_audience_file = db.Column(db.String(300))
    tone_method = db.Column(db.String(20))
    tone_value = db.Column(db.Text)
    tone_analyze_data = db.Column(db.Text)
    tone_file = db.Column(db.String(300))
    social_networks = db.Column(db.String(200))
    vk_url = db.Column(db.String(300))
    telegram_url = db.Column(db.String(300))
    dzen_url = db.Column(db.String(300))
    logo = db.Column(db.String(300))
    brandbook = db.Column(db.String(300))
    extra_info = db.Column(db.Text)
    api_integration = db.Column(db.String(10))
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'company_name': self.company_name,
            'industry': self.industry,
            'other_industry': self.other_industry,
            'target_audience': self.target_audience,
            'tone_method': self.tone_method,
            'tone_value': self.tone_value,
            'tone_analyze_data': self.tone_analyze_data,
            'social_networks': self.social_networks,
            'extra_info': self.extra_info,
            'api_integration': self.api_integration,
        }

FOLDER_ID = os.getenv('YANDEX_FOLDER_ID')
print("FOLDER_ID repr:", repr(FOLDER_ID))
API_KEY = os.getenv('YANDEX_API_KEY')
GPT_MODEL = "yandexgpt-lite"
GPT_URL = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"

@app.route('/register', methods=['POST'])
def register():
    try:
        data = request.form
        print("REGISTER DATA:", data)

        company_name = data.get('company_name')
        email = data.get('email')
        password = data.get('password')
        if not company_name or not email or not password:
            return jsonify({'error': 'Название компании, email и пароль обязательны'}), 400

        if User.query.filter_by(email=email).first():
            return jsonify({'error': 'Пользователь с таким email уже существует'}), 400

        password_hash = generate_password_hash(password)

        def save_file(file_key):
            file = request.files.get(file_key)
            if file and file.filename:
                filename = secure_filename(file.filename)
                unique = f"{datetime.datetime.utcnow().timestamp()}_{filename}"
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique)
                file.save(filepath)
                return unique
            return None

        target_audience_file = save_file('target_audience_file')
        tone_file = save_file('tone_file')
        logo = save_file('logo')
        brandbook = save_file('brandbook')

        example_files = request.files.getlist('examples_files')
        example_links = data.get('examples_links')
        extra_info = data.get('extra_info', '')
        if example_files or example_links:
            extra_info = (extra_info or '') + '\n\n=== Примеры постов ===\n'
            if example_links:
                extra_info += f"Ссылки: {example_links}\n"
            if example_files:
                file_names = []
                for f in example_files:
                    if f.filename:
                        fn = secure_filename(f.filename)
                        unique = f"{datetime.datetime.utcnow().timestamp()}_{fn}"
                        f.save(os.path.join(app.config['UPLOAD_FOLDER'], unique))
                        file_names.append(unique)
                extra_info += f"Загруженные файлы: {', '.join(file_names)}\n"

        user = User(
            email=email,
            password_hash=password_hash,
            company_name=company_name,
            industry=data.get('industry'),
            other_industry=data.get('other_industry'),
            target_audience=data.get('target_audience'),
            target_audience_file=target_audience_file,
            tone_method=data.get('tone_method'),
            tone_value=data.get('tone_value') if data.get('tone_method') in ['select', 'custom'] else None,
            tone_analyze_data=data.get('tone_analyze') if data.get('tone_method') == 'analyze' else None,
            tone_file=tone_file,
            social_networks=data.get('social_networks'),
            vk_url=data.get('vk_url'),
            telegram_url=data.get('telegram_url'),
            dzen_url=data.get('dzen_url'),
            logo=logo,
            brandbook=brandbook,
            extra_info=extra_info,
            api_integration=data.get('api_integration')
        )
        db.session.add(user)
        db.session.commit()

        return jsonify({'status': 'ok', 'user_id': user.id}), 200
    except Exception as e:
        app.logger.error(f"Registration error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    if not email or not password:
        return jsonify({'error': 'Email и пароль обязательны'}), 400

    user = User.query.filter_by(email=email).first()
    if not user or not check_password_hash(user.password_hash, password):
        return jsonify({'error': 'Неверный email или пароль'}), 401

    return jsonify({'status': 'ok', 'user_id': user.id}), 200

@app.route('/user/<int:user_id>', methods=['GET'])
def get_user(user_id):
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({'error': 'Пользователь не найден'}), 404
    return jsonify({
        'id': user.id,
        'company_name': user.company_name,
        'target_audience': user.target_audience,
        'tone_value': user.tone_value,
        'extra_info': user.extra_info
    })

@app.route('/change-password', methods=['POST'])
def change_password():
    data = request.get_json()
    user_id = data.get('user_id')
    old_password = data.get('old_password')
    new_password = data.get('new_password')

    if not user_id or not old_password or not new_password:
        return jsonify({'error': 'Все поля обязательны'}), 400

    user = db.session.get(User, int(user_id))
    if not user:
        return jsonify({'error': 'Пользователь не найден'}), 404

    if not check_password_hash(user.password_hash, old_password):
        return jsonify({'error': 'Неверный старый пароль'}), 401

    user.password_hash = generate_password_hash(new_password)
    db.session.commit()
    return jsonify({'status': 'ok'}), 200

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
    if request.is_json:
        data = request.get_json()
    else:
        data = request.form.to_dict()

    print("RECEIVED DATA:", data)

    user_id = data.get('user_id')
    user = None
    if user_id:
        try:
            user = db.session.get(User, int(user_id))
        except Exception as e:
            app.logger.error(f"Error loading user {user_id}: {e}")

    description = data.get('description')
    if not description:
        return jsonify({"error": "Не указано описание товара или услуги"}), 400

    goal = data.get('goal')
    keywords = data.get('keywords')
    social = data.get('social_network', 'VK')
    hesh = data.get('hesh')

    brand = data.get('brand')
    if not brand and user:
        brand = user.company_name
    if not brand:
        return jsonify({"error": "Не указано название бренда"}), 400

    audience = data.get('audience')
    if not audience and user and user.target_audience:
        audience = user.target_audience
    if not audience:
        return jsonify({"error": "Не указана целевая аудитория"}), 400

    tone = data.get('tone')
    if not tone and user and user.tone_value:
        tone = user.tone_value

    user_context = ""
    if user and user.extra_info:
        user_context = f"Дополнительная информация о бизнесе: {user.extra_info}"

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
    {user_context}

    Инструкции по тексту (ВНИМАНИЕ, ЭТО ВАЖНО):
    1. ЗАГОЛОВОК. Должен быть ярким, цепляющим, без штампов. Используй вопрос, игру слов, неожиданное утверждение, связанное с ключевыми словами. Запрещено начинать с «Обновление меню в ...», «У нас новинки» и т.п.
    2. СТРУКТУРА (примерная)
- Зацепка (1-2 предложения): Опиши ситуацию/эмоцию/проблему, знакомую ЦА. Сразу вовлеки читателя.
- Представление новинок: Не перечисляй вещи сухо. Распиши каждый через детали и выгоды. Что даёт это? Какие ощущения? Почему это must-try?
- Микро-выгоды: Как это впишется в жизнь ЦА?
- Призыв к действию (ОДИН, чёткий, в конце). Не дублируй призыв в середине.
    3. ЧЕГО ДЕЛАТЬ НЕЛЬЗЯ (антипримеры)
- Забудь фразы-клише: «мы обновили меню», «приходите и попробуйте», «насладитесь вкусом», «погрузитесь в атмосферу», «не пропустите новинки», «порадуйте себя», «идеальное место».
- Не используй слово «новинки»/«новые» чаще двух раз за весь пост.
- Не повторяй одинаковые прилагательные рядом.
- Категорически нельзя делать два призыва к действию. Один — в конце.
    4. ЯЗЫК И СТИЛЬ
- Пиши короткими предложениями, чередуй с более длинными. Используй вопросы к читателю, восклицания, разговорные частицы.
- Добавь 3–4 эмодзи, но не перегружай.
- Конкретика вместо общих слов.
- Правило одного смысла: Каждый абзац — только одна новая мысль.
    5. ДЛИНА: максимум 2000 знаков с пробелами.
    """

    post_text = generate_text(prompt)
    return jsonify({"text": post_text})

with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True, port=5000)