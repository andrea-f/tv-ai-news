import json
import datetime
import os
import s3_operations
# import graphql_manager
# import graphql_queries
import traceback
OUTPUT_DATA_BUCKET_NAME = os.getenv("OUTPUT_DATA_BUCKET_NAME", "telegram-output-data")
SAVE_DIR = os.getenv("SAVE_DIR", "../messages")

# graphql = graphql_manager.GraphQLManager()

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
    if save_local_file:
        #print("Saved: %s and %s" % (file_name, "s3://"+OUTPUT_DATA_BUCKET_NAME+"/"+s3_file_path))
        if not return_both:
            return file_name
        else:
            return file_name, s3_file_path
    else:
        #print("Saved %s" % ("s3://"+OUTPUT_DATA_BUCKET_NAME+"/"+s3_file_path))
        return s3_file_path


def save_media_new(data=None, file_name="", save_local_file=True, data_type=None, save_graphql=False):
    """
    Saves Media to localhost or S3
    :return:
    """
    if file_name and len(file_name) > 0:
        if "s3" in file_name:
            file_name = file_name.replace("s3://"+OUTPUT_DATA_BUCKET_NAME+"/", SAVE_DIR+"/")
        s3_file_name = file_name.replace("../", "").replace(SAVE_DIR+"/","")
        if save_local_file and data:
            file_name = save_local(data, file_name)
        s3_file_path = s3_operations.save_file(OUTPUT_DATA_BUCKET_NAME, file_name, s3_file_name)
        return file_name, s3_file_path
    #if data_type and data and save_graphql:
    #    try:
    #        if data_type == "group":
    #            saved_group = save_group(data)
    #            return saved_group
    #
    #        elif data_type == "message":
    #            saved_message = save_message(data)
    #            return saved_message
    #    except Exception as e:
    #        print("Error in saving %s: %s" % (data_type, e))
    #        traceback.print_exc()




def save_group(group:dict):

    current_time = datetime.datetime.utcnow()
    aws_timestamp = current_time.isoformat() + "Z"

    group_input = {
        "id": group["entity"]["id"],
        "original_name_language": group["original_name_language"],
        "participants": group["entity"]["participants_count"],
        "platform_id": group["entity"]["id"],
        "platform_name": "telegram",
        "s3_profile_image": OUTPUT_DATA_BUCKET_NAME+"/"+group["profile_photo"],
        "username": group["entity"]["username"],
        "title": group["entity"]["title"],
        "name": group["name"],
        "created_at": aws_timestamp
    }
    if "original_name" in group:
        group_input["original_name"] = group["original_name"]
    # query = graphql_queries.GROUP_CREATE_QUERY.format(
    #     input_data=json.dumps(group_input, indent=4)
    # )
    query = graphql_queries.GROUP_CREATE_QUERY.replace(
        '{input_data}',json.dumps(group_input, indent=4)
    )
    saved_group = graphql.send_graphql_query(query)
    return saved_group

def save_message(message:dict):
    current_time = datetime.datetime.utcnow()
    aws_timestamp = current_time.isoformat() + "Z"
    media_type = None
    if ("s3_file_name" in message and message["s3_file_name"]
        and len(message["s3_file_name"]) > 0):
        if message["s3_file_name"].endswith("jpg"):
            media_type = "image"
        elif (
            message["s3_file_name"].lower().endswith(".mov") or
            message["s3_file_name"].lower().endswith(".mp4")
        ):
            media_type = "video"
        else:
            media_type = "doc"

    message_input = {
        "category": message["category"],
        "id": message["signature"],
        "forwards": message["forwards"],
        "created_at": aws_timestamp,
        "message_date": message["date"],
        "platform": "telegram",
        "media_type": media_type,
        "platform_group_id": message["group_id"],
        "platform_group_name": message["group_name"],
        "platform_group_participants": message["group_participants"],
        "platform_id": message["id"],
        "public_media_url": message["public_media_url"],
        "reactions_count": message["reactions_count"],
        "reactions": json.dumps(message["reactions"], indent=4),
        "replies": json.dumps(message["replies"], indent=4),
        "replies_count": message["replies_count"],
        "s3_media_file_name": message["s3_file_name"],
        "sentiment": message["sentiment"] if "sentiment" in message else "Not detected",
        "signature": message["signature"],
        "text": message["message"],
        "views": message["views"],
        "grouped_id": message["grouped_id"]
    }
    query = graphql_queries.MESSAGE_CREATE_QUERY.format(
        input=json.dumps(message_input, indent=4)
    )
    saved_message = graphql.send_graphql_query(query)
    # Missing saving keywords
    return saved_message


def save_keyword(data:dict):
    keyword_input = {
        "category": data["category"],
        "created_at": data["created_at"],
        "type_of_label": data["type_of_label"],
        "id": "",
        "text": data["text"],
        "original_text": data["original_text"],
        "confidence": 0,
        "language": data["language"],
        "parent": data["parent"],
        "label_category": data["label_category"]
    }
    query = graphql_queries.KEYWORD_CREATE_QUERY.format(
        input=json.dumps(keyword_input, indent=4)
    )
    saved_keyword = graphql.send_graphql_query(query)
    return saved_keyword

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