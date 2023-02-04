import os, sys, json
import boto3
import video_detection
import subprocess
import s3_operations
#UNIQUE_SIGNATURES_FILE_NAME = os.getenv("UNIQUE_SIGNATURES_FILE_NAME", "unique_signatures.csv")
OUTPUT_DATA_BUCKET_NAME = os.getenv("OUTPUT_DATA_BUCKET_NAME", "telegram-output-data")

def detect_text_language(text):
    if text and len(text)>0:
        comprehend = boto3.client('comprehend')
        response = comprehend.detect_dominant_language(
            Text=text
        )
        if len(response['Languages']) > 0:
            if "cv" == response['Languages'][0]['LanguageCode']:
                response['Languages'][0]['LanguageCode'] = "ru"
            return response['Languages'][0]['LanguageCode']
    return None


def detect_entities(text, language="en"):
    comprehend = boto3.client('comprehend')
    entities = comprehend.detect_entities(Text=text, LanguageCode=language)
    return entities["Entities"]

def detect_sentiment(text, language="en"):
    comprehend = boto3.client('comprehend')
    sentiment = comprehend.detect_sentiment(Text=text, LanguageCode=language)
    return {
        "sentiment": sentiment["Sentiment"],
        "sentiments_score": sentiment["SentimentScore"]
    }


def translate_text(message, language_source='ru', language_target='en', current_try=0, max_tries=1):
    # Create a boto3 client for the Translate service
    translate = boto3.client('translate')
    # Translate the text from Russian to English
    try:
        result = translate.translate_text(
            Text=message, SourceLanguageCode=language_source, TargetLanguageCode=language_target
        )
    except Exception as e:
        print("Error in translating %s (%s) to %s" % (message[:30], language_source, language_target))
        if current_try<max_tries:
            return translate_text(message, 'auto', current_try=current_try+1)
        else:
            return None
    # Print the translated text
    #print(message, result['TranslatedText'])
    translated_message = result['TranslatedText']
    return translated_message



def get_keywords(bucket, s3_file_path, role):
    video = video_detection.VideoDetect(role, bucket, s3_file_path)
    detected_keywords = video.main()
    return detected_keywords


def get_keywords_image(image_name):
    #print("Getting labels, celebs, text in image for: %s" % image_name)
    # Create a Rekognition client
    rekognition = boto3.client('rekognition')

    # Set the name of the image and the image type
    image_type = 'jpg'

    # Open the image file
    with open(image_name, 'rb') as image:
        # Read the image file into memory
        image_bytes = image.read()

    # Run AWS Rekognition on the image
    response_labels = rekognition.detect_labels(Image={'Bytes': image_bytes}, MinConfidence=90)
    response_celebs = rekognition.recognize_celebrities(Image={'Bytes': image_bytes})
    response_text = rekognition.detect_text(Image={'Bytes': image_bytes})


    # Print the labels that were detected
    # print(response['Labels'])
    keywords = {
        "labels": response_labels["Labels"],
        "celebs": response_celebs["CelebrityFaces"]
    }
    translated = False
    try:
        full_text = ""
        for t in response_text["TextDetections"]:
            full_text += "%s " % t['DetectedText']
        if len(full_text.strip())>0:
            language = detect_text_language(full_text)
            if not "en" == language:
                translated_message = translate_text(full_text, language_source=language)
                keywords["text"] = [{"word": p} for p in translated_message.split(" ") if len(p.strip(" "))>0]
                translated = True
    except Exception as e:
        print("Error in tranlsating text extracted from %s image: %s" % (image_name, e))
    if translated:
        orig_text = "original_text"
    else:
        orig_text = "text"

    keywords[orig_text] = [{"word":t['DetectedText'], "confidence": t["Confidence"]} for t in response_text["TextDetections"] if len(t)>0]
    #print("Found %s keywords for %s" % (len(keywords), image_name))
    return keywords


