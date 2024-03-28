import telebot
from telebot.types import Message, ReplyKeyboardMarkup, KeyboardButton
from config import BOT_TOKEN, BOT_ADMIN_ID, GPT_MAX_TOKENS, MAX_SESSIONS, MAX_USERS, MAX_TOKENS_IN_SESSION
from gpt import get_answer_from_gpt
from log import get_log_file
from data_base import insert_user_to_user_data_table, get_user_data, add_message_data, get_messages_data
from bot_info import bot_info, system_end_prompt
from helpers import convert_messages_data, get_story, get_messages_data_by_user_id

# @GPT_StoryMaker_Bot
bot = telebot.TeleBot(token=BOT_TOKEN)

bot.send_message(BOT_ADMIN_ID, f"👋 летс гоу")


def make_keyboard(items):
    markup = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    for item in items:
        markup.add(KeyboardButton(item))

    return markup


@bot.message_handler(commands=['start', 'new_story'])
def start_command(message: Message):
    chat_id = message.chat.id
    user_name = message.chat.first_name
    insert_user_to_user_data_table(chat_id, user_name)
    if message.text == '/start':
        bot.send_message(chat_id, f"🤖 Приветствую тебя, {user_name}!")

    user_data = get_user_data(chat_id)
    session_id = user_data['session_id']
    user_number = user_data['id']

    if user_number > MAX_USERS:
        bot.send_message(chat_id, f"Извините, бот недоступен ((\nКоличество пользователей бота превышает допустимое "
                                  f"количество. ({user_number}/{MAX_USERS})")
        return
    if session_id > MAX_SESSIONS:
        bot.send_message(chat_id, f"К сожалению, вы потратили все сессии "
                                  f"({session_id} из {MAX_SESSIONS})"
                                  f"\nОбратитесь к администратору, чтобы возобновить доступ - @liwari_kaulitz")
        return
    messages_data = get_messages_data(chat_id, session_id)
    session_total_tokens = 0
    if messages_data and messages_data[-1]['total_tokens']:
        session_total_tokens = messages_data[-1]['total_tokens']
        if session_total_tokens >= MAX_TOKENS_IN_SESSION:
            bot.send_message(chat_id, f"К сожалению, вы потратили все токены"
                                      f"({session_total_tokens} из {MAX_TOKENS_IN_SESSION})"
                                      f"\nОбратитесь к администратору, чтобы возобновить доступ - @liwari_kaulitz")
            return
    bot.send_message(chat_id, f"Вы начали {session_id} из {MAX_SESSIONS} сессий.\nНа вашем счету: "
                              f"{MAX_TOKENS_IN_SESSION - session_total_tokens} из {MAX_TOKENS_IN_SESSION} токенов.")
    next_question_handler(chat_id, 0)


def make_command_button(message):
    chat_id = message.chat.id
    button_answers = ['/whole_story', '/new_story']
    if chat_id == BOT_ADMIN_ID:
        button_answers.append('/debug')
    markup = make_keyboard(button_answers)
    bot.send_message(chat_id, 'История закончена.\nСпасибо за то, что писал её со мной!', reply_markup=markup)


def check_is_command(message: Message):
    if message.text and message.text[0] == '/':
        return True
    return False


@bot.message_handler(commands=['help'])
def help_command(message):
    chat_id = message.chat.id
    bot.send_message(chat_id,
                     text="🤖 Привет!\nЯ GPT-бот, с которым ты сможешь создать свою уникальную историю.\nОт тебя мне "
                          "нужен выбор жанра, персонажа и места событий. Моя задача: на основе твоего выбора "
                          "придумать небольшую историю ☺️\nНачать - /start")


@bot.message_handler(commands=['debug'])
def send_logs(message):
    chat_id = message.chat.id
    if chat_id == BOT_ADMIN_ID:
        with get_log_file() as log_file:
            bot.send_document(chat_id, log_file)
    else:
        bot.send_message(chat_id, 'Недостаточно прав для выполнения команды')


@bot.message_handler(commands=['continue'])
def continue_action(message):
    chat_id = message.chat.id
    messages_data = get_messages_data_by_user_id(chat_id)
    messages_data_length = len(messages_data)
    questions_data_length = len(bot_info['questions_data'])

    if messages_data_length < questions_data_length:
        next_question_index = len(messages_data)
        next_question_handler(chat_id, next_question_index)
        return

    session_total_tokens = 0
    if messages_data and messages_data[-1]['total_tokens']:
        session_total_tokens = messages_data[-1]['total_tokens']
    if session_total_tokens >= MAX_TOKENS_IN_SESSION:
        bot.send_message(chat_id, f"Количество токенов, использованых за сессию, превысило лимит. "
                                  f"({session_total_tokens} из {MAX_TOKENS_IN_SESSION})"
                                  f"\nНачните новую историю - /start")
        return

    converted_messages = convert_messages_data(messages_data)
    messages = converted_messages['messages']
    all_text = converted_messages['all_text']

    waiting_message = bot.send_message(chat_id, 'Запрос передан GPT.\nПодождите, история генерируется...')

    gpt_response = get_answer_from_gpt(messages, all_text)
    answer = gpt_response['answer']
    tokens_number = gpt_response['tokens_number']
    add_message_data(chat_id, 'assistant', answer, tokens_number)

    bot.delete_message(waiting_message.chat.id, waiting_message.message_id)

    bot.send_message(chat_id, answer)
    if message.text == '/end':
        make_command_button(message)
        return
    bot.send_message(chat_id, 'Для продолжения истории напиши дополнительную информацию или нажми /continue\nДля '
                              'генерации завершения истории нажми /end')


@bot.message_handler(commands=['end'])
def end_command(message):
    chat_id = message.chat.id
    messages_data = get_messages_data_by_user_id(chat_id)
    messages_data_length = len(messages_data)
    questions_data_length = len(bot_info['questions_data'])

    if messages_data_length < questions_data_length:
        next_question_index = len(messages_data)
        next_question_handler(chat_id, next_question_index)
        return

    add_message_data(chat_id, 'system', system_end_prompt, len(system_end_prompt))
    continue_action(message)


@bot.message_handler(commands=['whole_story'])
def whole_story(message: Message):
    chat_id = message.chat.id
    messages_data = get_messages_data_by_user_id(chat_id)
    story_text = get_story(messages_data)
    if not story_text:
        bot.send_message(chat_id, 'В текущей сессии у вас ещё не было сгенерированной истории.')
        return
    bot.send_message(chat_id, story_text)


def next_question_handler(user_id, question_index):
    chat_id = user_id

    button_answers = []
    next_question_data = bot_info['questions_data'][question_index]
    answers_data = next_question_data['answers_data']
    for answer_data in answers_data:
        button_answers.append(answer_data['button_answer'])
    markup = make_keyboard(button_answers)
    bot.send_message(chat_id, next_question_data['question'], reply_markup=markup)


@bot.message_handler(content_types=['text'])
def text_handler(message: Message):
    if check_is_command(message):
        return
    chat_id = message.chat.id
    user_message = message.text
    prev_messages_data = get_messages_data_by_user_id(chat_id)
    current_question_index = len(prev_messages_data)
    prev_messages_data_length = current_question_index + 1
    questions_data_length = len(bot_info['questions_data'])
    role = 'user'
    prompt = ''
    if prev_messages_data_length <= questions_data_length:
        role = 'system'
        current_question_data = bot_info['questions_data'][current_question_index]
        current_answers_data = current_question_data['answers_data']
        if not len(current_answers_data):
            prompt = user_message
        for answer_data in current_answers_data:
            if user_message == answer_data['button_answer']:
                prompt = answer_data['prompt']
    if not prompt:
        next_question_handler(chat_id, current_question_index)
        return

    add_message_data(chat_id, role, prompt, len(prompt))
    continue_action(message)


bot.polling()
