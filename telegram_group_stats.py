import json

class TelegramGroupAnalysis:
    """
    Create stats from Telegram group messages.
    """

    def __init__(self):
        pass

    def read_file(self, telegram_messages_filename):
        with open(telegram_messages_filename, 'r') as f:
            telegram_messages_data = json.load(f.read())
        return telegram_messages_data

    def 