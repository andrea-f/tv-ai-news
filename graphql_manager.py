import requests
import json
import time
import os
import boto3
import base64
from botocore.exceptions import ClientError
from requests_aws_sign import AWSV4Sign
import graphql_queries
#from aws_amplify_api.aws_amplify_api import AmplifyAPI

# GRAPHQL_DATA_OUTPUT_FILE_PATH = "../graphql_output_data/listScanURLModels.json"
# QUERY_FILTER = 'filter: {country: {contains: "Italy"}, check_results: {attributeExists: true}, scanURLModelIPInformationModelId: {attributeExists: true}}'
QUERY_FILTER = ""



class GraphQLManager:
    """
    GraphQL manager for getting data.
    """

    def __init__(self):
        self.total_results = []
        self.unique_urls = []

    def send_graphql_query(self, query, next_token=None, total_processed_items=0, key='listScanURLModels', variables=None):
        """
        Executes a graphql query against an aws appsync endpoint
        :return:
        """
        # establish a session with requests session
        session = boto3.session.Session()
        credentials = session.get_credentials()
        region = session.region_name or 'eu-west-1'

        try:
            creds = json.loads(self.get_secret())
            print(creds)
        except Exception as e:
            creds = {
                "APPSYNC_URL": None,
                "api_key": None
            }
            print(e)


        headers={"Content-Type": "application/json", "x-api-key": os.environ.get('API_KEY', creds['api_key'])}

        endpoint = os.environ.get('APPSYNC_URL', creds['APPSYNC_URL'])

        # setup the query string (optional)
        if next_token:
            nt = ',nextToken:"%s"' % next_token
            qf = QUERY_FILTER + nt
        else:
            qf = QUERY_FILTER

        query = query.replace("QUERY_FILTER", qf)
        if variables:
            payload = {"query": query, 'variables': variables}
        else:
            payload = {"query": query}
        auth=AWSV4Sign(credentials, region, 'appsync')
        #print(query)
        #query = """query listItemsQuery {listItemsQuery {items {correlation_id, id, etc}}}"""

        # Now we can simply post the request...
        try:
            response = session.request(
                url=endpoint,
                auth=auth,
                method='POST',
                headers=headers,
                json=payload
            )
            results = response.json()
            print("Retrieved keys: %s" % results.keys())
        except Exception as e:
            print(json.dumps(payload, indent=4))
            print("Error in Graphql query: %s" % e)
            raise Exception(e)
        if key and "list" in key:
            results=results['data']
            #print(json.dumps(results, indent=True))
            next_token = response.json()['data'][key].get('nextToken', None)
            print(len(results), next_token)
            total_processed_items += len(results)

            for result in results:
                if not result['id'] in self.unique_urls:
                    self.unique_urls.append(result['id'])
                    self.total_results.append(result)
                    print("Added to results: %s" % result['name'])
                else:
                    print("%s already present in results" % result['url_name'])
            print("Processed items: %s"%total_processed_items)
            if next_token:
                query = query.replace(qf, 'QUERY_FILTER')
                #print(query)
                # with open(GRAPHQL_DATA_OUTPUT_FILE_PATH, 'w') as f:
                #     f.write(json.dumps(self.total_results, indent=True))
                return self.send_graphql_query(
                    query,
                    next_token,
                    total_processed_items,
                    key,
                    variables
                )
            else:
                return total_processed_items
        else:
            return results




    def get_secret(self, secret_name = "tv-ai-news-graphql-endpoint-and-api-key", region_name = "eu-west-1"):

        # Create a Secrets Manager client
        session = boto3.session.Session()
        client = session.client(
            service_name='secretsmanager',
            region_name=region_name
        )

        # In this sample we only handle the specific exceptions for the 'GetSecretValue' API.
        # See https://docs.aws.amazon.com/secretsmanager/latest/apireference/API_GetSecretValue.html
        # We rethrow the exception by default.
        secret = None
        try:
            get_secret_value_response = client.get_secret_value(
                SecretId=secret_name
            )
        except ClientError as e:
            if e.response['Error']['Code'] == 'DecryptionFailureException':
                # Secrets Manager can't decrypt the protected secret text using the provided KMS key.
                # Deal with the exception here, and/or rethrow at your discretion.
                raise e
            elif e.response['Error']['Code'] == 'InternalServiceErrorException':
                # An error occurred on the server side.
                # Deal with the exception here, and/or rethrow at your discretion.
                raise e
            elif e.response['Error']['Code'] == 'InvalidParameterException':
                # You provided an invalid value for a parameter.
                # Deal with the exception here, and/or rethrow at your discretion.
                raise e
            elif e.response['Error']['Code'] == 'InvalidRequestException':
                # You provided a parameter value that is not valid for the current state of the resource.
                # Deal with the exception here, and/or rethrow at your discretion.
                raise e
            elif e.response['Error']['Code'] == 'ResourceNotFoundException':
                # We can't find the resource that you asked for.
                # Deal with the exception here, and/or rethrow at your discretion.
                raise e
        else:
            # Decrypts secret using the associated KMS key.
            # Depending on whether the secret is a string or binary, one of these fields will be populated.
            if 'SecretString' in get_secret_value_response:
                secret = get_secret_value_response['SecretString']
            else:
                secret = base64.b64decode(get_secret_value_response['SecretBinary'])

        # Your code goes here.
        return secret

    def save_to_graphql_with_amplify(self, data:dict, data_type:str):
        amplify = AmplifyAPI()

        # Create a student
        item = amplify.create(data_type.capitalize(), data)

        # Create a subject
        # subject = amplify.create("Subject", {"name": "Math"})

        # Add the subject to the student
        # amplify.create("SubjectStudent", {"student": {"id": student["id"]}, "subject": {"id": subject["id"]}})

        # Get the subjects for a student
        # student_subjects = amplify.list("SubjectStudent", filter={"student": {"eq": student["id"]}})
        return item


if __name__ == "__main__":
    gm = GraphQLManager()
    start_time = time.monotonic()
    try:
        total_processed_items = gm.send_graphql_query()
    except KeyboardInterrupt:
        total_processed_items= len(gm.total_results)
        pass
    # with open(GRAPHQL_DATA_OUTPUT_FILE_PATH, 'w') as f:
    #     f.write(json.dumps(gm.total_results, indent=True))
    # print("Wrote: %s with %s elements"% (GRAPHQL_DATA_OUTPUT_FILE_PATH, len(gm.total_results)))

    end_time = time.monotonic()
    elapsed = end_time-start_time
    print("Read %s items in %s seconds" % (total_processed_items, elapsed))