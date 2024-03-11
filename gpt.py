from log import log_info, log_error
from config import (GPT_API_URL, GPT_TEMPERATURE, GPT_MAX_TOKENS, GPT_SYSTEM_CONTENT, GPT_MODEL, GPT_MAX_USER_TOKENS,
                    GPT_THEME, GPT_LEVEL)
import requests
# from transformers import AutoTokenizer
system_content = GPT_SYSTEM_CONTENT
theme = GPT_THEME
level = GPT_LEVEL


themes_prompts = {
                      'математика': 'Ты помощник по математике',
                      'искусство': 'Ты помощник по искусству',
                    }
levels_prompts = {
                      'новичок': 'давай простые ответы',
                      'профи': 'давай сложные ответы'
                    }


def generate_system_prompt_message(text: str):
    return {"role": "system", "content": text}


def generate_system_prompt_messages():
    system_prompt_messages = []
    if system_content:
        system_prompt_messages.append(generate_system_prompt_message(system_content))
    theme_prompt = themes_prompts.get(theme)
    if theme_prompt:
        system_prompt_messages.append(generate_system_prompt_message(theme_prompt))
    level_prompt = levels_prompts.get(level)
    if level_prompt:
        system_prompt_messages.append(generate_system_prompt_message(level_prompt))
    return system_prompt_messages


def count_tokens(text):
    # tokenizer = AutoTokenizer.from_pretrained(GPT_MODEL)
    # return len(tokenizer.encode(text))
    return len(text)


def gpt_post(messages: list[dict[str, str]]):
    return requests.post(GPT_API_URL,
                         headers={"Content-Type": "application/json"},
                         json={
                             "messages": messages,
                             "temperature": GPT_TEMPERATURE,
                             "max_tokens": GPT_MAX_TOKENS,
                         })


def get_answer_from_response(response):
    if response.status_code == 200:
        response_json = response.json()
        if 'choices' in response_json:
            return response_json['choices'][0]['message']['content']
        else:
            log_error("Не обнаружено 'choices'")
            return f'Не удалось получить ответ от нейросети.'
    else:
        log_error(f'Код ошибки {response.status_code}')
        return f'Произошла ошибка ({response.status_code}). Попробуйте отправить запрос заново'


def get_answer_from_gpt(question: str):
    log_info(f"Запрос пользователя: {question}")
    messages = []
    system_messages = generate_system_prompt_messages()
    messages.extend(system_messages)
    messages.append({"role": "user", "content": question})
    tokens_number = count_tokens(question)
    if tokens_number > GPT_MAX_USER_TOKENS:
        log_error(f'Превышено допустимое количество токенов запроса пользователя: {tokens_number} > {GPT_MAX_USER_TOKENS}')
        return {"answer": 'Запрос не принят.\nДлина запроса превышает допустимое значение.\nОтправьте запрос '
                          'повторно', "continue": None}
    response = gpt_post(messages)
    answer = get_answer_from_response(response)
    messages.append({"role": "assistant", "content": answer})

    def continue_answer():
        next_response = gpt_post(messages)
        next_answer = get_answer_from_response(next_response)
        messages.append({"role": "assistant", "content": next_answer})
        return next_answer

    return {"answer": answer, "continue": continue_answer}
