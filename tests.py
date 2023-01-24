import os, sys, json
import telegram_api

class TestTelegramAPITV:

    def test_telegram_login(self):
        tg = telegram_api.TelegramAPI()
        client = tg.login_to_telegram()
        assert client

