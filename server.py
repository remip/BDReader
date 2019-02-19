#!/usr/bin/python
# -*- coding:UTF-8 -*-

import os
import io
import sys
import re
import string
import unicodedata
import zipfile
import rarfile
import filetype
from PIL import Image
from wand.image import Image as WandImage
from PyPDF2 import PdfFileReader
import requests
import configparser
import datetime
import zipfile
import rarfile
from peewee import *
from bottle import (route, post, redirect, run, template, static_file, request,
                    response)

# read configuration file
config = configparser.ConfigParser()
config.read('config.ini')
LIBRARY = config['Default']['library_path']
CACHE = config['Default']['cache_path']
HOST = config['Default']['host']
PORT = config['Default']['port']
DB = config['Default']['database']

EXT = ['pdf', 'cbz', 'cbr', 'zip', 'rar']
IMGEXT = ['.png', '.PNG', '.jpg', '.JPG', '.jpeg', '.JPEG']
thumbsize = (177, 250)
itemsByPage = 50
PDFDPI=300
MAXDPI=400

ERROR = open("error.log", "a", 1)


# connect/create database
db = SqliteDatabase(DB)

ENUM_EXT =[
    (1, "pdf"),
    (2, "cbz"),
    (3, "cbr"),
    (4, "zip"),
    (5, "rar")]

class EnumField(IntegerField):
    def __init__(self, choices, *args, **kwargs):
        self.to_db = {v:k for k, v in choices}
        self.from_db = {k:v for k, v in choices}
        super(IntegerField, self).__init__(*args, **kwargs)

    def db_value(self, value):
        return self.to_db[value]

    def python_value(self, value):
        return self.from_db[value]


class Library(Model):
    name = CharField(unique=True)
    dirname = CharField()

    class Meta:
        database = db
        order_by = ('name',)

class Serie(Model):
    name = CharField(unique=True, null=True)
    dirname = CharField()
    urlname = CharField(null=True)
    #library = ForeignKeyField(Library, related_name='library_series')
    link = CharField(default="")
    image = IntegerField(default=0)
    validated = BooleanField(default=False)
    added_date = DateTimeField(default=datetime.datetime.now)

    class Meta:
        database = db
        order_by = ('name',)

class Publisher(Model):
    name = CharField()

    class Meta:
        database = db
        order_by = ('name',)

class Album(Model):
    name = CharField(null=True)
    filename = CharField()
    urlname = CharField(null=True)
    filetype = EnumField(choices=ENUM_EXT, null=True)
    serie = ForeignKeyField(Serie, related_name='serie_albums')
    publisher = ForeignKeyField(Publisher, null=True, related_name='published_albums')
    summary = TextField(null=True)
    volume = SmallIntegerField(null=True)
    pages = SmallIntegerField(null=True)
    year = SmallIntegerField(null=True)
    link = CharField(null=True)
    read = BooleanField(default=False)
    validated = BooleanField(default=False)
    added_date = DateTimeField(default=datetime.datetime.now)

    class Meta:
        database = db
        order_by = ('name',)
        indexes = (
            (('name', 'serie'), True),
        )

ENUM_AUTHOR = [
    (1, 'writer'),
    (2, 'penciller'),
    (3, 'colorist')
]

class Author(Model):
    name = CharField()
    job = EnumField(choices=ENUM_AUTHOR)

    class Meta:
        database = db
        order_by = ('name',)

class AlbumAuthor(Model):
    album = ForeignKeyField(Album)
    author = ForeignKeyField(Author)

    class Meta:
        database = db

class Bookmark(Model):
    serie = ForeignKeyField(Serie)
    album = ForeignKeyField(Album)
    page = SmallIntegerField(default=1)
    added_date = DateTimeField(default=datetime.datetime.now)

    class Meta:
        database = db

if not os.path.isfile(DB):
    db.connect()
    db.create_tables([Library, Serie, Album, Author, AlbumAuthor, Publisher, Bookmark])
    print("Database '{}' created".format(DB))
else:
    db.connect()

@route('/')
@route('/page/<page>')
def index(page=1):
    page = int(page)
    prevpage = 0
    nextpage = 0

    series = Serie.select(Serie, fn.Count(Album.id).alias('count')).join(Album).group_by(Serie).paginate(page, itemsByPage)
    if page > 1:
        prevpage = page - 1

    if Serie.select().count() > itemsByPage*page:
        nextpage = page + 1

    return template('index', series=series, prevpage=prevpage, nextpage=nextpage)

@route('/random')
def random():
    albums = Album.select(Album).order_by(fn.Random()).limit(50)
    return template('random', serie="Random", albums=albums, prevpage=0, nextpage=0)

@route('/last')
def last():
    albums = Album.select(Album).order_by(Album.added_date.desc()).limit(50)
    return template('random', serie="Last", albums=albums)

@route('/serie/<serie>')
def showSerie(serie):
    serie = Serie.get(Serie.urlname == serie)
    albums = Album.select(Album, Serie).join(Serie).where(Serie.id == serie.id).order_by(Album.volume, Album.name)
    return template('serie', serie=serie, albums=albums)

@route('/album/<serie>/<album>')
def showAlbum(serie,album):

    serie = Serie.get(Serie.urlname == serie)
    album = Album.get(Album.urlname == album, Album.serie == serie)
    writers = []
    for writer in Author.select().join(AlbumAuthor).join(Album).where(Album.id == album.id, Author.job == 'writer'):
        writers.append(writer.name)
    pencillers = []
    for penciller in Author.select().join(AlbumAuthor).join(Album).where(Album.id == album.id, Author.job == 'penciller'):
        pencillers.append(penciller.name)
    colorists = []
    for colorist in Author.select().join(AlbumAuthor).join(Album).where(Album.id == album.id, Author.job == 'colorist'):
        colorists.append(colorist.name)

    return template('album', serie=serie, album=album, writers=", ".join(writers),
        pencillers=", ".join(pencillers), colorists=", ".join(colorists))

@route('/read/<serie>/<album>')
@route('/read/<serie>/<album>/<page>')
def readAlbum(serie, album, page=1):

    serie = Serie.get(urlname=serie)
    album = Album.get(serie=serie, urlname=album)
    bookmark, created = Bookmark.get_or_create(serie=serie, album=album)
    if bookmark:
        page = bookmark.page

    return template('read', serie=serie, album=album, page=page)

@route('/getpage/<serie>/<album>/<page>')
def getPage(serie, album, page):
    serie = Serie.get(Serie.urlname == serie)
    album = Album.get(Album.serie == serie, Album.urlname == album)
    page = int(page)

    file = os.path.join(LIBRARY, serie.dirname, album.filename)


    try:
        kind = filetype.guess(file)
        if kind.mime == 'application/zip' or kind.mime == 'application/x-rar-compressed':
            compress = None
            if kind.mime == 'application/zip':
                compress = zipfile.ZipFile(file,'r')
            else:
                compress = rarfile.RarFile(file,'r')
            #find the page
            filelist = [f for f in sorted(compress.namelist()) if os.path.splitext(f)[1] in IMGEXT]
            image = io.BytesIO(compress.read(filelist[page - 1]))
            compress.close()
            response.headers['Content-Type'] = filetype.guess(image.getvalue())
            return image.getvalue()

        elif kind.mime == 'application/pdf':
            with WandImage(filename=file + "[" + str(page - 1) + "]", resolution=PDFDPI) as image:
                image = image.make_blob('png')
            response.headers['Content-Type'] = 'image/png'
            return image
    except:
        print("Something wrong happens while reading page {}".format(page))
        e = sys.exc_info()
        print(e)


@route('/bookmarks')
def listBookmarks():

    bookmarks = Bookmark.select(Bookmark).order_by(Bookmark.added_date.desc())

    return template('bookmarks', bookmarks=bookmarks)


@post('/bookmark/<serie>/<album>')
def saveBookmark(serie, album):
    page = int(request.forms.get('page'))

    serie = Serie.get(urlname=serie)
    album = Album.get(serie=serie, urlname=album)
    bookmark, created = Bookmark.get_or_create(serie=serie, album=album)

    # end -> album read
    if page == album.pages:
        album.read = True
        album.save()
        bookmark.delete_instance()
    else:
        bookmark.page = page
        bookmark.save()

    return 'saved'

@route('/validate/serie/<serie>')
def validateSerie(serie=0):

    serie = Serie.select().where(Serie.validated==0).get()

    id = int(request.query.id) or 0


    return template('validateSerie', serie=serie)

@route('/validate/album/<album>')
def validateAlbum(album):
    return template('validateAlbum')

@route('/thumbnail/<id>')
def getImage(id):
    id = int(id)
    if id == 0:
        return static_file('blank.png', root=CACHE)

    if id < 10:
        id = "0" + str(id)
    else:
        id = str(id)

    key = id[-2:]

    if os.path.exists(os.path.join(CACHE, key, "{}.jpg".format(id))):
        filepath = os.path.join(key, "{}.jpg".format(id))
    else:
        filepath = "blank.png"

    return static_file(filepath, root=CACHE)

@route('/download/<serie>/<album>')
def download(serie,album):
    serie = Serie.get(Serie.urlname == serie)
    album = Album.get(Album.serie == serie, Album.urlname == album)

    return static_file(os.path.join(serie.dirname,album.filename), root=LIBRARY, download=True)

@route('/static/<filepath:path>')
def getStatic(filepath):
    return static_file(filepath, root='static')

@route('/settings')
def settings(newSeries = 0, newAlbums = 0, delSeries = 0, delAlbums = 0):

    totalAlbums = Album.select().count()
    totalSeries = Serie.select().count()

    return template('settings', newAlbums=newAlbums, newSeries=newSeries,
        delSeries = delSeries, delAlbums = delAlbums,
        totalAlbums=totalAlbums, totalSeries=totalSeries)

@route('/search')
def search():
    return template('search')

@post('/result')
def result():
    term = request.forms.get('term')

    series = Serie.select(Serie, fn.Count(Album.id).alias('count')).join(Album).where(Serie.name.contains(term)).group_by(Serie)
    albums = Album.select().where(Album.name.contains(term))

    return template('result', series=series, albums=albums)

@post('/rename/serie')
def renameSerie():
    urlname = request.forms.urlname
    name = request.forms.name

    serie = Serie.get(Serie.urlname == urlname)

    newdir = createFilename(name)
    newurl = createUrl(newdir)

    print("Renaming serie {} to {}, dir: {}, url:{}".format(serie.name, name, newdir, newurl))

    os.rename(os.path.join(LIBRARY, serie.dirname), os.path.join(LIBRARY, newdir))

    serie.name = name
    serie.dirname = newdir
    serie.urlname = newurl
    serie.save()

    redirect('/serie/{}'.format(newurl))

@post('/edit/album')
def editAlbum():
    serie = Serie.get(Serie.urlname == request.forms.serie)
    album = Album.get(Album.serie == serie, Album.urlname == request.forms.album)

    volume = request.forms.volume
    if volume == '':
        volume = None
    album.volume = volume

    name = request.forms.name
    if serie.name != name:
        newfile = serie.dirname
        newurl = ''
        if album.volume is not None:
            newfile += ' - T' + album.volume + ' -'
            newurl = 'T' + album.volume + '-'
        newfile += ' ' + createFilename(name) + '.' + album.filetype
        newurl = createUrl(newurl + name)

        print("Renaming album {} to {}, file: {}, url:{}".format(album.name, name, newfile, newurl))

        os.rename(os.path.join(LIBRARY, serie.dirname, album.filename),
            os.path.join(LIBRARY, serie.dirname, newfile))

        album.name = name
        album.filename = newfile
        album.urlname = newurl

    album.save()

    redirect('/album/{}/{}'.format(serie.urlname, album.urlname))

@route('/mark/<mark>/<serie>/<album>')
def mark(mark, serie, album):
    serie = Serie.get(Serie.urlname == serie)
    album = Album.get(Album.serie == serie, Album.urlname == album)

    if mark == 'read':
        album.read = True
        album.save()
    elif mark == 'unread':
        album.read = False
        album.save()
    else:
        print("Warning: unknown mark: '{}'".format(mark))

    redirect('/album/{}/{}'.format(serie.urlname, album.urlname))


@route('/scan')
def scanLibrary():
    """
        Scan the library path for new series or albums
    """
    newSeries = 0
    newAlbums = 0
    delSeries = 0
    delAlbums = 0

    dbseries = []
    for serie in Serie.select():
        dbseries.append(serie.name)

    folders = [folder for folder in os.listdir(LIBRARY) if os.path.isdir(os.path.join(LIBRARY, folder))]

    for folder in folders:
        serie, created = Serie.get_or_create(dirname=folder)
        if created:
            urlname = createUrl(folder)
            serie.name = folder
            serie.urlname = urlname
            serie.save()
            print("Add Serie {} [{}]".format(folder, urlname))
            newSeries += 1
        else:
            dbseries.remove(folder)

        re_title = re.escape(serie.dirname) + r' - T(\d+) - (.*)\.\w{3}'

        files = [file for file in os.listdir(os.path.join(LIBRARY, folder)) if os.path.isfile(os.path.join(LIBRARY, folder, file)) and any(file.endswith(ext) for ext in EXT)]

        for file in files:
            album, created = Album.get_or_create(filename=file, serie=serie)
            if created:
                s = re.search(re_title, file)
                if s:
                    album.volume = s.group(1)
                    title = s.group(2)
                else:
                    title = os.path.splitext(file)[0]

                urlname = createUrl(title)
                album.name = title
                album.filetype = os.path.splitext(file)[1].lower()[1:]
                album.urlname = urlname
                pages = countPages(os.path.join(LIBRARY, folder, file))
                if pages > 0:
                    album.pages = pages
                album.save()
                print("Add Album {} [{}] {} pages".format(title, urlname, pages))
                newAlbums += 1
                if createThumb(os.path.join(LIBRARY, folder, file), getThumb(album.id)):
                    # update serie if needed
                    if serie.image == 0:
                        print("Update serie thumbnail")
                        serie.image = album.id
                        serie.save()

    for folder in dbseries:
        print("Delete {}".format(folder))
        serie = Serie.get(Serie.name == folder)
        delSeries += 1
        delAlbums += Album.select().where(Album.serie == serie).count()
        serie.delete_instance(recursive=True)

    return settings(newSeries, newAlbums, delSeries, delAlbums)

def createUrl(name):
    """
        Make an url friendly string
    """
    name = name.lower()
    name = name.replace('#', 't')
    name = name.replace('\'', '-')
    name = name.replace('-', ' ')
    name = name.translate(str.maketrans({key: None for key in string.punctuation}))
    name = name.replace(' ', '-')
    name = re.sub('-+', '-', name)
    name = re.sub('^-', '', name)
    name = re.sub('-$', '', name)
    name = unicodedata.normalize('NFD', name).encode('ascii', 'ignore')
    return name.decode()

def createFilename(name):
    """
        Remove forbidden chars for a filename
    """
    name = name.replace('\\','')
    name = name.replace('/','')
    name = name.replace(':','')
    name = name.replace('*','')
    name = name.replace('?','')
    name = name.replace('"','')
    name = name.replace('<','')
    name = name.replace('>','')
    name = name.strip()
    return name

def getThumb(id):
    """
        Get the album jpeg thumbnail path in cache from the album id
    """
    if id < 10:
        id = "0" + str(id)
    else:
        id = str(id)

    key = id[-2:]

    if not os.path.exists(os.path.join(CACHE, key)):
        os.mkdir(os.path.join(CACHE, key))
    return os.path.join(CACHE, key, "{}.jpg".format(id))

def countPages(file):
    """
        Open the comic file and count the number of pages
    """

    try:
        kind = filetype.guess(file)
        if kind.mime == 'application/zip' or kind.mime == 'application/x-rar-compressed':
            compress = None
            if kind.mime == 'application/zip':
                compress = zipfile.ZipFile(file,'r')
            else:
                compress = rarfile.RarFile(file,'r')
            #find the page
            filelist = [f for f in sorted(compress.namelist()) if os.path.splitext(f)[1] in IMGEXT]
            return len(filelist)

        elif kind.mime == 'application/pdf':
            pdf = PdfFileReader(open(file, "rb"))
            return pdf.getNumPages()
    except:
        print("Something wrong happens while counting pages of {}".format(file))
        e = sys.exc_info()
        print(e)

    return 0

def createThumb(file, thumbnail):
    """
        Open the comic file and generate a jpeg thumbnail of the first page
    """
    cover = None
    try:
        index = 0
        kind = filetype.guess(file)
        if kind is None:
            print("File type unknown {}".format(file))
            ERROR.write("File type unknown {}".format(file)+"\n")
            return False
        if kind.mime == 'application/zip':
            zip = zipfile.ZipFile(file,'r')
            #find the first image
            filelist = sorted(zip.namelist())
            while not (filelist[index].endswith(".jpg") or filelist[index].endswith(".jpeg") or filelist[index].endswith(".JPG") or filelist[index].endswith(".png")):
                index += 1
            cover = io.BytesIO(zip.read(filelist[index]))
            zip.close()
        elif kind.mime == 'application/x-rar-compressed':
            rar = rarfile.RarFile(file,'r')
            #find the first image
            filelist = sorted(rar.namelist())
            while not (filelist[index].endswith(".jpg") or filelist[index].endswith(".jpeg") or filelist[index].endswith(".JPG") or filelist[index].endswith(".png")):
                index += 1
            cover = io.BytesIO(rar.read(filelist[index]))
            rar.close()
        elif kind.mime == 'application/pdf':
            with WandImage(filename=file+"[0]") as original:
                original.transform(resize="{}x{}>".format(thumbsize[0], thumbsize[1]))
                original.save(filename=thumbnail)
                return True
        else:
            print("File format not handled {} {}".format(kind.mime, file))
            ERROR.write("File format not handled {} {}".format(kind.mime, file)+"\n")
            return False

        im = Image.open(cover)
        im.thumbnail(thumbsize)
        im.save(thumbnail, "JPEG")

        return True

    except:
        e = sys.exc_info()
        print("Cannot create thumbnail {} for {}".format(thumbnail, file))
        print(e)
        ERROR.write("Cannot create thumbnail {} for {}".format(thumbnail, file)+"\n")
        ERROR.write(str(e)+"\n\n")
        return False

@route('/hint/author/<term>')
def authorHint(term):
    json = ''
    return json

@route('/scrap/serie/<text>')
def scrapSerie(text):
    print("scrap '{}'".format(text))
    #https://www.bedetheque.com/search/albums?RechIdSerie=&RechIdAuteur=&csrf_token_bedetheque=3cc59c74f310bd58b0379d4561eba126&RechSerie=ca+vous+int%C3%A9resse&RechTitre=&RechEditeur=&RechCollection=&RechStyle=&RechAuteur=&RechISBN=&RechParution=&RechOrigine=&RechLangue=&RechMotCle=&RechDLDeb=&RechDLFin=&RechCoteMin=&RechCoteMax=&RechEO=0
    r = requests.get('https://www.bedetheque.com/ajax/series?term={}'.format(text))
    #[{"id":"36","label":"Nef des fous (La)","value":"Nef des fous (La)","desc":"skin\/flags\/France.png"}]
    print(r.text)

    return r.text

def scrapAlbum(text):
    r = requests.get('https://www.bedetheque.com/ajax/albums?term={}'.format(text))
    list = []

    for e in r.json():
        list.append(e['value'])
    return list

if len(sys.argv) > 1 and sys.argv[1] == '--scan':
    print("Initial Library scan")
    scanLibrary()
    sys.exit(0)

run(host=HOST, port=PORT, reloader=True)
