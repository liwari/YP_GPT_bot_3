import telebot
from telebot.types import Message, ReplyKeyboardMarkup, KeyboardButton
from config import BOT_TOKEN, BOT_ADMIN_ID, GPT_MAX_TOKENS
from gpt import get_answer_from_gpt, themes_prompts, levels_prompts
from log import get_log_file

bot = telebot.TeleBot(token=BOT_TOKEN)

bot.send_message(BOT_ADMIN_ID, f"бот был запущен")

gpt_params = {
    'theme': '',
    'level': ''
}


def make_keyboard(items):
    markup = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    for item in items:
        markup.add(KeyboardButton(item))

    return markup


@bot.message_handler(commands=['start'])
def start_command(message):
    chat_id = message.chat.id
    user_name = message.from_user.first_name
    buttons_labels = themes_prompts.keys()
    markup = make_keyboard(buttons_labels)
    bot.send_message(chat_id, f"Приветствую тебя, {user_name}!")

    select_theme_message = bot.send_message(chat_id, f"Для начала выберите тему вашего запроса:",
                                            reply_markup=markup)
    bot.register_next_step_handler(select_theme_message, selected_theme_handler)


def selected_theme_handler(message: Message):
    chat_id = message.chat.id
    gpt_params['theme'] = message.text
    buttons_labels = levels_prompts.keys()
    markup = make_keyboard(buttons_labels)

    selected_level_message = bot.send_message(chat_id, f"Теперь выбери сложность объяснения:",
                                              reply_markup=markup)
    bot.register_next_step_handler(selected_level_message, selected_level_handler)


def selected_level_handler(message: Message):
    chat_id = message.chat.id
    gpt_params['level'] = message.text

    bot.send_message(chat_id, f'Теперь можешь написать свой запрос на тему {gpt_params['theme']}, бот сформулирует ответ сложности '
                              f'объяснения "{gpt_params['level']}"')


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
    gpt_response = get_answer_from_gpt(user_message, gpt_params['theme'], gpt_params['level'])
    get_continue_answer = gpt_response['continue']

    def continue_message(next_message: Message):
        text = next_message.text
        if text == '/continue' and get_continue_answer:
            continue_answer = get_continue_answer()
            if continue_answer:
                bot.send_message(chat_id, continue_answer)
                continue_user_message = bot.send_message(chat_id, 'Для продолжения ответа нажми /continue,\nили '
                                                                  'отправь следующий запрос')
                bot.register_next_step_handler(continue_user_message, continue_message)
            else:
                bot.send_message(chat_id, 'Мне больше нечего сказать...')
        else:
            question_handler(next_message)

    answer = gpt_response['answer']
    bot.send_message(chat_id, answer)
    next_user_message = bot.send_message(chat_id, 'Для продолжения ответа нажми /continue,\nили отправь следующий '
                                                  'запрос')
    bot.register_next_step_handler(next_user_message, continue_message)


bot.polling()
