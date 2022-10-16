FROM python:3.9-slim-bullseye

COPY sources.list /etc/apt/
RUN apt-get update && apt-get install -y imagemagick ghostscript unrar libxslt1.1 curl
#raspbian
#RUN apt install -y libxml2-dev libxslt-dev zlib1g-dev build-essential
RUN apt-get install -y libopenjp2-7 libwebpdemux2 libjbig0 libtiff5 libwebp6 libwebpmux3 liblcms2-2 libzstd1
ADD pip.conf /etc/pip.conf

WORKDIR /root

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY server.py config.ini ./
ADD views ./views/
ADD static ./static/
# should be mounted as external volumes later
ADD Library ./Library/
ADD data ./data/

HEALTHCHECK --interval=30s --timeout=5s --retries=2 CMD curl -f http://localhost/ || exit 1

EXPOSE 80/tcp

CMD [ "python", "-u", "./server.py" ]