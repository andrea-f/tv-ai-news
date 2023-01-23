import json
import datetime
import os
import s3_operations
OUTPUT_DATA_BUCKET_NAME = os.getenv("OUTPUT_DATA_BUCKET_NAME", "telegram-output-data")


def date_format(message):
    """
    :param message:
    :return:
    """
    if type(message) is datetime:
        return message.strftime("%Y-%m-%d %H:%M:%S")

def save_media(data, file_name):
    """
    Saves Media to localhost or S3
    :return:
    """
    saved_file_name= save_local(data, file_name)
    s3_file_name = file_name.replace("../", "")
    s3_file_path = s3_operations.save_file(OUTPUT_DATA_BUCKET_NAME, file_name, s3_file_name)
    print("Saved: %s and %s" % (saved_file_name, s3_file_path))
    return saved_file_name


def save_local(data, file_name):
    with open(file_name, 'w') as f:
        f.write(json.dumps(data, indent=4,default=date_format))
        return file_name