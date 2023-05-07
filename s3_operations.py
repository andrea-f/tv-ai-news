import boto3

import json
import sys
import os
SAVE_DIR = os.getenv("SAVE_DIR", ".")


def get_s3_file(bucket_name, filename, save_dir=None, return_file_contents=True):
    if not save_dir:
        save_dir = SAVE_DIR
    if not bucket_name:
        raise Exception("No bucket name!")
    session = boto3.Session()
    s3_client = session.client("s3")
    filename_only = filename.split("/")[-1]
    s3_client.download_file(bucket_name, filename, "%s/%s" % (save_dir,filename_only))
    if return_file_contents:
        with open("%s/%s" % (save_dir,filename_only), "r") as f:
            if filename.endswith(".json"):
                file_contents = json.loads(f.read())
            elif filename.endswith(".csv"):
                file_contents = f.readlines()
            return file_contents
    else:
        return "%s/%s" % (save_dir,filename_only)


def list_files_in_bucket(bucket_name, subfolder="full_scans/", word_in_filename=None):
    s3 = boto3.resource('s3')
    my_bucket = s3.Bucket(bucket_name)
    files = []
    for object_summary in my_bucket.objects.filter(Prefix=subfolder):
        if word_in_filename:
            if word_in_filename.lower() in object_summary.key.lower():
                files.append(object_summary.key)
        else:
            files.append(object_summary.key)
    return files


def save_file(bucket_name, file_name, s3_file_name):
    try:
        session = boto3.Session()
        s3_client = session.client("s3")
        # Upload the file to the S3 bucket
        s3_client.upload_file(file_name, bucket_name, s3_file_name)
        #print("Loaded to S3 bucket %s the file: %s" % (bucket_name, file_name))
        return s3_file_name
    except Exception as e:
        print("Error in saving to S3 bucket %s the file %s: %s" % (bucket_name, file_name, e))
        return None