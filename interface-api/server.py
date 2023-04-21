from flask import Flask, render_template,send_from_directory, request
import time
import json, os, sys
import boto3

OUTPUT_DATA_BUCKET_NAME = os.getenv("OUTPUT_DATA_BUCKET_NAME", "telegram-output-data")


import tv_operations

app = Flask(__name__)
playlists_file = "groups_to_analyse__ukr.json__playlists.json"
#playlists_file = "groups_to_analyse__ukr.json__playlists_shortened.json"
playlists_file = "../data/groups_to_analyse__ultras.json__processed.json__playlists.json"
playlists_file = "../data/groups_to_analyse__ukr.json__processed.json__playlists.json"
playlists_file= "../data/groups_to_analyse__ukr.json__processed.json__playlists.json"
playlists_file= "groups_to_analyse__russia.json__processed.json__playlists.json"
playlists_file = "26-01-2023_01_13_10__groups_to_analyse__-__18.json__processed.json__playlists.json__public.json"
playlists_file = "27-01-2023_20_11_34__groups_to_analyse__-__18.json__processed.json__playlists.json__public.json"
playlists_file = "ukraine.json"


received_requests = {}

category = "ukraine"
tv_ops = tv_operations.TVOperations(category)

@app.before_request
def check_ip():
    #print(request)
    ###  Here I need the IP address and port of the client
    ip = request.environ['REMOTE_ADDR']
    # print("The client IP is: {}".format(ip))
    # print("The client port is: {}".format(request.environ['REMOTE_PORT']))
    item = {
        "method": request.method,
        "path": request.path
    }

    try:
        item["data"] = str(request.get_data())
    except Exception as e:
        print("Error in setting request data from %s: %s" % (ip, e))
        item["data"] = None

    try:
        received_requests[ip].append(item)
    except:
        received_requests[ip] = [item]

    if len(received_requests.keys()) % 50 == 0:
        fn = "connections_received.json"
        s3_folder = "flask-connections"
        with open("/tmp/%s" % fn, 'w') as f:
            f.write(json.dumps(received_requests, indent=4))
            print("Saved %s requests" % len(received_requests.keys()))
        tv_ops.save_file(OUTPUT_DATA_BUCKET_NAME, "/tmp/%s" % fn, s3_folder +"/" + fn)




def get_playlist_items_from_file_name(playlists_file_name):
    playlists_parts = playlists_file_name.split("/")[-1].split("__")
    try:
        playlist_date = playlists_parts[0].split("_")[0]
        category = playlists_parts[2].replace("_", " ")
        if len(category) < 2:
            category = None
    except Exception as e:
        print("Error in getting parts from playlists file %s: %s" % (playlists_file_name, e))
        playlist_date = time.time()
        category = None

    return {
        "category": category,
        "playlist_date": playlist_date
    }


@app.route('/')
def index():

    # Calls tv operations
    processed_video_list, \
    playlists_file_name, \
    total_items,\
    current_item, \
    batch_number = tv_ops.get_processed_video_list(limit_returned_playlist_size=True, category=category)
    playlist_metadata = get_playlist_items_from_file_name(playlists_file_name)
    batch_number = 0
    current_item=0
    return render_template('index.html',
                           video_list=processed_video_list,
                           batch_number=batch_number,
                           playlist_date=playlist_metadata["playlist_date"],
                           category=playlist_metadata["category"],
                           total_items=total_items,
                           current_item=current_item
                           )

@app.route('/news/<string:category_input>')
@app.route('/news/<string:category_input>/<string:filter>')
@app.route('/news/<string:category_input>/<string:filter>/<string:item_number>/')
def get_next_videos(category_input, filter=None, item_number=None):
    print(category_input, filter, item_number)
    if "live" in filter or not filter:
        try:
            item_numbers = item_number.split("-")
            batch_number = int(item_numbers[0])
            if batch_number > 100:
                batch_number=100
            video_index = int(item_numbers[1])
        except:
            batch_number = 0
            video_index = 0
        if "latest" in filter:
            force_playlist_refetch=True
        else:
            force_playlist_refetch=False
        print("Requested: %s-%s" % (batch_number, video_index))
        processed_video_list, \
        playlists_file_name,\
        total_items, \
        current_item, \
        batch_number = tv_ops.get_processed_video_list(
            video_index, batch_number,
            limit_returned_playlist_size=True,
            category=category_input.replace("-", " "),
            force_refetch=force_playlist_refetch
        )
        playlist_metadata = get_playlist_items_from_file_name(playlists_file_name)
        return render_template('index.html',
                               video_list=processed_video_list,
                               playlist_date=playlist_metadata["playlist_date"],
                               category=playlist_metadata["category"],
                               batch_number=batch_number,
                               total_items=total_items,
                               current_item=current_item
                               )


@app.route('/static/<path:path>')
def send_report(path):
    return send_from_directory('static', path)

@app.route('/media/<path:path>')
def send_media(path):
    dir = path.split("/")
    d = "/".join(dir[:-1])
    p = dir[-1]
    d = "../media/%s" % d
    #print(path)
    #print(d, p)
    return send_from_directory(d, p)

if __name__ == '__main__':
    try:
        port = sys.argv[1]
    except:
        port = 5000
    app.run(host="0.0.0.0", port=port)
