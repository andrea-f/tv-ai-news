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

7. Run server to show TV interface: `python3 -m server 80`, then go to: http://127.0.0.1
Documents and files for the interface are in `interface-api/server.py`
There is a DNS record pointing to the flask server ECS service and can be accessed at: https://tv.cyber-monitor.com
The server is run as an ECS task for a flask API: https://eu-west-1.console.aws.amazon.com/ecs/v2/clusters/telegram-interface/services/flask-api-3/health?region=eu-west-1
The ECS task service definition is available here: https://eu-west-1.console.aws.amazon.com/ecs/v2/task-definitions/telegram-interface?status=ACTIVE?region=eu-west-1
The container running in the service is from this image: 967979648201.dkr.ecr.eu-west-1.amazonaws.com/tv-interface:latest

To deploy a new version of the server code:
```
Retrieve an authentication token and authenticate your Docker client to your registry.
Use the AWS CLI:

aws ecr get-login-password --region eu-west-1 | docker login --username AWS --password-stdin 967979648201.dkr.ecr.eu-west-1.amazonaws.com
Note: if you receive an error using the AWS CLI, make sure that you have the latest version of the AWS CLI and Docker installed.
Build your Docker image using the following command. For information on building a Docker file from scratch, see the instructions here . You can skip this step if your image has already been built:

docker build -t tv-interface .
After the build is completed, tag your image so you can push the image to this repository:

docker tag tv-interface:latest 967979648201.dkr.ecr.eu-west-1.amazonaws.com/tv-interface:latest
Run the following command to push this image to your newly created AWS repository:

docker push 967979648201.dkr.ecr.eu-west-1.amazonaws.com/tv-interface:latest
```

## Tests

Run test to save groups to graphql: `python3 -m pytest tests.py -k test_save_group`

## Structure

The code structure of the algorithm follows this flow: 
1. edit the file `telegram_api.py` is the entry point of the ETL application and takes arguments.
2. once the messages have been downloaded and analysed (including media) for all the groups in the input, in the file `telegram_tv.py` `generate_playlist` method is called to generate a playlist
3. after the playlist has been generated and saved to S3, the public playlist is created by calling `telegram_tv_public_playlist`  `lambda_handler` method to create the public playlist which copies the files to a CDN and saves the playlist file to S3



### Lambda functions used
1. lambda function for ECS task: https://eu-west-1.console.aws.amazon.com/lambda/home?region=eu-west-1#/functions/telegram-tv-api-configure-ecs-task-input for ingestion
2. lambda function for copying generated files and json playlist file from private bucket to public one used by Cloudfront CDN: https://eu-west-1.console.aws.amazon.com/lambda/home?region=eu-west-1#/functions/telegram-tv-api-public-playlist
3. to avoid re processing messages this lambda function is used to copy messages into a unique signatures file: https://eu-west-1.console.aws.amazon.com/lambda/home?region=eu-west-1#/functions/unique-saved-messages?tab=code

Input with groups to analyse for lambda function in 1.:
```

{
  "selected_groups_file": "s3://telegram-output-data/groups_to_analyse__test.json"
}
```
When the lambda function in 1. is executed the resutling output is:
```
{
        'commands_telegram_api': commands_get_messages,
        'commands_telegram_tv': commands_run_playlist_generation
    }

```

The ECS task definition for the ingestion part is here: https://eu-west-1.console.aws.amazon.com/ecs/v2/task-definitions/telegram-api-tv/12/containers?region=eu-west-1
The containers in the ECS task running the ingestion and ML operations on the data is: https://eu-west-1.console.aws.amazon.com/ecs/v2/task-definitions/telegram-api-tv/12/containers?region=eu-west-1
The image running in the task can be updated by:
```Retrieve an authentication token and authenticate your Docker client to your registry.
   Use the AWS CLI:
   
   aws ecr get-login-password --region eu-west-1 | docker login --username AWS --password-stdin 967979648201.dkr.ecr.eu-west-1.amazonaws.com
   Note: if you receive an error using the AWS CLI, make sure that you have the latest version of the AWS CLI and Docker installed.
   Build your Docker image using the following command. For information on building a Docker file from scratch, see the instructions here . You can skip this step if your image has already been built:
   
   docker build -t telegram-api-tv .
   After the build is completed, tag your image so you can push the image to this repository:
   
   docker tag telegram-api-tv:latest 967979648201.dkr.ecr.eu-west-1.amazonaws.com/telegram-api-tv:latest
   Run the following command to push this image to your newly created AWS repository:
   
   docker push 967979648201.dkr.ecr.eu-west-1.amazonaws.com/telegram-api-tv:latest
```