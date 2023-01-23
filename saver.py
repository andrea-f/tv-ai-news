import json
import datetime

def date_format(message):
    """
    :param message:
    :return:
    """
    if type(message) is datetime:
        return message.strftime("%Y-%m-%d %H:%M:%S")

def save_media(data, file_name, save_local_file=True):
    """
    Saves Media to localhost or S3
    :return:
    """
    if save_local_file:
        saved_file_name= save_local(data, file_name)
    return saved_file_name


def save_local(data, file_name):
    with open(file_name, 'w') as f:
        f.write(json.dumps(data, indent=4,default=date_format))
        return file_name