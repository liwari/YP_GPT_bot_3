from data_base import get_user_data, get_messages_data


def convert_messages_data(messages_data: list):
    messages = []
    all_text = ''

    for message_data in messages_data:
        all_text = all_text + message_data['content'] + '\n'
        message = {
            'role': message_data['role'],
            'content': message_data['content'],
            'text': message_data['content']
        }
        messages.append(message)
    return {'messages': messages, 'all_text': all_text}


def get_story(messages_data: list):
    story_text = ''
    for message_data in messages_data:
        if message_data['role'] == 'assistant':
            story_text = story_text + message_data['content'] + '\n'
    return story_text


def get_messages_data_by_user_id(user_id: int):
    user_data = get_user_data(user_id)
    session_id = user_data['session_id']
    messages_data = get_messages_data(user_id, session_id)
    return messages_data
