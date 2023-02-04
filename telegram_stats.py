import os, sys, json

OUTPUT_FOLDER_MESSAGES = os.getenv("OUTPUT_FOLDER_MESSAGES", "../messages/")
import parallelization

class TelegramStats:
    """
    Aggregates the tokens found in the different analysis of the messages.
    Who ?
    What ?
    When ?
    Where ?
    Why ?
    How ?
    """

    stats_format = {
        "who": {
            "types": ["PERSON"]
        },
        "what": {

        },
        "when": {
            "message": {},
            "content": {}
        },
        "where": {
            "types": ["LOCATION"]
        },
        "why": {

        },
        "how": {}
    }

    def __init__(self):
        self.messages=[]
        self.unique_message_signatures = []
        self.sentiments = {
            "items": {}
        }
        self.people = {
            "items": {}
        }

    def load_messages(self, local_messages_dir=True):
        messages = []
        if local_messages_dir:
            files = os.walk(OUTPUT_FOLDER_MESSAGES)
            messages = parallelization.process_urls_in_batch(
                files,
                self.load_local_messages, #function_to_be_run_in_the_thread
            )
        return messages

    def load_local_messages(self, file):
        """
        Loads JSON messages files from local
        :param messages_dir:
        :return:
        """

        with open(file, 'f') as f:
            message_json_file = json.loads(f.read())
        for message in message_json_file:
            if "signature" in message:
                if not message["signature"] in self.unique_message_signatures:
                    self.messages.append(message)
                    self.unique_message_signatures.append(message["signature"])
            # calculate sentiment
            try:
                self.sentiments["items"][
                    message["sentiment"]["sentiment"]
                ]["total"]+=1
                self.sentiments["items"][
                    message["sentiment"]["sentiment"]
                ]["signatures"].append(message["signature"])
            except:
                self.sentiments["items"][
                    message["sentiment"]["sentiment"]
                ]["total"]=1
                self.sentiments["items"][
                    message["sentiment"]["sentiment"]
                ]["signatures"] = [message["signature"]]


            if "keywords_found_in_image" in message:
                for word in message["keywords_found_in_image"]["celebs"]:
                    self.process_item_and_store_refs(word["name"], message["signature"], "celebs")
                for word in message["keywords_found_in_image"]["labels"]:
                    self.process_item_and_store_refs(word["Name"], message["signature"], "keywords")
                for word in message["keywords_found_in_image"]["text"]:
                    self.process_item_and_store_refs(word["word"], message["signature"], "keywords")

            if "keywords_found_in_video" in message:
                for word in message["keywords_found_in_video"]["labels"]["labels"]:
                    self.process_item_and_store_refs(word["name"], message["signature"], "keywords")
                for word in message["keywords_found_in_video"]["celebs"]["celebs"]:
                    self.process_item_and_store_refs(word["name"], message["signature"], "celebs")


            if "entities_in_message" in message:
                for e in message["entities_in_message"]:
                    if e["Type"] == "PERSON" or (e["name"].startswith("@") and (e["Type"] == "ORGANIZATION" or e["Type"] == "TITLE")):
                        self.process_item_and_store_refs(e["name"], message["signature"], "celebs")
                    elif e["Type"] == "LOCATION" or e["Type"] == "ORGANIZATION":
                        self.process_item_and_store_refs(e["name"], message["signature"], "locations")

        return self.data


    def process_item_and_store_refs(self, word, signature, category):
        try:
            self.data[category]["items"][word]["total"]+=1
            self.data[category]["items"][word]["signatures"].append(signature)
        except:
            self.data[category]["items"][word]["total"]=1
            self.data[category]["items"][word]["signatures"] = [signature]





