import requests
import telebot
from telebot import types
from config import *
from database import *
bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)
conn = sqlite3.connect('database.db',check_same_thread=False)
conn.commit()

def ask_gpt(text):
    iam_token = IAM_TOKEN
    folder_id = FOLDER_ID

    headers = {
        'Authorization': f'Bearer {iam_token}',
        'Content-Type': 'application/json'
    }
    data = {
        "modelUri": f"gpt://{folder_id}/yandexgpt-lite",  # модель для генерации текста
        "completionOptions": {
            "stream": False,  # потоковая передача частично сгенерированного текста выключена
            "temperature": 0.6,  # чем выше значение этого параметра, тем более креативными будут ответы модели (0-1)
            "maxTokens": "200"  # максимальное число сгенерированных токенов, очень важный параметр для экономии токенов
        },
        "messages": [
            {
                "role": "user",  # пользователь спрашивает у модели
                "text": "Ты пишешь историю вместе с человеком. Историю вы пишете по очереди. Начинает человек, а ты продолжаешь. Если это уместно, ты можешь добавлять в историю диалог между персонажами. Диалоги пиши с новой строки и отделяй тире. Не пиши никакого пояснительного текста в начале, а просто логично продолжай историю\nНапиши начало истории в стиле 123 с главным героем 123. Вот начальный сеттинг: \n123. \nНачало должно быть коротким, 1-3 предложения.\nНе пиши никакие подсказки пользователю, что делать дальше. Он сам знает"
            }
        ]
    }

    # Выполняем запрос к YandexGPT
    response = requests.post("https://llm.api.cloud.yandex.net/foundationModels/v1/completion",
                             headers=headers,
                             json=data)

    # Проверяем, не произошла ли ошибка при запросе
    if response.status_code == 200:
                # достаём ответ YandexGPT
        text = response.json()["result"]["alternatives"][0]["message"]["text"]
        return text
    else:
        raise RuntimeError(
            'Invalid response received: code: {}, message: {}'.format(
                {response.status_code}, {response.text}
            )
        )

# Подсчитывает количество токенов в сессии
def count_tokens(text):
    headers = { # заголовок запроса, в котором передаем IAM-токен
        'Authorization': f'Bearer {IAM_TOKEN}', # token - наш IAM-токен
        'Content-Type': 'application/json'
    }
    data = {
       "modelUri": f"gpt://{FOLDER_ID}/yandexgpt/latest", # указываем folder_id
       "maxTokens": 200,
       "text": text # text - тот текст, в котором мы хотим посчитать токены
    }
    return len(
        requests.post(
            "https://llm.api.cloud.yandex.net/foundationModels/v1/tokenize",
            json=data,
            headers=headers
        ).json()['tokens']
    ) # здесь, после выполнения запроса, функция возвращает количество токенов в text


# Обработчик команды /start
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.chat.id
    add_row(conn,user_id,0,0,SYSTEM_PROMPT, "")
    bot.send_message(message.chat.id, "Привет! Я помогу тебе составить классный сценарий!")

    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    genres = ["Драма", "Комедия", "Фэнтези", "Ужасы", "Приключения"]
    for genre in genres:
        keyboard.add(types.KeyboardButton(genre))
    bot.send_message(message.chat.id, "Для начала выбери жанр, в котором хочешь составить сценарий(дан выбор)",
                     reply_markup=keyboard)
    bot.register_next_step_handler(message, get_genre)


# Обработчик ввода жанра
def get_genre(message):
    user_id = message.chat.id
    tokens, session_id, prompt, history = get_row(conn,user_id)
    genre = message.text
    prompt += (f"\nНапиши начало истории в стиле {genre} ")
    update_row(conn,user_id, tokens, session_id, prompt, history)
    # Запрашиваем персонажа
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    characters = ["Самоуверенный мужчина с трудным характером", "Самоуверенная женщина с трудным характером", "Мужчина лидерскими качествами", "Женщина лидерскими качествами", "Стеснительный мужчина-ученый", "Стеснительная женщина-ученый"]
    for character in characters:
        keyboard.add(types.KeyboardButton(character))
    bot.send_message(message.chat.id, "Теперь опиши персонажа, который будет главным героем(дан выбор или введите сами)\n", reply_markup=keyboard)
    bot.register_next_step_handler(message, get_character)


# Обработчик ввода персонажа
def get_character(message):
    user_id = message.chat.id
    tokens, session_id, prompt, history = get_row(conn,user_id)
    character = message.text
    prompt += (f"с главным героем {character}. ")
    update_row(conn,user_id, tokens, session_id, prompt, history)
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    settings = ["Дюна", "Звездные Войны", "Сталкер", "Киберпанк", "Средневековье"]
    for setting in settings:
        keyboard.add(types.KeyboardButton(setting))
    bot.send_message(message.chat.id, f"И последнее. Выбери сеттинг, в котором будет жить главный герой(дан выбор)\n"
                                      f"Дюна: Будущее человечества без высоких технологий так как нет вычислительных машин человек начал развиваться по альторнативному путю.Путь - саморазвития\n"
                                      f"Звездные Войны: Всем известная вселенная незачем объяснятью\n"
                                      f"Сталкер: Мир припяти в котором сущиствуют мутанты. В зоне отчуждения каждый сам за себя.\n"
                                      f"Киберпанк: Будущее человечества в котором люди стали активно внядрять в себя импланты для улучшение жизни и не только.\n"
                                      f"Средневековье: Прошлое человека описывающиее события без технологий.",
                     reply_markup=keyboard)
    bot.register_next_step_handler(message, get_setting)


def get_setting(message):
    # Сохраняем сеттинг
    user_id = message.chat.id
    tokens, session_id, prompt, history = get_row(conn,user_id)
    setting = message.text
    # Формируем запрос для YandexGPT
    prompt += (f"Вот начальный сеттинг: \n{setting}. \n"
              "Начало должно быть коротким, 1-3 предложения.\n")
    prompt += 'Не пиши никакие подсказки пользователю, что делать дальше. Он сам знает'
    update_row(conn,user_id, tokens, session_id, prompt, history)
    # Запрашиваем продолжение истории
    bot.send_message(message.chat.id, "Напиши продолжение истории. Чтобы закончить введи end(напишите вручную)")
    bot.register_next_step_handler(message, get_user_content)


# Обработчик ввода продолжения истории
def get_user_content(message):
    user_id = message.chat.id
    tokens, session_id, prompt, history = get_row(conn,user_id)
    # Получаем продолжение истории
    user_content = message.text
    history+=user_content
    prompt += f"Человек начал эту историю вот так - {user_content}."
    print(count_tokens(prompt))
    if count_tokens(prompt)> 200:
        bot.send_message(message.chat.id, "Запрос слишком длинный")
        bot.send_message(message.chat.id, "Вот, что у нас получилось:")
        bot.send_message(message.chat.id, prompt)
    # Если пользователь ввел "end", то завершаем диалог
    if user_content.lower() == 'end':
        bot.send_message(message.chat.id, "Вот, что у нас получилось:")
        bot.send_message(message.chat.id, prompt)
        return

    # Отправляем запрос в YandexGPT
    assistant_content = ask_gpt(prompt)
    prompt += f"Ты продолжил эту историю вот так - {user_content}."
    # Отправляем начало истории пользователю
    bot.send_message(message.chat.id, f"YandexGPT: {assistant_content}")
    history += assistant_content
    update_row(conn,user_id, tokens, session_id, prompt, history)
    # Запрашиваем продолжение истории
    bot.send_message(message.chat.id, "Напиши продолжение истории. Чтобы закончить введи end:")
    bot.register_next_step_handler(message, get_user_content)



bot.polling()
