FROM python:3-slim

COPY sources.list /etc/apt/
RUN apt update && apt install -y imagemagick ghostscript unrar libxslt1.1 curl

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