import os, sys, json
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
        print("Generating playlist from %s group from %s messages" % (group["name"], len(messages)))
        for message in messages:
            if "download_path" in message:
                item = {
                    "group_name": group["name"],
                    "group_participants": group["participants_count"],
                    "group_icon": group["group_image"],
                    "category": group["category"],
                    "reactions": message["total_reactions"] if "total_reactions" in message else 0,
                    "source_link": message["id"],
                    "media_url": message["download_path"],
                    "text": message["message"],
                    "translated_text": message["translated_message"] if "translated_message" in message else None,
                    "message_date": message["date"],
                    "s3_file_name": message["s3_file_name"],
                    "post_author": message["post_author"] if "post_author" in message and message["post_author"] else None
                }

                if "keywords_found_in_image" in message:
                    keywords = []
                    for i in message["keywords_found_in_image"]:
                        if i["Confidence"] > MIN_CONFIDENCE:
                            keywords.append({
                                "name": i["Name"]
                            })
                            if len(i["Parents"])>0:
                                for p in i["Parents"]:
                                    keywords.append({
                                        "name": p["Name"]
                                    })
                    item["keywords"] = keywords
                if "keywords_found_in_video" in message:
                    keywords = []
                    celebs = message["keywords_found_in_video"]["celebs"]["celebs"]
                    if len(celebs)>0:
                        for c in celebs:
                            keywords.append({
                                "name": c["name"],
                                "timestamp": c["timestamp"]
                            })
                    labels = message["keywords_found_in_video"]["labels"]["labels"]
                    for l in labels:
                        if l["confidence"] >= MIN_CONFIDENCE:
                            keywords.append({
                                "name": l["name"],
                                "timestamp": l["timestamp"]
                            })
                    if "keywords" in item:
                        item["keywords"] = item["keywords"] + message["keywords_found_in_video"]
                    else:
                        item["keywords"] = keywords
                    item["video_info"] = message["keywords_found_in_video"]["labels"]["video_info"]
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
        print("Generated playlist with %s items for %s" % (len(playlist), group["name"]))
        return playlist


    def save_playlist(self, playlist, playlist_file):
        with open(playlist_file, 'w') as f:
            f.write(json.dumps(playlist, indent=4))
        print("Saved playlist file %s with %s items" % (playlist_file, len(playlist)))

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

    groups_input = "groups_to_analyse__ukr.json__processed.json"
    with open(groups_input, 'r') as f:
        groups = json.loads(f.read())

    playlists = []
    for group in groups:
        messages = tgtv.load_local_messages(group["messages_file"])
        playlist = tgtv.generate_playlist(messages=messages,group=group)
        playlists += playlist

    tgtv.save_playlist(playlists, groups_input+"__playlists.json")
    print("Total duration: %s minutes" % tgtv.get_playlist_duration(playlists))

