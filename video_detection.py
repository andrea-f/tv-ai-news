#Copyright 2018 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#PDX-License-Identifier: MIT-0 (For details, see https://github.com/awsdocs/amazon-rekognition-developer-guide/blob/master/LICENSE-SAMPLECODE.)

import boto3
import json
import sys
import time
import os



class VideoDetect:
    jobId = ''
    rek = boto3.client('rekognition')
    sqs = boto3.client('sqs')
    sns = boto3.client('sns')

    roleArn = ''
    bucket = ''
    video = ''
    startJobId = ''

    sqsQueueUrl = ''
    snsTopicArn = ''
    processType = ''

    def __init__(self, role, bucket, video):
        self.roleArn = role
        self.bucket = bucket
        self.video = video

    def GetSQSMessageSuccess(self):

        jobFound = False
        succeeded = False

        dotLine=0
        while jobFound == False:
            sqsResponse = self.sqs.receive_message(QueueUrl=self.sqsQueueUrl, MessageAttributeNames=['ALL'],
                                                   MaxNumberOfMessages=10)

            if sqsResponse:
                print(json.dumps(sqsResponse, indent=4))
                if 'Messages' not in sqsResponse:
                    if dotLine<40:
                        print('.', end='')
                        dotLine=dotLine+1
                    else:
                        print()
                        dotLine=0
                    sys.stdout.flush()
                    time.sleep(5)
                    continue

                for message in sqsResponse['Messages']:
                    notification = json.loads(message['Body'])
                    rekMessage = json.loads(notification['Message'])
                    print(rekMessage['JobId'])
                    print(rekMessage['Status'])
                    if rekMessage['JobId'] == self.startJobId:
                        print('Matching Job Found:' + rekMessage['JobId'])
                        jobFound = True
                        if (rekMessage['Status']=='SUCCEEDED'):
                            succeeded=True

                        self.sqs.delete_message(QueueUrl=self.sqsQueueUrl,
                                                ReceiptHandle=message['ReceiptHandle'])
                    else:
                        print("Job didn't match:" +
                              str(rekMessage['JobId']) + ' : ' + self.startJobId)
                    # Delete the unknown message. Consider sending to dead letter queue
                    self.sqs.delete_message(QueueUrl=self.sqsQueueUrl,
                                            ReceiptHandle=message['ReceiptHandle'])


        return succeeded

    def main(self):
        jobFound = False
        sqs = boto3.client('sqs')
        self.CreateTopicandQueue()

        results = {}

        # Change active start function for the desired analysis. Also change the GetResults function later in this code.
        #=====================================
        response = self.rek.start_label_detection(Video={'S3Object': {'Bucket': self.bucket, 'Name': self.video}},
                                                  NotificationChannel={'RoleArn': self.roleArn, 'SNSTopicArn': self.snsTopicArn})
        #print('Start Job Id: ' + response['JobId'])
        r = self.GetResultsLabels(response['JobId'])
        results["labels"] = r
        #print("l",r)
        #response = self.rek.start_face_detection(Video={'S3Object':{'Bucket':self.bucket,'Name':self.video}},
        #    NotificationChannel={'RoleArn':self.roleArn, 'SNSTopicArn':self.topicArn})

        #response = self.rek.start_face_search(Video={'S3Object':{'Bucket':self.bucket,'Name':self.video}},
        #    CollectionId='CollectionId',
        #    NotificationChannel={'RoleArn':self.roleArn, 'SNSTopicArn':self.topicArn})

        #response = self.rek.start_person_tracking(Video={'S3Object':{'Bucket':self.bucket,'Name':self.video}},
        #   NotificationChannel={'RoleArn':self.roleArn, 'SNSTopicArn':self.topicArn})

        response = self.rek.start_celebrity_recognition(Video={'S3Object':{'Bucket':self.bucket,'Name':self.video}},
            NotificationChannel={'RoleArn':self.roleArn, 'SNSTopicArn':self.snsTopicArn})

        #response = self.rek.start_content_moderation(Video={'S3Object':{'Bucket':self.bucket,'Name':self.video}},
        #    NotificationChannel={'RoleArn':self.roleArn, 'SNSTopicArn':self.topicArn})

        #print('Start Job Id: ' + response['JobId'])
        #self.GetResultsFaces(rekMessage['JobId'])
        #self.GetResultsFaceSearchCollection(rekMessage['JobId'])
        #self.GetResultsPersons(rekMessage['JobId'])
        r = self.GetResultsCelebrities(response['JobId'])
        #print("c",r)
        results["celebs"] = r
        self.DeleteTopicandQueue()

        return results





    # Gets the results of labels detection by calling GetLabelDetection. Label
    # detection is started by a call to StartLabelDetection.
    # jobId is the identifier returned from StartLabelDetection
    def GetResultsLabels(self, jobId):
        maxResults = 10
        paginationToken = ''
        finished = False
        label_results = {"labels":[]}
        printed = False
        while finished == False:
            response = self.rek.get_label_detection(
                JobId=jobId,
                MaxResults=maxResults,
                NextToken=paginationToken,
                SortBy='TIMESTAMP'
            )

            if response['JobStatus']=="IN_PROGRESS":
                if not printed:
                    #print(response['JobStatus'], "labels")
                    printed = True
                continue

            try:
                label_results["video_info"] = {
                    "codec": response['VideoMetadata']['Codec'],
                    "duration_ms": response['VideoMetadata']['DurationMillis'],
                    "format": response['VideoMetadata']['Format'],
                    "frame_rate": response['VideoMetadata']['FrameRate']
                }
                # print(response['VideoMetadata']['Codec'])
                # print(str(response['VideoMetadata']['DurationMillis']))
                # print(response['VideoMetadata']['Format'])
                # print(response['VideoMetadata']['FrameRate'])
            except:
                pass

            for labelDetection in response['Labels']:
                label_results['labels'].append({
                    "name": labelDetection['Label']['Name'],
                    "confidence": labelDetection['Label']['Confidence'],
                    "timestamp": str(labelDetection['Timestamp'])
                })
                # print("Label name:",labelDetection['Label']['Name'])
                # print("Label confidence:",labelDetection['Label']['Confidence'])
                # print("Timestamp:",str(labelDetection['Timestamp']))

            if 'NextToken' in response:
                paginationToken = response['NextToken']
            else:
                #print("FINISHED LABELS, found: %s" % len(label_results["labels"]))
                finished = True
        return label_results

    # Gets person tracking information using the GetPersonTracking operation.
    # You start person tracking by calling StartPersonTracking
    # jobId is the identifier returned from StartPersonTracking
    def GetResultsPersons(self, jobId):
        maxResults = 10
        paginationToken = ''
        finished = False

        while finished == False:
            response = self.rek.get_person_tracking(JobId=jobId,
                                                    MaxResults=maxResults,
                                                    NextToken=paginationToken)

            print(response['VideoMetadata']['Codec'])
            print(str(response['VideoMetadata']['DurationMillis']))
            print(response['VideoMetadata']['Format'])
            print(response['VideoMetadata']['FrameRate'])

            for personDetection in response['Persons']:
                print('Index: ' + str(personDetection['Person']['Index']))
                print('Timestamp: ' + str(personDetection['Timestamp']))
                print()

            if 'NextToken' in response:
                paginationToken = response['NextToken']
            else:
                finished = True
    # Gets the results of unsafe content label detection by calling
    # GetContentModeration. Analysis is started by a call to StartContentModeration.
    # jobId is the identifier returned from StartContentModeration
    def GetResultsModerationLabels(self, jobId):
        maxResults = 10
        paginationToken = ''
        finished = False

        while finished == False:
            response = self.rek.get_content_moderation(JobId=jobId,
                                                       MaxResults=maxResults,
                                                       NextToken=paginationToken)

            print(response['VideoMetadata']['Codec'])
            print(str(response['VideoMetadata']['DurationMillis']))
            print(response['VideoMetadata']['Format'])
            print(response['VideoMetadata']['FrameRate'])

            for contentModerationDetection in response['ModerationLabels']:
                print('Label: ' +
                      str(contentModerationDetection['ModerationLabel']['Name']))
                print('Confidence: ' +
                      str(contentModerationDetection['ModerationLabel']['Confidence']))
                print('Parent category: ' +
                      str(contentModerationDetection['ModerationLabel']['ParentName']))
                print('Timestamp: ' + str(contentModerationDetection['Timestamp']))
                print()

            if 'NextToken' in response:
                paginationToken = response['NextToken']
            else:
                finished = True

    # Gets the results of face detection by calling GetFaceDetection. Face
    # detection is started by calling StartFaceDetection.
    # jobId is the identifier returned from StartFaceDetection
    def GetResultsFaces(self, jobId):
        maxResults = 10
        paginationToken = ''
        finished = False

        while finished == False:
            response = self.rek.get_face_detection(JobId=jobId,
                                                   MaxResults=maxResults,
                                                   NextToken=paginationToken)

            print(response['VideoMetadata']['Codec'])
            print(str(response['VideoMetadata']['DurationMillis']))
            print(response['VideoMetadata']['Format'])
            print(response['VideoMetadata']['FrameRate'])

            for faceDetection in response['Faces']:
                print('Face: ' + str(faceDetection['Face']))
                print('Confidence: ' + str(faceDetection['Face']['Confidence']))
                print('Timestamp: ' + str(faceDetection['Timestamp']))
                print()

            if 'NextToken' in response:
                paginationToken = response['NextToken']
            else:
                finished = True

    # Gets the results of a collection face search by calling GetFaceSearch.
    # The search is started by calling StartFaceSearch.
    # jobId is the identifier returned from StartFaceSearch
    def GetResultsFaceSearchCollection(self, jobId):
        maxResults = 10
        paginationToken = ''

        finished = False

        while finished == False:
            response = self.rek.get_face_search(JobId=jobId,
                                                MaxResults=maxResults,
                                                NextToken=paginationToken)

            print(response['VideoMetadata']['Codec'])
            print(str(response['VideoMetadata']['DurationMillis']))
            print(response['VideoMetadata']['Format'])
            print(response['VideoMetadata']['FrameRate'])

            for personMatch in response['Persons']:
                print('Person Index: ' + str(personMatch['Person']['Index']))
                print('Timestamp: ' + str(personMatch['Timestamp']))

                if ('FaceMatches' in personMatch):
                    for faceMatch in personMatch['FaceMatches']:
                        print('Face ID: ' + faceMatch['Face']['FaceId'])
                        print('Similarity: ' + str(faceMatch['Similarity']))
                print()
            if 'NextToken' in response:
                paginationToken = response['NextToken']
            else:
                finished = True
            print()

    # Gets the results of a celebrity detection analysis by calling GetCelebrityRecognition.
    # Celebrity detection is started by calling StartCelebrityRecognition.
    # jobId is the identifier returned from StartCelebrityRecognition
    def GetResultsCelebrities(self, jobId):
        maxResults = 10
        paginationToken = ''
        finished = False
        celebrities_results = {"celebs":[]}
        printed = False
        while finished == False:
            response = self.rek.get_celebrity_recognition(
                JobId=jobId,
                MaxResults=maxResults,
                NextToken=paginationToken
            )

            if response['JobStatus']=="IN_PROGRESS":
                if not printed:
                    #print(response['JobStatus'], "celebs")
                    printed = True
                continue
            try:
                # print(response['VideoMetadata']['Codec'])
                # print(str(response['VideoMetadata']['DurationMillis']))
                # print(response['VideoMetadata']['Format'])
                # print(response['VideoMetadata']['FrameRate'])
                celebrities_results["video_info"] = {
                    "codec": response['VideoMetadata']['Codec'],
                    "duration_ms": response['VideoMetadata']['DurationMillis'],
                    "format": response['VideoMetadata']['Format'],
                    "frame_rate": response['VideoMetadata']['FrameRate']
                }
            except:
                pass

            for celebrityRecognition in response['Celebrities']:
                celebrities_results["celebs"].append({
                    "name": str(celebrityRecognition['Celebrity']['Name']),
                    "timestamp": str(celebrityRecognition['Timestamp'])
                })
                # print('Celebrity: ' +
                #       str(celebrityRecognition['Celebrity']['Name']))
                # print('Timestamp: ' + str(celebrityRecognition['Timestamp']))
                # print()

            if 'NextToken' in response:
                paginationToken = response['NextToken']
            else:
                #print("FINISHED LABELS, found: %s" % len(celebrities_results["celebs"]))
                finished = True
        return celebrities_results



    def CreateTopicandQueue(self):

        millis = str(int(round(time.time() * 1000)))

        #Create SNS topic

        snsTopicName="AmazonRekognitionExample" + millis

        topicResponse=self.sns.create_topic(Name=snsTopicName)
        self.snsTopicArn = topicResponse['TopicArn']

        #create SQS queue
        sqsQueueName="AmazonRekognitionQueue" + millis
        self.sqs.create_queue(QueueName=sqsQueueName,
                              Attributes={"SqsManagedSseEnabled":"false"})
        self.sqsQueueUrl = self.sqs.get_queue_url(QueueName=sqsQueueName)['QueueUrl']

        attribs = self.sqs.get_queue_attributes(QueueUrl=self.sqsQueueUrl,
                                                AttributeNames=['QueueArn'])['Attributes']

        sqsQueueArn = attribs['QueueArn']

        # Subscribe SQS queue to SNS topic
        self.sns.subscribe(
            TopicArn=self.snsTopicArn,
            Protocol='sqs',
            Endpoint=sqsQueueArn)

        #Authorize SNS to write SQS queue
        policy = """{{
  "Version":"2012-10-17",
  "Statement": [
    {{
      "Sid": "Stmt1596186812579",
      "Effect": "Allow",
      "Principal": {{
        "Service": "sns.amazonaws.com"
      }},
      "Action": [
        "sqs:SendMessage",
        "sqs:SendMessageBatch"
      ],
      "Resource": "{}",
      "Condition":{{
      "ArnEquals":{{
        "aws:SourceArn": "{}"
      }}
    }}
    }}
  ]
  
}}""".format(sqsQueueArn, self.snsTopicArn)

        response = self.sqs.set_queue_attributes(
            QueueUrl = self.sqsQueueUrl,
            Attributes = {
                'Policy' : policy
            }
        )
        #print(response)
        #print("Created queue: %s" % sqsQueueName)

    def DeleteTopicandQueue(self):
        self.sqs.delete_queue(QueueUrl=self.sqsQueueUrl)
        self.sns.delete_topic(TopicArn=self.snsTopicArn)





def start():
    roleArn = 'arn:aws:iam::967979648201:role/telegram-role'
    bucket = 'telegram-output-data'
    video = 'Ukraine NOW___1280273449/IMG_8376 (2).MP4'
    #video = "Hooligans.cz___1249907791/.mp4"

    analyzer=VideoDetect(roleArn, bucket,video)
    #analyzer.CreateTopicandQueue()

    analyzer.main()

    #analyzer.DeleteTopicandQueue()


if __name__ == "__main__":
    start()
