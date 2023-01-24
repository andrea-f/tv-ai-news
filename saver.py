import json
import datetime
import os
import s3_operations
OUTPUT_DATA_BUCKET_NAME = os.getenv("OUTPUT_DATA_BUCKET_NAME", "telegram-output-data")
SAVE_DIR = os.getenv("SAVE_DIR", "../output_data/downloaded_site_data")

def date_format(message):
    """
    :param message:
    :return:
    """
    if type(message) is datetime:
        return message.strftime("%Y-%m-%d %H:%M:%S")


def save_media(data={}, file_name="", save_local_file=True):
    """
    Saves Media to localhost or S3
    :return:
    """
    if "s3" in file_name:
        file_name = file_name.replace("s3://"+OUTPUT_DATA_BUCKET_NAME+"/", SAVE_DIR+"/")
    if save_local_file:
        save_local(data, file_name)
    s3_file_name = file_name.replace("../", "").replace(SAVE_DIR+"/","")

    s3_file_path = s3_operations.save_file(OUTPUT_DATA_BUCKET_NAME, file_name, s3_file_name)

    if save_local_file:
        print("Saved: %s and %s" % (file_name, s3_file_path))
        return file_name
    else:
        print("Saved %s" % (s3_file_path))
        return s3_file_path


def save_local(data, file_name):
    with open(file_name, 'w') as f:
        f.write(json.dumps(data, indent=4,default=date_format))
        return file_name