import os, sys, json
import telegram_api
import telegram_stats
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


    def test_telegram_stats(self):
        playlist_file_name = "./test-data/04-02-2023_18_02_17__groups_to_analyse__War in Ukraine__29.json__playlists.json__public.json"
        playlist_file_name = "./test-data/04-02-2023_18_02_17__groups_to_analyse__War in Ukraine__29.json__playlists.json__public.json"
        ts = telegram_stats.TelegramStats()
        stats, sentiments = ts.calculate_stats_messages(playlist_file_name)
        # print(json.dumps(stats,indent=4))
        # print(json.dumps(sentiments,indent=4))
        assert False
