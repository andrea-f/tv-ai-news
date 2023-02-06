import os, sys, json
import saver
import s3_operations
import traceback
import telegram_tv_public_playlist

OUTPUT_DATA_BUCKET_NAME = os.getenv("OUTPUT_DATA_BUCKET_NAME", "telegram-output-data")
MIN_CONFIDENCE = 50

class TelegramTV:
    """
    Telegram TV code to create playlist and stats around videos/pics in messages
    """

    def __init__(self):
        pass

    def load_local_messages(self, messages_file):
        with open(messages_file, 'r') as f:
            messages = json.loads(f.read())
        return messages


    def generate_playlist(self, messages, group, filter_keywords=[]):
        playlist = []
        for message in messages:
            if "download_path" in message:
                item = {
                    "group_name": group["name"],
                    "group_id":message["peer_id"]["channel_id"],
                    "group_participants": group["participants_count"],
                    "group_icon": group["profile_photo"],
                    "category": group["category"],
                    "reactions": message["total_reactions"] if "total_reactions" in message else 0,
                    "source_link": message["id"],
                    "media_url": message["download_path"],
                    "text": message.get("message",""),
                    "translated_text": message["translated_message"] if "translated_message" in message else None,
                    "message_date": message["date"],
                    "s3_file_name": message["s3_file_name"],
                    "post_author": message["post_author"] if "post_author" in message and message["post_author"] else None,
                    "entities": message.get("entities_in_message", {}),
                    "sentiment": message.get("sentiment", {}),
                    "signature": message["signature"]
                }
                keywords = []
                unique_keywords = []
                if "keywords_found_in_image" in message:
                    try:
                        for i in message["keywords_found_in_image"].keys():
                            if "labels" in i:
                                for l in message["keywords_found_in_image"][i]:
                                    if l["Confidence"] > MIN_CONFIDENCE:
                                        if not l["Name"] in unique_keywords:
                                            keywords.append({
                                                "name": l["Name"]
                                            })
                                            if len(l["Parents"]) > 0:
                                                for p in l["Parents"]:
                                                    keywords.append({
                                                        "name": p["Name"]
                                                    })
                                            unique_keywords.append(l["Name"])
                            if "celebs" in i:
                                for v in message["keywords_found_in_image"][i]:
                                    if not v["Name"] in unique_keywords:
                                        keywords.append(
                                            {
                                                "name": v["Name"]
                                            }
                                        )
                                        unique_keywords.append(l["Name"])
                            if "text" in i:
                                for z in message["keywords_found_in_image"][i]:
                                    if not z["word"] in unique_keywords:
                                        keywords.append(
                                            {"name": z["word"]}
                                        )
                                        unique_keywords.append(z["word"])
                    except:
                        for i in message["keywords_found_in_image"]:
                            if i["Confidence"] > MIN_CONFIDENCE:
                                if not i["Name"] in unique_keywords:
                                    keywords.append({
                                        "name": i["Name"]
                                    })
                                    unique_keywords.append(i["Name"])
                                    if len(i["Parents"])>0:
                                        for p in i["Parents"]:
                                            if not p["Name"] in unique_keywords:
                                                keywords.append({
                                                    "name": p["Name"]
                                                })
                                                unique_keywords.append(p["Name"])

                    item["keywords"] = keywords
                if "keywords_found_in_video" in message:
                    celebs = message["keywords_found_in_video"]["celebs"]["celebs"]
                    if len(celebs)>0:
                        for c in celebs:

                            if not c["name"] in unique_keywords:
                                keywords.append({
                                    "name": c["name"],
                                    "timestamp": c["timestamp"]
                                })
                                unique_keywords.append(c["name"])
                    labels = message["keywords_found_in_video"]["labels"]["labels"]
                    for l in labels:
                        if l["confidence"] >= MIN_CONFIDENCE:

                            if not l["name"] in unique_keywords:
                                keywords.append({
                                    "name": l["name"],
                                    "timestamp": l["timestamp"]
                                })
                                unique_keywords.append(l["name"])
                    if "keywords" in item:
                        item["keywords"] = item["keywords"] + message["keywords_found_in_video"]
                    else:
                        item["keywords"] = keywords
                    try:
                        item["video_info"] = message["keywords_found_in_video"]["labels"]["video_info"]
                    except Exception as e:
                        print("Video info not found, message['keywords_found_in_video']['labels']:%s" % message["keywords_found_in_video"]["labels"].keys())

                if "views" in message:
                    item["views"] = message["views"]
                else:
                    item["views"] = None
                if "forwards" in message:
                    item["forwards"] = message["forwards"]
                else:
                    item["forwards"] = None
                if len(filter_keywords) > 0:
                    add = False
                    for k in filter_keywords:
                        if item["text"] and k in item["text"]:
                            add=True
                        if item["translated_text"] and k in item["translated_text"]:
                            add=True
                    if add:
                        playlist.append(item)
                else:
                    playlist.append(item)
        #print("Generated playlist with %s items for %s" % (len(playlist), group["name"]))
        playlists = sorted(playlist,key=lambda x: x.get("date", 0), reverse=True)
        # sort by reactions
        #playlists = sorted(playlists,key=lambda x: x["reactions"], reverse=True)
        saved_file, s3_saved_file = self.save_playlist(playlists, group['s3_processed_groups_file_name']+"__playlists.json")
        telegram_tv_public_playlist.lambda_handler(
            {
                "s3_processed_file":saved_file,
                "category": group["category"]
            }
        )
        return playlist


    def save_playlist(self, playlist, playlist_file):
        saved_file, s3_saved_file = saver.save_media(
            data=playlist, file_name=playlist_file, save_local_file=True, append=True, return_both=True
        )
        #print("Saved playlist file %s with %s items" % (saved_file, len(playlist)))
        return saved_file, s3_saved_file

    def get_playlist_duration(self, playlist, image_on_screen_duration_ms=5000):
        total_duration_ms = 0
        for item in playlist:
            if "video_info" in item:
                total_duration_ms += item["video_info"]["duration_ms"]
            else:
                total_duration_ms += image_on_screen_duration_ms
        return total_duration_ms/1000/60



if __name__ == "__main__":
    tgtv = TelegramTV()
    groups_file = sys.argv[1]
    if "s3://" in groups_file:
        groups_file = groups_file.replace("s3://%s/"%OUTPUT_DATA_BUCKET_NAME,"")
        groups = s3_operations.get_s3_file(OUTPUT_DATA_BUCKET_NAME, groups_file)
    else:
        with open(groups_file, 'r') as f:
            groups = json.loads(f.read())
    playlists = []
    for group in groups:
        try:
            messages = tgtv.load_local_messages(group["messages_file"])
        except Exception as e:

            print("Getting S3 file: %s" % (group["s3_messages_file_name"]))
            try:
                messages = s3_operations.get_s3_file(OUTPUT_DATA_BUCKET_NAME, group["s3_messages_file_name"])
            except:
                continue

        try:
            playlist = tgtv.generate_playlist(messages=messages,group=group)
            playlists += playlist
        except Exception as e:
            print("Error in genertaing playlists for %s: %s" % (group["messages_file"], e))
            traceback.print_exc()

    playlists = sorted(playlists,key=lambda x: x.get("date", 0), reverse=True)
    # sort by reactions
    #playlists = sorted(playlists,key=lambda x: x["reactions"], reverse=True)
    tgtv.save_playlist(playlists, groups_file+"__playlists.json")
    print("Total duration: %s minutes" % tgtv.get_playlist_duration(playlists))

