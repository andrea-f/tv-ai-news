from flask import Flask, render_template,send_from_directory
import json, os, sys

app = Flask(__name__)
playlists_file = "groups_to_analyse__ukr.json__playlists.json"
#playlists_file = "groups_to_analyse__ukr.json__playlists_shortened.json"
playlists_file = "../data/groups_to_analyse__ultras.json__processed.json__playlists.json"
playlists_file = "../data/groups_to_analyse__ukr.json__processed.json__playlists.json"
playlists_file= "../data/groups_to_analyse__ukr.json__processed.json__playlists.json"
playlists_file= "groups_to_analyse__russia.json__processed.json__playlists.json"
playlists_file = "26-01-2023_01_13_10__groups_to_analyse__-__18.json__processed.json__playlists.json__public.json"

def process_video_list(video_list):
    processed_video_list =[]
    for v in video_list:
        keywords = []
        if "keywords" in v:
            for k in v["keywords"]:
                name = k["name"]
                if not name in keywords:
                    keywords.append(name)
        v["keywords_list"] = ", ".join(keywords)
        if "sentiment" in v and "sentiment" in v["sentiment"]:
            v["sentiment_word"] = v["sentiment"]["sentiment"]

        if "entities" in v:
            entities = ["ORGANIZATION", "PERSON", "LOCATION", "OTHER", "COMMERCIAL_ITEM", "TITLE"]
            v["entities_list"] = ", ".join([e["Text"].replace("\n","") for e in v["entities"] if e["Type"] in entities])
        if not "translated_text" in v or not v["translated_text"]:
            v["translated_text"] = ""

        if "public_media_url" in v:
            v["media_url"] = v["public_media_url"]

        processed_video_list.append(v)


    video_list_by_date = sorted(processed_video_list,key=lambda x: x["message_date"], reverse=True)
    video_list_by_reactions = sorted(processed_video_list,key=lambda x: x["reactions"], reverse=True)
    return processed_video_list, video_list_by_date, video_list_by_reactions

with open(playlists_file, 'r') as f:
    video_list_data = json.loads(f.read())

processed_video_list, video_list_by_date, video_list_by_reactions = process_video_list(video_list_data)





@app.route('/')
def index():


    return render_template('index2.html', video_list=processed_video_list)

@app.route('/static/<path:path>')
def send_report(path):
    return send_from_directory('static', path)

@app.route('/media/<path:path>')
def send_media(path):
    dir = path.split("/")
    d = "/".join(dir[:-1])
    p = dir[-1]
    d = "../media/%s" % d
    print(path)
    print(d, p)
    return send_from_directory(d, p)

if __name__ == '__main__':
    try:
        port = sys.argv[1]
    except:
        port = 5000
    app.run(port=port)
