import hashlib
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
        self.data = {}

    def load_messages(self, local_messages_dir=True):
        messages = []
        if local_messages_dir:
            files = os.walk(OUTPUT_FOLDER_MESSAGES)
            messages = parallelization.process_urls_in_batch(
                files,
                self.calculate_stats_messages, #function_to_be_run_in_the_thread
            )
        return messages

    def calculate_stats_messages(self, file_name):
        """
        Loads JSON messages files from local
        :param messages_dir:
        :return:
        """

        with open(file_name, 'r') as f:
            message_json_file = json.loads(f.read())
            print(message_json_file[0].keys())
        c=0
        for message in message_json_file:
            print(c, "/", len(message_json_file))
            if not "signature" in message:
                unique_str = "%s%s%s" % (message.get("message", ""), message['message_date'], message["group_name"])
                message["signature"] = hashlib.md5(unique_str.encode('utf-8', errors="ignore")).hexdigest()

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
                if message["sentiment"].get("sentiment",None):
                    if not self.sentiments["items"].get(message["sentiment"]["sentiment"], None):
                        self.sentiments["items"][
                            message["sentiment"]["sentiment"]
                        ] = {}
                    self.sentiments["items"][
                        message["sentiment"]["sentiment"]
                    ]["total"]=1
                    self.sentiments["items"][
                        message["sentiment"]["sentiment"]
                    ]["signatures"] = [message["signature"]]


            if "keywords" in message:
                for word in message["keywords"]:
                    self.process_item_and_store_refs(word["name"], message["signature"], "keywords")



            if "entities" in message:
                for e in message["entities"]:
                    if e["Type"] == "PERSON" or (e["Text"].startswith("@") and (e["Type"] == "ORGANIZATION" or e["Type"] == "TITLE")):
                        self.process_item_and_store_refs(e["Text"], message["signature"], "celebs")
                    elif e["Type"] == "LOCATION":
                        self.process_item_and_store_refs(e["Text"], message["signature"], "locations")
                    elif e["Type"] == "ORGANIZATION":
                        print(e["Text"])
                        self.process_item_and_store_refs(e["Text"], message["signature"], "organizations")
            c+=1


        k = sorted(self.data["keywords"]['items'].items(), key=lambda item: item[1]["total"], reverse=True)
        p = sorted(self.data["celebs"]['items'].items(), key=lambda item: item[1]["total"], reverse=True)
        l = sorted(self.data["locations"]['items'].items(), key=lambda item: item[1]["total"], reverse=True)
        o = sorted(self.data["organizations"]['items'].items(), key=lambda item: item[1]["total"], reverse=True)
        with open("results3.json", 'w') as f:
            f.write(json.dumps({
                "keywords": k,
                "people": p,
                "locations": l,
                "organizations": o,
                "sentiments": self.sentiments
            }, indent=4))
        return self.data, self.sentiments


    def process_item_and_store_refs(self, word, signature, category):
        try:
            self.data[category]["items"][word]["total"]+=1
            #self.data[category]["items"][word]["signatures"].append(signature)
        except Exception as e:
            if not self.data.get(category, None):
                self.data[category]={"items":{}}
            self.data[category]["items"][word] = {
                "total": 1,
                #"signatures": [signature]
            }






if __name__ == "__main__":
    pass


