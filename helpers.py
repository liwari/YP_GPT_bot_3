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
