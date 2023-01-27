import os, sys, json
import telegram_api
import media_analyser
OUTPUT_FOLDER_MESSAGES = os.getenv("OUTPUT_FOLDER_MESSAGES", "../messages/")



class TestTelegramAPITV:

    def test_telegram_login(self):
        tg = telegram_api.TelegramAPI()
        client = tg.login_to_telegram()
        assert client


    def test_check_message_already_downloaded(self):
        signature = "7efbfbeedf38f53342c6ed0c85c2b567"

        exists = media_analyser.check_message_already_downloaded(
            signature, OUTPUT_FOLDER_MESSAGES
        )

        assert exists