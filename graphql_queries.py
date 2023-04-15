GROUP_CREATE_QUERY = """
mutation createGroupMutation {
  createGroup(input: {input_data}
  ) {
    id
    name
    participants
    username
    s3_profile_image
  }
}
"""

GROUP_CREATE_INPUT = {
    "id": "",
    "original_name_language": "",
    "participants": 10,
    "platform_id": "",
    "platform_name": "",
    "s3_profile_image": "",
    "username": "",
    "title": "",
    "name": "",
    "created_at": ""
}

KEYWORD_CREATE_QUERY = """
mutation createKeywordMutation {
  createKeyword(input: {input}
  ) {
    id
    type_of_label
    text
  }
}
"""

KEYWORD_CREATE_INPUT = {
    "category": "",
    "created_at": "",
    "type_of_label": "",
    "id": "",
    "text": "",
    "original_text": "",
    "confidence": 0,
    "language": "",
    "parent": "",
    "updated_at": ""
}

MESSAGE_CREATE_QUERY = """
mutation createMessageMutation {
  createMessage(input: {input}
  ) {
    id
    public_media_url
    reactions_count
    sentiment
    text
    views
    category
    forwards
    replies_count
  }
}
"""

MESSAGE_CREATE_INPUT = {
    "category": "",
    "group_id": "",
    "id": "",
    "forwards": 0,
    "created_at": "",
    "message_date": "",
    "platform": "",
    "media_type": "",
    "platform_group_id": 0,
    "platform_group_name": "",
    "platform_group_participants": "",
    "platform_id": "",
    "platform_name": "",
    "public_media_url": "",
    "reactions_count": 0,
    "reactions": "",
    "replies": "",
    "replies_count": 0,
    "s3_media_file_name": "",
    "sentiment": "",
    "signature": "",
    "sentiments": "",
    "text": "",
    "views": 0,
    "grouped_id": 0
}