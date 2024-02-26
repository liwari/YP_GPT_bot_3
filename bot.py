import telebot
from telebot.types import Message
from config import BOT_TOKEN, BOT_ADMIN_ID, GPT_MAX_TOKENS
from gpt import get_answer_from_gpt
from log import get_log_file

bot = telebot.TeleBot(token=BOT_TOKEN)

bot.send_message(BOT_ADMIN_ID, f"бот был запущен")


@bot.message_handler(commands=['start'])
def start_command(message):
    chat_id = message.chat.id
    user_name = message.from_user.first_name
    bot.send_message(chat_id, text=f"Приветствую тебя, {user_name}!\nМожешь написать мне свой запрос ниже")


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
    gpt_response = get_answer_from_gpt(user_message)
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
