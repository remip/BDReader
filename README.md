# BDReader

BD "Bande Dessinée" is the french acronym for Comic.

## Install

### Windows

install winrar and put the path to unrar.exe in %PATH%

install ImageMagick select update path & install c/c++ headers
http://docs.wand-py.org/en/0.4.4/guide/install.html#install-imagemagick-windows

install ghostscript
https://www.ghostscript.com/download/gsdnld.html

pip install -r requirements.txt

### Ubuntu

apt install libmagickwand-dev ghostscript unrar libxslt1.1
pip install -r requirements.txt

### docker

Compose file use two volumes, first one is the path to the comic library, second one is for storing database and thumbnails.
```
docker volume create bd-data
docker-compose up -d
```

Scan the library from command line:

`docker exec -it bdreader python server.py --scan`



Icons made by https://www.flaticon.com/authors/smashicons licensed by CC 3.0 BY