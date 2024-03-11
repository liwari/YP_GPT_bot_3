# для запуска проекта создайте файл config.py в корне проекта с объявлением нижеуказанных переменных

BOT_TOKEN = ''  # токен доступа к боту
BOT_ADMIN_ID = 1234567890  # идентификатор чата пользователя телеграмм с правами админа

GPT_MODEL = "mistralai/Mistral-7B-Instruct-v0.2-GGUF"  # название GPT модели
GPT_API_URL = ''  # url адрес api gpt
GPT_TEMPERATURE = 0.7  # gpt параметр
GPT_MAX_TOKENS = 2048  # gpt параметр
GPT_SYSTEM_CONTENT = "Ты ребенок."  # базовый промт для gpt
GPT_THEME = 'математика'  # математика / искусство
GPT_LEVEL = 'профи'  # математика / искусство
