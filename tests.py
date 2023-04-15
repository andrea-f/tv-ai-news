import os, sys, json
import telegram_api
import telegram_stats
import media_analyser
import saver
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


    def test_save_group(self):
        group = {
            "name": "Cyber security research academy",
            "date": None,
            "entity": {
                "_": "Channel",
                "id": 1761003953,
                "title": "Cyber security research academy",
                "photo": {
                    "_": "ChatPhoto",
                    "photo_id": 6084695050761122177,
                    "dc_id": 5,
                },
                "access_hash": 8682239036210658169,
                "username": "cybersra",
                "participants_count": 1062,
                "usernames": []
            },
            "original_name_language": "en",
            "profile_photo": "media/Odessa Course___1130291425/Odessa Course__1130291425__profile_image.jpg"
        }
        saved_group = saver.save_media(data=group, data_type="group")
        assert saved_group
