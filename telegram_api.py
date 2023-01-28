import os, json, sys
import datetime
import saver
import media_analyser
import traceback
# importing all required libraries
#from telethon.sync import TelegramClient
from telethon.tl.types import InputPeerUser, InputPeerChannel
from telethon import TelegramClient, sync, events
import s3_operations
import time
import argparse
from datetime import datetime
from datetime import date
import hashlib

STOP_AT_MAX_DATE = os.getenv("STOP_AT_MAX_DATE", "true")
OUTPUT_DATA_BUCKET_NAME = os.getenv("OUTPUT_DATA_BUCKET_NAME", "telegram-output-data")
OUTPUT_FOLDER_NAME = os.getenv("OUTPUT_FOLDER_NAME", "../media/")
OUTPUT_FOLDER_MESSAGES = os.getenv("OUTPUT_FOLDER_MESSAGES", "../messages/")
GROUP_FILE_NAME = os.getenv("GROUP_FILE_NAME", "groups.json")
CREDENTIALS_FILE = os.getenv("CREDENTIALS_FILE", "creds.json")
FORCE_REDOWNLOAD = os.getenv("FORCE_REDOWNLOAD", "no")
UNIQUE_SIGNATURES_FILE_NAME = os.getenv("UNIQUE_SIGNATURES_FILE_NAME", "unique_signatures.csv")

def date_format(message):
    """
    :param message:
    :return:
    """
    if type(message) is datetime:
        return message.strftime("%Y-%m-%d %H:%M:%S")



# Use your own values from my.telegram.org
with open(CREDENTIALS_FILE, 'r') as f:
    creds = json.loads(f.read())
    api_id = int(creds["api_id"])
    api_hash = creds["api_hash"]
    username = creds["username"]
    phone = creds["phone"]
    aws_s3_role_arn = creds["aws_s3_role_arn"]



class TelegramAPI:
    """
    Logs in Telegram via API id and hash.
    Gets groups of users.
    For each group if its in a list the last X messages are downloaded including media locally and s3.
    """

    def __init__(self):
        self.client = None


    def login_to_telegram(self, ):
        # The first parameter is the .session file name (absolute paths allowed)
        if not self.client:
            token = 'bot token'
            message = "Working..."

            # creating a telegram session and assigning
            # it to a variable client
            client = TelegramClient('session', api_id, api_hash)

            # connecting and building the session
            client.connect()

            # in case of script ran first time it will
            # ask either to input token or otp sent to
            # number or sent or your telegram id
            if not client.is_user_authorized():

                client.send_code_request(phone)

                # signing in the client
                client.sign_in(phone, input('Enter the code: '))
            return client


    def send_message(self, client, message="Working!"):
        try:
            # receiver user_id and access_hash, use
            # my user_id and access_hash for reference
            receiver = InputPeerUser(api_id, api_hash)

            # sending message using telegram client
            client.send_message(username, message, parse_mode='html')
        except Exception as e:
            # there may be many error coming in while like peer
            # error, wrong access_hash, flood_error, etc
            print(e)
            traceback.print_stack()
        client.disconnect()


    def get_groups(self, client):
        groups_obj = []
        try:
            c=0
            groups = client.get_dialogs()
            for group in groups:

                name = group.name.replace("&", "e").replace("/","_")
                date = group.date
                message = group.message.to_dict()
                entity = group.entity.to_dict()
                channel_id = entity["id"]
                g = {
                    "name": name,
                    "date": date,
                    "message": message,
                    "entity": entity,
                }
                language = media_analyser.detect_text_language(name)
                g["original_name_language"] = language
                if not "en" == language:
                    translated_message = media_analyser.translate_text(name, language_source=language)
                    if translated_message:
                        g["name"] = translated_message
                        g["original_name"] = name
                # Save profile photo
                media_fn = "../media/%s___%s/"%(g["name"], channel_id)
                profile_file_name = g["name"]+"__"+str(channel_id)+"__profile_image.jpg"
                g["local_profile_photo"]= media_fn+profile_file_name
                # Download the group's profile photo and save it to a file
                file = client.download_profile_photo(channel_id, file=media_fn+profile_file_name)
                g["profile_photo"]=saver.save_media(file_name=media_fn+profile_file_name, save_local_file=False)
                print("group name: ", g['name'], c, len(groups))
                groups_obj.append(g)

                c+=1
        except Exception as e:
            print("Error in fetching groups: %s" % e)
            traceback.print_exc()

        # disconnecting the telegram session
        client.disconnect()
        saved_file_name = saver.save_media(groups_obj, GROUP_FILE_NAME)
        print("Saved %s groups in %s" % (len(groups_obj), saved_file_name))
        return groups_obj


    def _get_messages(self, client, channel_id, limit=100, channel_name=None, analyse_media=True, max_date=None, stop_at_max_date=STOP_AT_MAX_DATE, force_redownload=FORCE_REDOWNLOAD):
        messages = []
        count = 0
        if stop_at_max_date=="false":
            stop_at_max_date = False
        elif stop_at_max_date=="true":
            stop_at_max_date=True
        #group = client.get_entity('group_username')



        # set to todays date to filter only latest messages
        if max_date and "today" == max_date:
            #max_date = datetime.now()
            today = date.today()
            max_date = datetime.combine(today, datetime.min.time())
            #max_date = today.strftime("%d/%m/%Y")
        if channel_name:
            media_fn = OUTPUT_FOLDER_NAME+"%s___%s/" % (channel_name, channel_id)
            fn = OUTPUT_FOLDER_MESSAGES + 'messages__%s___%s.json' % (channel_name, channel_id)
        else:
            media_fn = OUTPUT_FOLDER_NAME+"%s/" % channel_id
            fn = OUTPUT_FOLDER_MESSAGES + 'messages__%s.json' % channel_id
        s3_messages_file_name = fn.replace("../", "")
        try:
            unique_signatures = s3_operations.get_s3_file(OUTPUT_DATA_BUCKET_NAME, UNIQUE_SIGNATURES_FILE_NAME, "")
            unique_signatures = [u.replace("\n", "") for u in unique_signatures if len(u)>0]
            print("Loaded %s unique signatures!" % len(unique_signatures))

        except Exception as e:
            print("Did not get unique_signatures file: %s/%s because %s" % (OUTPUT_DATA_BUCKET_NAME, UNIQUE_SIGNATURES_FILE_NAME, e))
            raise Exception("Signatures file not found: %s" % e)

        try:
            for message in client.get_messages(channel_id, limit=limit):
                if max_date and stop_at_max_date:
                    try:
                        max_date_obj = datetime.strptime(max_date, '%d/%m/%Y')
                    except:
                        max_date_obj = max_date
                    if max_date_obj.timestamp() > message.date.timestamp():
                        continue


                message_obj = message.to_dict()

                # get message date
                message_obj['date'] = message.date.strftime("%m/%d/%Y, %H:%M:%S")

                # get message signature
                unique_str = "%s%s%s" % (message_obj.get("message", ""), message_obj['date'], channel_id)
                message_obj["signature"] = hashlib.md5(unique_str.encode('utf-8', errors="ignore")).hexdigest()

                # check if message has already been processed
                if not force_redownload == "yes":
                    # message_exists = media_analyser.check_message_already_downloaded(message_obj["signature"])
                    # if message_exists:
                    if message_obj["signature"] in unique_signatures:
                        print("Message %s already processed" % message_obj["signature"])
                        continue


                # get message media, might be more than one item
                try:
                    download_path = message.download_media(file=media_fn)
                except Exception as e:
                    print("Error in downloading media from Telegram for %s: %s" % (media_fn, e))
                    download_path = None
                if download_path:
                    message_obj['download_path'] = download_path
                    # save downloaded media to S3
                    s3_file_name=saver.save_media(file_name=download_path, save_local_file=False)
                    message_obj["s3_file_name"] = s3_file_name

                    # get keywords from video and images
                    if analyse_media:
                        print("Processing for content analysis: %s" % download_path)
                        if download_path.endswith(".jpg") or download_path.endswith(".png"):
                            message_obj["keywords_found_in_image"] = media_analyser.get_keywords_image(download_path)
                        elif download_path.lower().endswith(".mp4"):
                            message_obj["keywords_found_in_video"] = media_analyser.get_keywords(OUTPUT_DATA_BUCKET_NAME, s3_file_name, aws_s3_role_arn)

                # translate text if its not english
                if "message" in message_obj and len(message_obj["message"])>0:
                    message_obj["message"] = message_obj["message"].replace("\n", " ")
                    # detect language of text
                    language = media_analyser.detect_text_language(message_obj["message"])
                    message_obj["original_message_language"] = language
                    if not "en" == language:
                        translated_message = media_analyser.translate_text(message_obj["message"], language_source=language)
                        if len(translated_message)>0:
                            message_obj["original_message"] = message_obj["message"]
                            message_obj["message"] = translated_message

                    # detect entities in the text
                    message_obj["entities_in_message"] = media_analyser.detect_entities(message_obj["message"])

                    # detect sentiment of the text
                    message_obj["sentiment"] = media_analyser.detect_sentiment(message_obj["message"])

                # count reactions
                total_reactions = None
                if ("reactions" in message_obj.keys() and
                    message_obj["reactions"] and
                    "results" in message_obj["reactions"].keys() and
                    len(message_obj["reactions"]["results"])>0
                ):
                    total_reactions = 0
                    reactions = message_obj["reactions"]["results"]
                    for r in reactions:
                        total_reactions += r["count"]
                if total_reactions:
                    message_obj["total_reactions"] = total_reactions

                messages.append(message_obj)
                print(
                    "message text: ",
                    message_obj["translated_message"][:15] if "translated_message" in message_obj else message_obj["message"][:15] if "message" in message_obj else "",
                    message_obj["date"],
                    str(count)+"/"+str(limit)
                )
                count += 1
                unique_signatures.append(message_obj["signature"])
                saver.save_media("\n".join(unique_signatures), UNIQUE_SIGNATURES_FILE_NAME)
                local_messages_file_name, s3_messages_file_name = saver.save_media(message_obj, fn, return_both=True, append=True)
        except Exception as e:
            print("Error in parsing messages: %s" %e)
            traceback.print_exc()
            s3_messages_file_name = None
        if len(messages)>0:
            print("Parsed %s messages from %s, saved to: %s" % (len(messages), channel_name, fn))
        else:
            print("No new messages for %s " % channel_name)
        return messages, fn, s3_messages_file_name


    def get_messages_from_groups(self, group_file=None, group_list=[]):
        if group_file:
            if group_file.startswith("s3"):
                s3_filename = group_file.replace("s3://%s/"%OUTPUT_DATA_BUCKET_NAME,"")
                groups = s3_operations.get_s3_file(OUTPUT_DATA_BUCKET_NAME, s3_filename)
            else:
                with open(group_file, 'r') as f:
                    groups = json.loads(f.read())
            print("Loaded %s groups from %s " % (len(groups), group_file))
        elif len(group_list)>0:
            groups = group_list
        else:
            raise Exception("No groups passed in!")
        c=0
        start = time.monotonic()
        total_messages = 0
        processed_groups = []
        try:
            for group in groups:
                group_id = group["id"]
                group_name = group["name"]
                print("Fetching messages from group: %s (%s)..." % (group_name, group_id))
                messages, fn, s3_messages_file_name = self._get_messages(
                    client,
                    group_id,
                    channel_name=group_name,
                    limit=group["max_past_messages"],
                    analyse_media=group["analyse_media"],
                    max_date=group["max_past_date"]
                )
                print("Fetched %s messages for group %s %s/%s" % (len(messages), group_name, c, len(groups)))
                total_messages += len(messages)
                group["messages_file"] = fn
                group["s3_messages_file_name"] = s3_messages_file_name
                group["participants_count"], group["profile_photo"] = self._get_groups_participants_and_profile_image(group_id)
                processed_groups.append(group)

                local_file_name, s3_file_name = saver.save_media(processed_groups, group_file+"__processed.json", return_both=True)

                #print("Saved: ", s3_file_name, " and messages file: ", s3_messages_file_name)
                c+=1
        except Exception as e:
            print("Error in processing groups: %s" % e)
            traceback.print_exc()

        saver.save_media(processed_groups, group_file+"__processed.json")
        finish = time.monotonic()
        elapsed = (finish - start) / 60
        print("Processed %s groups and %s messages in %s minutes" % (len(groups), total_messages, elapsed))


    def _get_groups_participants_and_profile_image(self, group_id, groups_file=None):
        if not groups_file:
            groups_file = GROUP_FILE_NAME
        if groups_file.startswith("s3"):
            s3_filename = groups_file.replace("s3://%s/"%OUTPUT_DATA_BUCKET_NAME,"")
            groups = s3_operations.get_s3_file(OUTPUT_DATA_BUCKET_NAME, s3_filename)
        else:
            with open(groups_file, 'r') as f:
                groups = json.loads(f.read())
        for group in groups:
            if group_id == group["entity"]["id"]:
                return group["entity"]["participants_count"], group["profile_photo"]
        return None, None


if __name__ == "__main__":
    tg = TelegramAPI()
    client = tg.login_to_telegram()

    parser = argparse.ArgumentParser()
    parser.add_argument("-g", "--groups", action="store_true",
                        help="Fetches all groups joined by the logged in user and saves it in JSON file")
    parser.add_argument("-m", "--messages", action="store",
                        help="Gets messages from the groups in the JSON file.")

    parser.add_argument("-f", "--fileWithAnalysedMessages",help="use already present message files with analysed data", action="store")

    args = parser.parse_args()
    print(args)
    if args.groups:
        groups = tg.get_groups(client)


    if args.messages and len(args.messages) > 0:
        # process group file
        groups_to_analyse_file = args.messages
        tg.get_messages_from_groups(group_file=groups_to_analyse_file)


    if args.fileWithAnalysedMessages:
        pass


    # process group list
    # groups = [{
    #     "name": "ULTRAS MENTALITY",
    #     "id": 1147727897,
    #     "analyse_media": True,
    #     "max_past_messages": 100,
    #     "category": "ultras",
    #     "max_past_date": "1/1/2023"
    # }]
    # tg.get_messages_from_groups(group_list=groups)


