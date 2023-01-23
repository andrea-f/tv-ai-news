from flask import Flask, render_template,send_from_directory
import json, os, sys

app = Flask(__name__)
playlists_file = "groups_to_analyse__ukr.json__playlists.json"
#playlists_file = "groups_to_analyse__ukr.json__playlists_shortened.json"

with open(playlists_file, 'r') as f:
    video_list = json.loads(f.read())

@app.route('/')
def index():
    processed_video_list =[]
    for v in video_list:
        keywords = []
        for k in v["keywords"]:
            name = k["name"]

            if not name in keywords:
                keywords.append(name)
        v["keywords_list"] = ", ".join(keywords)

        if not "translated_text" in v or not v["translated_text"]:
            v["translated_text"] = ""
        processed_video_list.append(v)

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
    app.run()
