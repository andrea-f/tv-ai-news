
import json, os, sys
import time

import boto3
from datetime import datetime

from functools import wraps
MAX_PLAYLISTS_ITEMS_TO_RETURN_IN_BATCH = os.getenv("MAX_PLAYLISTS_ITEMS_TO_RETURN_IN_BATCH", 150)
OUTPUT_DATA_BUCKET_NAME = os.getenv("OUTPUT_DATA_BUCKET_NAME", "telegram-output-data")
SAVE_DIR = os.getenv("SAVE_DIR", "/tmp/")
BOTO_CONFIG=os.getenv("BOTO_CONFIG", "creds_aws")

class TVOperations:
    """
    Helper functions to run Cyber-Monitor TV platform.
    """

    def __init__(self, category=None):
        self.playlists_file_name = self._get_new_playlist_file_from_s3(category=category)
        video_list_data_start = self._get_latest_playlist_file_contents_from_s3(self.playlists_file_name)
        self.playlist = self._process_video_list(video_list_data_start)


    def _process_video_list(self,video_list):
        media_urls = []
        processed_video_list =[]
        for v in video_list:
            keywords = []
            if "keywords" in v:
                for k in v["keywords"]:
                    name = k["name"]
                    if not name in keywords:
                        name = ''.join(e for e in name if e.isalnum() or e==' ')
                        keywords.append(name)
            v["keywords_list"] = ", ".join(keywords)
            if "sentiment" in v and "sentiment" in v["sentiment"]:
                v["sentiment_word"] = v["sentiment"]["sentiment"]

            if "entities" in v:
                entities = ["ORGANIZATION", "PERSON", "LOCATION", "OTHER", "COMMERCIAL_ITEM", "TITLE"]
                v["entities_list"] = []
                for e in v["entities"]:
                    ent = e["Text"].replace("\n","")
                    if e["Type"] in entities and not ent in v["entities_list"]:
                        if not "http" in ent:
                            v["entities_list"].append(ent)
                v["entities_list"] = ", ".join(v["entities_list"])
            if not "translated_text" in v or not v["translated_text"]:
                v["translated_text"] = ""

            if "public_media_url" in v:
                v["media_url"] = v["public_media_url"]

            # convert date to d/m/Y
            v = self._datetime_converter_to_timestamp(v)
            if not v["public_media_url"] in media_urls:
                processed_video_list.append(v)
                media_urls.append(v["public_media_url"])
        video_list_by_date = sorted(
            processed_video_list,
            key=lambda x: x["timestamp"],
            reverse=True
        )

        print(json.dumps(video_list_by_date[0]["message_date"]))

        #video_list_by_reactions = sorted(processed_video_list,key=lambda x: x["reactions"], reverse=True)
        #return processed_video_list, video_list_by_date, video_list_by_reactions
        return video_list_by_date

    def _datetime_converter_to_timestamp(self, v):
        try:
            v["timestamp"] = datetime.strptime(v["message_date"], '%d/%m/%Y, %H:%M:%S').timestamp()
        except:
            date_pieces = v["message_date"].split("/")
            v["message_date"] = "%s/%s/%s"% (date_pieces[1], date_pieces[0], date_pieces[2])
            v["timestamp"] = datetime.strptime(v["message_date"], '%d/%m/%Y, %H:%M:%S').timestamp()
        date_now_timestamp = time.time()
        if v["timestamp"] > int(date_now_timestamp):
            date_pieces = v["message_date"].split("/")
            v["message_date"] = "%s/%s/%s"% (date_pieces[1], date_pieces[0], date_pieces[2])
            v["timestamp"] = datetime.strptime(v["message_date"], '%d/%m/%Y, %H:%M:%S').timestamp()
        return v


    def _list_files_in_bucket(self,bucket_name, subfolder="playlists/", word_in_filename=None):
        s3 = boto3.resource('s3')
        my_bucket = s3.Bucket(bucket_name)
        files = []
        for object_summary in my_bucket.objects.filter(Prefix=subfolder):
            if word_in_filename:
                if word_in_filename.lower() in object_summary.key.lower():
                    files.append(object_summary)
            else:
                files.append(object_summary)

        try:
            files = [obj.key for obj in sorted(files, key=lambda x: x.last_modified,reverse=True)]
            if len(files)>2:
                files = files[0:2]
        except:
            files = [files[0].key]

        return files



    def _get_s3_file(self,bucket_name, filename, save_dir=None):
        if not save_dir:
            save_dir = SAVE_DIR
        if not bucket_name:
            raise Exception("No bucket name!")
        session = boto3.Session()
        s3_client = session.client("s3")
        filename_only = filename.split("/")[-1]
        s3_client.download_file(bucket_name, filename, "%s/%s" % (save_dir,filename_only))
        with open("%s/%s" % (save_dir,filename_only), "r") as f:
            if filename.endswith(".json"):
                file_contents = json.loads(f.read())
            elif filename.endswith(".csv"):
                file_contents = f.readlines()
            return file_contents

    def _get_new_playlist_file_from_s3(self,current_playlist_file=None, category=None):
        files = self._list_files_in_bucket(OUTPUT_DATA_BUCKET_NAME, word_in_filename=category)
        # Get latest playlist file
        playlists_file = files[0]
        if current_playlist_file and current_playlist_file==playlists_file:
            return None
        else:
            return playlists_file

    def _get_latest_playlist_file_contents_from_s3(self,playlists_file):
        print("Selected playlist file: %s" % playlists_file)
        video_list_data = self._get_s3_file(OUTPUT_DATA_BUCKET_NAME, playlists_file)
        print("Retrieved playslist file with %s items" % len(video_list_data))
        return video_list_data

    def get_local_playlist_file(self,playlists_file):
        with open(playlists_file, 'r') as f:
            video_list_data = json.loads(f.read())
            return video_list_data

    def save_file(self,bucket_name, file_name, s3_file_name):
        try:
            session = boto3.Session()
            s3_client = session.client("s3")
            # Upload the file to the S3 bucket
            s3_client.upload_file(file_name, bucket_name, s3_file_name)
            print("Loaded to S3 bucket %s the file: %s" % (bucket_name, file_name))
            return s3_file_name
        except Exception as e:
            print("Error in saving to S3 bucket %s the file %s: %s" % (bucket_name, file_name, e))
            return None


    def get_processed_video_list(self, range_from=0,batch_number=0, limit_returned_playlist_size=False, category=None, force_refetch=False):
        latest_playlists_file_name = self._get_new_playlist_file_from_s3(category=category)
        if force_refetch:
            self.playlists_file_name = ""
        if latest_playlists_file_name != self.playlists_file_name:
            print("Fetching new playlist: %s" % latest_playlists_file_name)
            self.playlists_file_name = latest_playlists_file_name
            video_list_data = self._get_latest_playlist_file_contents_from_s3(self.playlists_file_name)
            self.playlist = self._process_video_list(video_list_data)
        range_from = (MAX_PLAYLISTS_ITEMS_TO_RETURN_IN_BATCH * batch_number) + range_from
        total_items = len(self.playlist)
        if range_from > len(self.playlist)-1:
            range_from = 0
        if limit_returned_playlist_size:
            range_to = range_from + MAX_PLAYLISTS_ITEMS_TO_RETURN_IN_BATCH
            if range_to > len(self.playlist)-1:
                range_to = len(self.playlist)-1
        else:
            range_to = len(self.playlist)-1
        if len(self.playlist)>0:
            playlist_segment = self.playlist[range_from:range_to]
        else:
            playlist_segment = self.playlist
        return playlist_segment, self.playlists_file_name, total_items, range_from, batch_number+1



