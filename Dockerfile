FROM python

RUN pip3 install boto3
RUN pip3 install requests
RUN pip3 install telethon

RUN mkdir -p /tmp/utils_dir
RUN mkdir -p /tmp/media
RUN mkdir -p /tmp/messages
RUN mkdir -p /tmp/output_data

COPY media_analyser.py /tmp/utils_dir
COPY s3_operations.py /tmp/utils_dir
COPY saver.py /tmp/utils_dir
COPY telegram_api.py /tmp/utils_dir
COPY video_detection.py /tmp/utils_dir
COPY session.session /tmp/utils_dir
COPY creds.json /tmp/utils_dir
COPY groups.json /tmp/utils_dir

VOLUME ["/tmp/utils_dir"]
WORKDIR /tmp/utils_dir
CMD [ "python3", "-m", "telegram_api", "--messages", "s3://telegram-output-data/groups_to_analyse__test.json"]

