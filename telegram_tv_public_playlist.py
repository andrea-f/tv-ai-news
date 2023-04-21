import boto3
import json
import sys
import os
import botocore
import hashlib
OUTPUT_DATA_BUCKET_NAME = os.getenv("OUTPUT_DATA_BUCKET_NAME", "telegram-output-data")

CDN_BUCKET_NAME = os.getenv("CDN_BUCKET_NAME", "cloudfront-tv-ai-news")
CDN_PUBLIC_DOMAIN = os.getenv("CDN_PUBLIC_DOMAIN", "https://dv2qvx24vgmrl.cloudfront.net")

def get_s3_file(bucket_name, filename, save_dir="/tmp/"):
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
        else:
            file_contents = f.read()
        return file_contents


def list_files_in_bucket(bucket_name, subfolder="playlists/", word_in_filename=None):
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

class LoadedPlaylistFile:

    def __init__(self):
        self.already_existing_playlist_items = None


    def load(self, category):
        if not self.already_existing_playlist_items:
            try:
                fn = list_files_in_bucket(OUTPUT_DATA_BUCKET_NAME,word_in_filename=category)[0]
                self.already_existing_playlist_items = get_s3_file(OUTPUT_DATA_BUCKET_NAME, fn)
                print("Loaded %s files from %s" % (len(self.already_existing_playlist_items), fn))
            except Exception as e:
                print("Error in fetching already existing playlist: %s" % e)
                self.already_existing_playlist_items = []
        return self.already_existing_playlist_items


lpf = LoadedPlaylistFile()


def lambda_handler(event, context=None):
    files = get_s3_files()
    #print("Loaded %s files from %s" % (len(files), CDN_BUCKET_NAME))
    if "Cause" in event:
        event = json.loads(event["Cause"])
    try:
        commands = event["Overrides"]["ContainerOverrides"]
        s3_processed_file = None
        for c in commands:
            for v in c["Command"]:
                if "processed" in v:
                    s3_processed_file = v
    except:
        #print(json.dumps(event, indent=True))
        s3_processed_file = event.get("s3_processed_file", None)

    if s3_processed_file:
        if not "__playlists" in s3_processed_file:
            playlist_file = s3_processed_file+"__playlists.json"
        else:
            playlist_file = s3_processed_file
    else:
        raise Exception("File to process not found in %s" % json.dumps(event["Overrides"], indent=4))

    if "s3://" in playlist_file:
        bucket_name= playlist_file.replace("s3://", "").split("/")[0]
        just_playlist_filename = playlist_file.replace("s3://", "").replace(bucket_name+"/", "")
        try:
            playlist_json = get_s3_file(bucket_name, just_playlist_filename)
        except Exception as e:
            raise Exception("%s not found in s3: %s" % (s3_processed_file, e))
    else:
        with open(playlist_file, 'r') as f:
            playlist_json = json.loads(f.read())
        just_playlist_filename = "playlists/"+playlist_file.split("/")[-1]
        bucket_name = OUTPUT_DATA_BUCKET_NAME

    new_public_playlists = lpf.load(category=event["category"])

    s3 = boto3.resource('s3')
    #print("Processing: %s with %s messages..."%(playlist_file, len(playlist_json)))
    c = 1
    z = 0
    # Convert to threading
    public_media_urls = []
    for message in playlist_json:
        new_public_file_name = hashlib.md5(message["s3_file_name"].encode('utf-8', errors="ignore")).hexdigest()+"."+message["s3_file_name"].split(".")[-1]
        public_media_url = CDN_PUBLIC_DOMAIN + "/" + new_public_file_name
        # if not file_exists
        if not new_public_file_name in files:
            copy_source = {
                'Bucket': bucket_name,
                'Key': message["s3_file_name"]
            }

            s3.meta.client.copy(copy_source, CDN_BUCKET_NAME, new_public_file_name)
            print("Copied to CDN bucket (%s): %s %s/%s" %(bucket_name, public_media_url, c, len(playlist_json)))
        else:
            z += 1
            #print("File %s/%s %s (%s) exists in %s" % (c, len(playlist_json), new_public_file_name, message["s3_file_name"], CDN_BUCKET_NAME))

        message["public_media_url"] = public_media_url
        if not public_media_url in public_media_urls:
            new_public_playlists.append(message)
            public_media_urls.append(public_media_url)
        c += 1
    #print("Didn't copy %s files in playlist because they were already in %s" % (z, CDN_BUCKET_NAME))
    #print("Processed %s messages in %s" % (len(playlist_json), s3_processed_file) )

    # Save local and S3 public playlist location
    public_playlist_locations = just_playlist_filename+"__public.json"
    public_playlist_locations = public_playlist_locations.split("/")
    if "test" in just_playlist_filename:
        public_playlist_locations[0] = "test-playlists"
    else:
        public_playlist_locations[0] = "playlists"
    public_playlist_location = "/".join(public_playlist_locations)
    local_public_playlist_location = "/tmp/"+public_playlist_location.split("/")[-1]
    with open(local_public_playlist_location,'w') as f:
        f.write(json.dumps(new_public_playlists))
    saved = save_file(bucket_name, local_public_playlist_location, public_playlist_location)
    if not saved:
        raise Exception("File %s not saved!" % public_playlist_location)
    # TODO implement
    return {
        'total_playlist_items': len(new_public_playlists),
        's3_file_name': "s3://"+bucket_name+"/"+public_playlist_location
    }






def save_file(bucket_name, file_name, s3_file_name):
    try:
        session = boto3.Session()
        s3_client = session.client("s3")
        # Upload the file to the S3 bucket
        s3_client.upload_file(file_name, bucket_name, s3_file_name)
        #print("Saved to S3 bucket %s the file: %s" % (bucket_name, file_name))
        return s3_file_name
    except Exception as e:
        print("Error in saving to S3 bucket %s the file %s: %s" % (bucket_name, file_name, e))
        return None



def file_exists_load(file_name):
    s3 = boto3.resource('s3')

    try:
        s3.Object(CDN_BUCKET_NAME, file_name).load()
        return True
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == "404":
            # The object does not exist.
            return False
        else:
            # Something else has gone wrong.
            raise


def file_exists(file_name):
    s3 = boto3.resource('s3')
    my_bucket = s3.Bucket(CDN_BUCKET_NAME)
    for object_summary in my_bucket.objects.filter():
        if file_name.lower() in object_summary.key.lower():
            return True
    return False


def get_s3_files():
    files = []
    s3 = boto3.resource('s3')
    my_bucket = s3.Bucket(CDN_BUCKET_NAME)
    for object_summary in my_bucket.objects.filter(Prefix=""):
        files.append(object_summary.key)
    return files


