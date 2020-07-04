FROM python:3-slim

COPY sources.list /etc/apt/
RUN apt update && apt install -y imagemagick ghostscript unrar libxslt1.1

WORKDIR /root

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY server.py config.ini ./
ADD views ./views/
ADD static ./static/
# should be mounted as external volumes later
ADD Library ./Library/
ADD data ./data/

EXPOSE 80/tcp

CMD [ "python", "-u", "./server.py" ]