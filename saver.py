import json
import datetime
import os
import s3_operations
OUTPUT_DATA_BUCKET_NAME = os.getenv("OUTPUT_DATA_BUCKET_NAME", "telegram-output-data")
SAVE_DIR = os.getenv("SAVE_DIR", "../messages")

def date_format(message):
    """
    :param message:
    :return:
    """
    if type(message) is datetime:
        return message.strftime("%Y-%m-%d %H:%M:%S")


def save_media(data={}, file_name="", save_local_file=True, return_both=False, append=False):
    """
    Saves Media to localhost or S3
    :return:
    """
    if "s3" in file_name:
        file_name = file_name.replace("s3://"+OUTPUT_DATA_BUCKET_NAME+"/", SAVE_DIR+"/")
    s3_file_name = file_name.replace("../", "").replace(SAVE_DIR+"/","")
    if append and type(data) == dict:
        try:
            already_existing_messages = s3_operations.get_s3_file(OUTPUT_DATA_BUCKET_NAME, s3_file_name)
            already_existing_messages.append(data)
            data = already_existing_messages
        except Exception as e:
            print("Could not append to %s because: %s" % (s3_file_name, e))
            data = [data]
    if save_local_file:
        file_name = save_local(data, file_name)
    s3_file_path = s3_operations.save_file(OUTPUT_DATA_BUCKET_NAME, file_name, s3_file_name)
    print(OUTPUT_DATA_BUCKET_NAME, s3_file_path, s3_file_name, file_name)
    if save_local_file:
        print("Saved: %s and %s" % (file_name, "s3://"+OUTPUT_DATA_BUCKET_NAME+"/"+s3_file_path))
        if not return_both:
            return file_name
        else:
            return file_name, s3_file_path
    else:

        print("Saved %s" % ("s3://"+OUTPUT_DATA_BUCKET_NAME+"/"+s3_file_path))
        return s3_file_path





def save_local(data, file_name):
    if "/" in file_name:
        folder = "/".join(file_name.split("/")[:-1])
        if not os.path.isdir(folder):
            os.makedirs(folder)
    else:
        file_name = "/tmp/"+file_name
    with open(file_name, 'w') as f:
        if file_name.endswith(".json"):
            f.write(json.dumps(data, indent=4,default=date_format))
        else:
            f.write(data)
        return file_name