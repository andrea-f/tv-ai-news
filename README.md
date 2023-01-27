# Telegram TV

## Functionality
1. Logs in to Telegram via api id and hash
2. Fetches all groups that the logged in user is in
3. For a subset of groups, it saves messages and media
4. Messages and media are exported also to S3
5. Videos are then lined up chronologically and by an editor (and in the future via a filter) then list is saved to a json file
6. The list of videos/images set in the json file is encoded via ffmpeg to a HLS and RTSP stream
7. Stream is served online to YouTube via RTSP
8. Stream is republished as a HLS stream
9. Filter messages from a group based on a set of keywords and translate them if in Russian
10. Apply network topology to the messages to see where they are originated from and how they spread

## How to run

1. create virtualenv and install requirements.txt set the credentials json file in the current dir such as:
```json
{
  "api_id": "[TELEGRAM_API_ID]",
  "api_hash": "[TELEGRAM_API_HASH]",
  "username": "[TELEGRAM_USERNAME]",
  "phone": "[TELEGRAM_USERNAME_PHONE_NUMBER_WITH_AREA_CODE",
  "aws_s3_role_arn": "[AWS_ROLE_ARN_WITH_ACCESS_TO_S3_AND_REKOGNITION"
}
```
Make sure the folders `messages` and `media` are created in a level above of this README file.

2. Login to Telegram (will need input of received text code inside telegram channel in the app) and get groups by running: `python3 -m telegram_api -g` the result is saved to a `groups.json` file in the current folder
3. Login to Telegram and get messages from groups specified in a JSON file with the format:
```json
[
  {
    "name": "Troublemakers & Ultras Action",
    "id": 1131391619,
    "analyse_media": true,
    "max_past_messages": 100,
    "category": "ukr",
    "max_past_date": "1/1/2023",
    "messages_file": "/Users/andrea/Workspace/trueyou/telegram/messages/messages__Troublemakers & Ultras Action___1131391619.json",
    "participants_count": 10196,
    "group_image": ""
  },
  {
    "name": "Ukraine NOW",
    "id": 1280273449,
    "analyse_media": true,
    "max_past_messages": 200,
    "category": "ukr",
    "max_past_date": "1/1/2023",
    "messages_file": "/Users/andrea/Workspace/trueyou/telegram/messages/messages__Ukraine NOW___1280273449.json",
    "participants_count": 836239,
    "group_image": ""
  }
]
```
Run: `python3 -m telegram_api --messages location_of_groups_json_file.json`
This will start a long running task to fetch all the messages until `max_past_messages` is reached and saved in `location_of_groups_json_file.json__processed.json`
4. After the messages have been gathered and saved in S3 for all groups in `location_of_groups_json_file.json__processed.json`, 
generate the playlist by running: `python3 -m telegram_tv location_of_groups_json_file.json__processed.json`.
5. Once the above command is finished, it will generate and save to S3 a new JSON file: `location_of_groups_json_file.json__processed.json__playlists.json`
6. If a `__processed.json` file has already been created and needs to be converted to a playlist, run `python3 -m telegram_api -f` with the flag `fileWithAnalysedMessages` or `-f` so that the API fetching step is skipped and it goes directly to the playlist generation.
The request to the state machine should be of this format:
```json
{
  "load_messages_from_file": true,
  "selected_groups_file": "s3://telegram-output-data/groups_to_analyse_inputs/26-01-2023_01:13:10__groups_to_analyse__-__18.json__processed.json"
}
```