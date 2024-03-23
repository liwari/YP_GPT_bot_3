import telebot
from telebot.types import Message, ReplyKeyboardMarkup, KeyboardButton
from config import BOT_TOKEN, BOT_ADMIN_ID, GPT_MAX_TOKENS
from gpt import get_answer_from_gpt
from log import get_log_file
from data_base import insert_user_to_user_data_table, update_user_data, get_user_data
from bot_info import bot_info

# GPT_ThemeLevel_Bot
bot = telebot.TeleBot(token=BOT_TOKEN)

bot.send_message(BOT_ADMIN_ID, f"👋 летс гоу")


def make_keyboard(items):
    markup = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    for item in items:
        markup.add(KeyboardButton(item))

    return markup


@bot.message_handler(commands=['start'])
def start_command(message):
    chat_id = message.chat.id
    insert_user_to_user_data_table(chat_id)
    user_name = message.from_user.first_name
    bot.send_message(chat_id, f"Приветствую тебя, {user_name}!")
    choice_gpt_params(message)


def choice_gpt_params(message):
    chat_id = message.chat.id
    button_answers = []
    answers_data = bot_info['questions_data'][0]['answers_data']
    for answer_data in answers_data:
        button_answers.append(answer_data['button_answer'])
    markup = make_keyboard(button_answers)
    select_theme_message = bot.send_message(chat_id, bot_info['questions_data'][0]['question'],
                                            reply_markup=markup)
    bot.register_next_step_handler(select_theme_message, selected_theme_handler)


def check_is_command(message: Message):
    if message.text and message.text[0] == '/':
        return True
    return False


def selected_theme_handler(message: Message):
    if check_is_command(message):
        return
    chat_id = message.chat.id
    answer = message.text
    prompt = ''
    answers_data = bot_info['questions_data'][0]['answers_data']
    for answer_data in answers_data:
        if answer == answer_data['button_answer']:
            prompt = answer_data['prompt']
    if not prompt:
        choice_gpt_params(message)
        return
    update_user_data(chat_id, 'theme', prompt)
    button_answers = []
    answers_data = bot_info['questions_data'][1]['answers_data']
    for answer_data in answers_data:
        button_answers.append(answer_data['button_answer'])
    markup = make_keyboard(button_answers)

    selected_level_message = bot.send_message(chat_id, bot_info['questions_data'][1]['question'],
                                              reply_markup=markup)
    bot.register_next_step_handler(selected_level_message, selected_level_handler)


def selected_level_handler(message: Message):
    if check_is_command(message):
        return
    chat_id = message.chat.id
    answer = message.text
    prompt = ''
    answers_data = bot_info['questions_data'][1]['answers_data']
    for answer_data in answers_data:
        if answer == answer_data['button_answer']:
            prompt = answer_data['prompt']
    if not prompt:
        choice_gpt_params(message)
        return
    update_user_data(chat_id, 'level', prompt)
    user_data = get_user_data(chat_id)
    theme = user_data[2]
    bot.send_message(chat_id, f'Теперь можешь написать свой запрос на тему "{theme}", бот сформулирует ответ сложности '
                              f'объяснения "{prompt}"')


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


@bot.message_handler(content_types=['text'])
def question_handler(message: Message):
    chat_id = message.chat.id
    user_message = message.text
    update_user_data(chat_id, 'task', user_message)
    user_data = get_user_data(chat_id)
    theme_prompt = user_data[2]
    level_prompt = user_data[3]
    if not (theme_prompt and level_prompt):
        choice_gpt_params(message)
        return
    gpt_response = get_answer_from_gpt(user_message, theme_prompt, level_prompt)
    get_continue_answer = gpt_response['continue']

    def continue_message(next_message: Message):
        text = next_message.text
        if text == '/continue' and get_continue_answer:
            continue_answer = get_continue_answer()
            if continue_answer:
                last_answer = get_user_data(chat_id)[5]
                full_answer = f'{last_answer}{continue_answer}'
                update_user_data(chat_id, 'answer', full_answer)

                bot.send_message(chat_id, continue_answer)
                continue_user_message = bot.send_message(chat_id, 'Для продолжения ответа нажми /continue,\nили '
                                                                  'отправь следующий запрос')
                bot.register_next_step_handler(continue_user_message, continue_message)
            else:
                bot.send_message(chat_id, 'Мне больше нечего сказать...')
        else:
            question_handler(next_message)

    answer = gpt_response['answer']
    update_user_data(chat_id, 'answer', answer)
    bot.send_message(chat_id, answer)
    next_user_message = bot.send_message(chat_id, 'Для продолжения ответа нажми /continue,\nили отправь следующий '
                                                  'запрос')
    bot.register_next_step_handler(next_user_message, continue_message)


bot.polling()
