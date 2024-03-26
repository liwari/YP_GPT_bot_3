import telebot
from telebot.types import Message, ReplyKeyboardMarkup, KeyboardButton
from config import BOT_TOKEN, BOT_ADMIN_ID, GPT_MAX_TOKENS
from gpt import get_answer_from_gpt
from log import get_log_file
from data_base import (insert_user_to_user_data_table, update_user_data, get_user_data, add_message_data,
                       get_messages_data)
from bot_info import bot_info
from helpers import convert_messages_data

# @GPT_ThemeLevel_Bot
bot = telebot.TeleBot(token=BOT_TOKEN)

bot.send_message(BOT_ADMIN_ID, f"👋 летс гоу")


def make_keyboard(items):
    markup = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    for item in items:
        markup.add(KeyboardButton(item))

    return markup


@bot.message_handler(commands=['start'])
def start_command(message: Message):
    chat_id = message.chat.id
    user_name = message.chat.first_name
    insert_user_to_user_data_table(chat_id, user_name)
    bot.send_message(chat_id, f"Приветствую тебя, {user_name}!")
    choice_gpt_params(message)


def choice_gpt_params(message):
    if check_is_command(message) and message.text != '/start':
        return
    chat_id = message.chat.id
    answer = message.text

    user_data = get_user_data(chat_id)
    session_id = user_data['session_id']
    messages_data = get_messages_data(chat_id, session_id)
    current_question_index = len(messages_data)
    current_question_data = bot_info['questions_data'][current_question_index]
    current_answers_data = current_question_data['answers_data']

    prompt = ''
    if not len(current_answers_data):
        prompt = answer
    for answer_data in current_answers_data:
        if answer == answer_data['button_answer']:
            prompt = answer_data['prompt']
    if prompt:
        add_message_data(chat_id, 'system', prompt)

    messages_data = get_messages_data(chat_id, session_id)
    if len(messages_data) == len(bot_info['questions_data']):
        continue_message(message)
        return
    next_question_index = len(messages_data)

    button_answers = []
    next_question_data = bot_info['questions_data'][next_question_index]
    answers_data = next_question_data['answers_data']
    for answer_data in answers_data:
        button_answers.append(answer_data['button_answer'])
    markup = make_keyboard(button_answers)
    response_message = bot.send_message(chat_id, next_question_data['question'],
                                        reply_markup=markup)
    bot.register_next_step_handler(response_message, choice_gpt_params)


def check_is_command(message: Message):
    if message.text and message.text[0] == '/':
        return True
    return False


@bot.message_handler(commands=['help'])
def help_command(message):
    chat_id = message.chat.id
    bot.send_message(chat_id,
                     text="Я твой цифровой собеседник.\nТы можешь отправлять мне свои запросы, а для продолжения "
                          "ответа нажми /continue\nУзнать обо мне подробнее можно командой /about")


@bot.message_handler(commands=['about'])
def about_command(message):
    chat_id = message.chat.id
    bot.send_message(chat_id,
                     text="Рад, что ты заинтересован_а! Мое предназначение — не оставлять тебя в одиночестве и "
                          "всячески подбадривать!")


@bot.message_handler(commands=['debug'])
def send_logs(message):
    chat_id = message.chat.id
    if chat_id == BOT_ADMIN_ID:
        with get_log_file() as log_file:
            bot.send_document(chat_id, log_file)
    else:
        bot.send_message(chat_id, 'Недостаточно прав для выполнения команды')


@bot.message_handler(commands=['continue'], command=['begun'])
def continue_message(message):
    chat_id = message.chat.id
    user_data = get_user_data(chat_id)
    session_id = user_data['session_id']
    messages_data = get_messages_data(chat_id, session_id)
    if len(messages_data) >= len(bot_info['questions_data']):
        converted_messages = convert_messages_data(messages_data)
        messages = converted_messages['messages']
        all_text = converted_messages['all_text']
        gpt_response = get_answer_from_gpt(messages, all_text)
        answer = gpt_response['answer']
        if answer:
            add_message_data(chat_id, 'assistant', answer)
            bot.send_message(chat_id, answer)
            bot.send_message(chat_id, 'Для продолжения ответа нажми /continue,\nили отправь следующий запрос')
        else:
            bot.send_message(chat_id, 'Мне больше нечего сказать...')
    else:
        choice_gpt_params(message)


@bot.message_handler(content_types=['text'])
def question_handler(message: Message):
    chat_id = message.chat.id
    user_message = message.text
    add_message_data(chat_id, 'user', user_message)
    user_data = get_user_data(chat_id)

    session_id = user_data['session_id']
    messages_data = get_messages_data(chat_id, session_id)
    converted_messages = convert_messages_data(messages_data)
    messages = converted_messages['messages']
    all_text = converted_messages['all_text']

    if len(messages) < len(bot_info['questions_data']) + 1:
        choice_gpt_params(message)
        return

    gpt_response = get_answer_from_gpt(messages, all_text)
    answer = gpt_response['answer']
    add_message_data(chat_id, 'assistant', answer)

    bot.send_message(chat_id, answer)
    bot.send_message(chat_id, 'Для продолжения ответа нажми /continue,\nили отправь следующий запрос')


bot.polling()
