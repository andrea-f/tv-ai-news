FROM python:3.8
RUN mkdir -p /tmp/utils_dir
COPY ./* /tmp/utils_dir
COPY templates /tmp/utils_dir/templates
COPY static /tmp/utils_dir/static
VOLUME ["/tmp/utils_dir"]
WORKDIR /tmp/utils_dir
RUN pip3 install -r requirements.txt
EXPOSE 80
CMD [ "python3", "-m", "server", "80"]

