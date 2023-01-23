import os, sys, json
import boto3
import video_detection



def translate_text(message, language_source='ru', language_target='en'):
    # Create a boto3 client for the Translate service
    translate = boto3.client('translate')
    # Translate the text from Russian to English
    result = translate.translate_text(
        Text=message, SourceLanguageCode=language_source, TargetLanguageCode=language_target
    )

    # Print the translated text
    #print(message, result['TranslatedText'])
    translated_message = result['TranslatedText']
    return translated_message

def get_keywords_old(download_path):
    # Create a boto3 client for the Rekognition service
    rekognition = boto3.client('rekognition')

    # Load the video from a local file
    print("Processing %s, extracting keywords..." % download_path)
    video = open(download_path, "rb").read()

    # OR, load the video from an S3 bucket
    # s3 = boto3.client('s3')
    # video = s3.get_object(Bucket='my-bucket', Key='path/to/video.mp4')['Body'].read()

    # Extract keywords from the video
    response = rekognition.detect_labels(Video={'Bytes': video})

    # Print the keywords
    keywords = []
    for label in response['Labels']:
        print(label['Name'])
        keywords.append(label['Name'])
    print("Extracted %s keywords from %s" % (len(keywords), download_path))
    return keywords


def get_keywords(bucket, s3_file_path, role):
    video = video_detection.VideoDetect(role, bucket, s3_file_path)
    detected_keywords = video.main()
    return detected_keywords

def get_keywords_image(image_name):
    print("Getting keywords for: %s" % image_name)
    # Create a Rekognition client
    rekognition = boto3.client('rekognition')

    # Set the name of the image and the image type
    image_type = 'jpg'

    # Open the image file
    with open(image_name, 'rb') as image:
        # Read the image file into memory
        image_bytes = image.read()

    # Run AWS Rekognition on the image
    response = rekognition.detect_labels(Image={'Bytes': image_bytes}, MinConfidence=90)

    # Print the labels that were detected
    # print(response['Labels'])
    keywords = response['Labels']
    print("Found %s keywords for %s" % (len(keywords), image_name))
    return keywords

