#!/usr/bin/python
# -*- coding:UTF-8 -*-

import os
import io
import sys
import time
import shutil
import re
import string
import unicodedata
import zipfile
import rarfile
import filetype
import traceback
import logging
from logging.handlers import RotatingFileHandler
from multiprocessing import Process, Lock
from PIL import Image
from wand.image import Image as WandImage
from PyPDF2 import PdfFileReader
import requests
import configparser
import datetime
import zipfile
import rarfile
from lxml import objectify
from peewee import *
from playhouse.migrate import *
from bottle import (route, post, redirect, run, template, static_file, request,
                    response, abort)
import humanize

# read configuration file
config = configparser.ConfigParser()
config.read('config.ini')
LIBRARY = config['Default']['library_path']
DATA = config['Default']['data_path']
CACHE = os.path.join(DATA, "cache")
HOST = config['Default']['host']
PORT = config['Default']['port']
DB = os.path.join(DATA, "library.db")
CONVERTED_ARCHIVE = os.path.join(DATA, "converted")
ERROR_LOG = os.path.join(DATA, "error.log")

EXT = ['pdf', 'cbz', 'cbr', 'zip', 'rar']
IMGEXT = ['.png', '.PNG', '.jpg', '.JPG', '.jpeg', '.JPEG']
thumbsize = (177, 250)
itemsByPage = 50
PDFDPI=300
MAXDPI=400

logger = logging.getLogger()
logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s :: %(levelname)s :: %(message)s')
file_handler = RotatingFileHandler(ERROR_LOG, 'a', 1000000, 1)
file_handler.setLevel(logging.ERROR)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)
stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.INFO)
logger.addHandler(stream_handler)


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

DB_VERSION = "1.1"

class History(Model):
    version = CharField()
    date = DateTimeField(default=datetime.datetime.now)

    class Meta:
        database = db
        order_by = ('version',)

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
    complete = BooleanField(default=False)

    class Meta:
        database = db
        order_by = ('name',)

class Publisher(Model):
    name = CharField()

    class Meta:
        database = db
        order_by = ('name',)

class Imprint(Model):
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
    imprint = ForeignKeyField(Imprint, null=True, related_name='imprint_albums')
    summary = TextField(null=True)
    volume = CharField(null=True)
    pages = SmallIntegerField(null=True)
    year = SmallIntegerField(null=True)
    link = CharField(null=True)
    read = BooleanField(default=False)
    validated = BooleanField(default=False)
    added_date = DateTimeField(default=datetime.datetime.now)

    class Meta:
        database = db
        order_by = ('volume', 'name',)
        indexes = (
            (('serie', 'name', 'volume'), True),
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

# create db if needed
if not os.path.isfile(DB):
    db.connect()
    db.create_tables([Library, Serie, Album, Author, AlbumAuthor, Publisher, Imprint, Bookmark, History])
    History.create(version=DB_VERSION)
    logger.info("Database '{}' created".format(DB))
else:
    db.connect()
    try:
        db_version = History.select(History.version).order_by(History.version.desc()).get().version
    except:
        #default to 1.0
        db_version = "1.0"
    logger.info("DB version {}".format(db_version))
    # upgrade DB?
    if db_version == "1.0":
        db.create_tables([History])
        History.create(version=DB_VERSION)
        migrator = SqliteMigrator(db)
        complete_field = BooleanField(default=False)
        migrate(
            migrator.add_column('serie', 'complete', complete_field),
        )
        logger.info("DB upgraded to version {}".format(DB_VERSION))
        sys.exit(1)



#create cache folders if needed
if not os.path.exists(CACHE):
    os.mkdir(CACHE)
    for i in range(100):
        os.mkdir(os.path.join(CACHE,"{:02d}".format(i)))
    logger.info("Cache created")

if not os.path.exists(CONVERTED_ARCHIVE):
    os.mkdir(CONVERTED_ARCHIVE)

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
@route('/last/<page>')
def last(page=1):
    page = int(page)
    prevpage = 0
    nextpage = 0

    albums = Album.select(Album).order_by(Album.added_date.desc()).paginate(page, itemsByPage)
    if page > 1:
        prevpage = page - 1

    if Album.select().count() > itemsByPage*page:
        nextpage = page + 1

    return template('random', serie="Last", albums=albums, prevpage=prevpage, nextpage=nextpage, action='last')

@route('/date')
@route('/date/<page>')
def bydate(page=1):
    page = int(page)
    prevpage = 0
    nextpage = 0

    albums = Album.select(Album).order_by(Album.year.desc()).paginate(page, itemsByPage)
    if page > 1:
        prevpage = page - 1

    if Album.select().count() > itemsByPage*page:
        nextpage = page + 1

    return template('date', serie="Date", albums=albums, prevpage=prevpage, nextpage=nextpage, action='date')

@route('/serie/<serie>')
def showSerie(serie):
    serie = Serie.get(Serie.urlname == serie)
    albums = Album.select(Album, Serie).join(Serie).where(Serie.id == serie.id).order_by(Album.volume.cast('int'), Album.name)
    return template('serie', serie=serie, albums=albums)

@route('/album/<serie>/<album>')
def showAlbum(serie,album):

    serie = Serie.get(Serie.urlname == serie)
    album = Album.get(Album.urlname == album, Album.serie == serie)
    sizemb = int(os.stat(os.path.join(LIBRARY, serie.dirname, album.filename)).st_size/1024/1024)
    writers = []
    for writer in Author.select().join(AlbumAuthor).join(Album).where(Album.id == album.id, Author.job == 'writer'):
        writers.append(writer.name)
    pencillers = []
    for penciller in Author.select().join(AlbumAuthor).join(Album).where(Album.id == album.id, Author.job == 'penciller'):
        pencillers.append(penciller.name)
    colorists = []
    for colorist in Author.select().join(AlbumAuthor).join(Album).where(Album.id == album.id, Author.job == 'colorist'):
        colorists.append(colorist.name)

    return template('album', serie=serie, album=album, writers=writers,
        pencillers=pencillers, colorists=colorists, sizemb=sizemb)

@route('/read/<serie>/<album>')
@route('/read/<serie>/<album>/<page>')
def readAlbum(serie, album, page=1):

    serie = Serie.get(urlname=serie)
    album = Album.get(serie=serie, urlname=album)
    bookmark, created = Bookmark.get_or_create(serie=serie, album=album)
    if bookmark:
        page = bookmark.page

    return template('read', serie=serie, album=album, page=page)

file_cache = [] # { file, object, filelist}
CACHE_SIZE = 5

@route('/getpage/<serie>/<album>/<page>')
def getPage(serie, album, page):
    logger.debug("getpage: start"); ts_start = time.time()
    serie = Serie.get(Serie.urlname == serie)
    album = Album.get(Album.serie == serie, Album.urlname == album)
    page = int(page)

    file = os.path.join(LIBRARY, serie.dirname, album.filename)

    # search in cached opened archives
    for item in file_cache:
        if item["file"] == file:
            image = io.BytesIO(item["compress"].read(item["filelist"][page - 1]))
            response.headers['Content-Type'] = filetype.guess(image.getvalue())
            logger.debug("getpage: zip/rar end {}s".format(time.time()-ts_start))
            return image.getvalue()

    # if not in cache
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

            # cache the archive
            file_cache.insert(0, {'file': file, 'filelist': filelist, 'compress': compress}) # insert at beginning
            if len(file_cache) > CACHE_SIZE:
                o = file_cache.remove(CACHE_SIZE) # remove last
                o['object'].close()

            image = io.BytesIO(compress.read(filelist[page - 1]))
            response.headers['Content-Type'] = filetype.guess(image.getvalue())
            logger.debug("getpage: zip/rar end {}s".format(time.time()-ts_start))
            return image.getvalue()

        elif kind.mime == 'application/pdf':
            with WandImage(filename=file + "[" + str(page - 1) + "]", resolution=PDFDPI) as image:
                image = image.make_blob('png')
            response.headers['Content-Type'] = 'image/png'
            logger.debug("getpage: pdf end {}s".format(time.time()-ts_start))
            return image
    except:
        logger.error("Something wrong happens while reading page {}".format(page))
        logger.error(traceback.format_exc())


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
        return static_file('blank.png', root='static')

    if id < 10:
        id = "0" + str(id)
    else:
        id = str(id)

    key = id[-2:]

    if os.path.exists(os.path.join(CACHE, key, "{}.jpg".format(id))):
        filepath = os.path.join(key, "{}.jpg".format(id))
        return static_file(filepath, root=CACHE)

    return static_file('blank.png', root='static')


@route('/download/<serie>/<album>')
def download(serie,album):
    serie = Serie.get(Serie.urlname == serie)
    album = Album.get(Album.serie == serie, Album.urlname == album)

    return static_file(os.path.join(serie.dirname,album.filename), root=LIBRARY, download=True)

@route('/static/<filepath:path>')
def getStatic(filepath):
    return static_file(filepath, root='static')

def get_size(start_path = '.'):
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(start_path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            total_size += os.path.getsize(fp)
    return total_size

@route('/settings')
def settings(newSeries = 0, newAlbums = 0, delSeries = 0, delAlbums = 0):

    totalAlbums = Album.select().count()
    totalSeries = Serie.select().count()
    totalValidated = Album.select().where(Album.validated==True).count()
    totalCBZ = Album.select().where(Album.filetype == 'cbz').count()
    totalCBR = Album.select().where(Album.filetype == 'cbr').count()
    totalPDF = Album.select().where(Album.filetype == 'pdf').count()
    totalAuthors = Author.select().count()
    completeSeries = Serie.select().where(Serie.complete).count()
    seriesNoLink = Serie.select().where(Serie.link == '').count()

    totalSize = humanize.naturalsize(get_size(LIBRARY))

    return template('settings', newAlbums=newAlbums, newSeries=newSeries,
        delSeries = delSeries, delAlbums = delAlbums,
        totalAlbums=totalAlbums, totalSeries=totalSeries, totalAuthors=totalAuthors,
        totalValidated=totalValidated, totalCBZ=totalCBZ, totalCBR=totalCBR, totalPDF=totalPDF, totalSize=totalSize,
        cache_used=len(file_cache), cache_total=CACHE_SIZE, completeSeries=completeSeries,
        seriesNoLink=seriesNoLink)

@route('/search/<field>/<term>')
def fieldsearch(field, term):

    if field == 'Title':
        series = Serie.select(Serie, fn.Count(Album.id).alias('count')).join(Album).where(Serie.name.contains(term)).group_by(Serie)
        albums = Album.select().where(Album.name.contains(term))
    else :
        try:
            Object = globals()[field.capitalize()]
        except KeyError:
            abort(500, "Bad search field")

        if field.capitalize() == 'Author':
            series = Serie.select(Serie, fn.Count(Album.id.distinct()).alias('count')).join(Album).join(AlbumAuthor).join(Author).where(Author.name.contains(term)).group_by(Serie)
            albums = Album.select().join(AlbumAuthor).join(Author).where(Author.name.contains(term)).group_by(Album)
        else:
            series = Serie.select(Serie, fn.Count(Album.id).alias('count')).join(Album).join(Object).where(Object.name.contains(term)).group_by(Serie)
            albums = Album.select().join(Object).where(Object.name.contains(term))

    return template('result', series=series, albums=albums, field=field.capitalize(), term=term)

@route('/link/<field>/<term>')
def exactsearch(field, term):

    try:
        Object = globals()[field.capitalize()]
    except KeyError:
        abort(500, "Bad search field")

    if field.capitalize() == 'Author':
        series = Serie.select(Serie, fn.Count(Album.id.distinct()).alias('count')).join(Album).join(AlbumAuthor).join(Author).where(Author.name == term).group_by(Serie)
        albums = Album.select().join(AlbumAuthor).join(Author).where(Author.name == term).group_by(Album)
    else:
        series = Serie.select(Serie, fn.Count(Album.id).alias('count')).join(Album).join(Object).where(Object.name == term).group_by(Serie)
        albums = Album.select().join(Object).where(Object.name == term)

    return template('result', series=series, albums=albums, field=field.capitalize(), term=term)

@route('/author')
def authorlist():
    #python_value(lambda idlist: ", ".join(ENUM_AUTHOR[int(i)][1] for i in idlist.split(',')))
    authors = Author.select(Author.name,
                            fn.GROUP_CONCAT(Author.job.distinct()).coerce(False).alias('jobs'), fn.count(Album.id.distinct()).alias('albumcount')
                           ).join(AlbumAuthor).join(Album).group_by(Author.name).order_by(SQL('albumcount').desc())

    joblist = {}
    for x in ENUM_AUTHOR:
        joblist[str(x[0])] = x[1]

    return template('author', authors=authors, joblist=joblist)


@route("/complete/<urlname>")
def complete_serie(urlname):

    serie = Serie.get(Serie.urlname == urlname)

    serie.complete = not serie.complete
    serie.save()

    redirect('/serie/{}'.format(serie.urlname))

@post('/rename/serie')
def renameSerie():
    urlname = request.forms.urlname
    name = request.forms.name

    serie = Serie.get(Serie.urlname == urlname)

    newdir = createFilename(name)
    newurl = createUrl(newdir)

    logger.info("Renaming serie {} to {}, dir: {}, url:{}".format(serie.name, name, newdir, newurl))

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

        logger.info("Renaming album {} to {}, file: {}, url:{}".format(album.name, name, newfile, newurl))

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
        logger.info("Warning: unknown mark: '{}'".format(mark))

    redirect('/album/{}/{}'.format(serie.urlname, album.urlname))


@route('/scan')
def scanLibrary():
    """
        Scan the library path for new series or albums
    """

    logger.info("Starting library scan")

    newSeries = 0
    newAlbums = 0
    delSeries = 0
    delAlbums = 0

    dbseries = []
    for serie in Serie.select():
        dbseries.append(serie.dirname)

    dbalbums = []
    for album in Album.select():
        dbalbums.append(album.filename)

    folders = [folder for folder in os.listdir(LIBRARY) if os.path.isdir(os.path.join(LIBRARY, folder))]

    for folder in folders:
        serie, created = Serie.get_or_create(dirname=folder)
        if created:
            urlname = createUrl(folder)
            serie.name = folder
            serie.urlname = urlname
            serie.save()
            logger.info("Add Serie {} [{}]".format(folder, urlname))
            newSeries += 1
        else:
            try:
                dbseries.remove(folder)
            except Exception as e:
                print("folder: {}\n{}".format(folder, str(e)))
                raise(e)

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
                logger.info("Add Album {} [{}] {} pages".format(title, urlname, pages))
                newAlbums += 1
                getComicInfo(os.path.join(LIBRARY, folder, file), album)
                if createThumb(os.path.join(LIBRARY, folder, file), getThumb(album.id)):
                    # update serie if needed
                    if serie.image == 0:
                        logger.info("Update serie thumbnail")
                        serie.image = album.id
                        serie.save()
            else:
                dbalbums.remove(file)

    for folder in dbseries:
        logger.info("Delete {}".format(folder))
        serie = Serie.get(Serie.name == folder)
        delSeries += 1
        delAlbums += Album.select().where(Album.serie == serie).count()
        serie.delete_instance(recursive=True)

    logger.info("There is {} albums with file missing".format(len(dbalbums)))
    for filename in dbalbums:
        delAlbums += 1
        album = Album.get(Album.filename == filename)
        album.delete_instance(recursive=True)

    logger.info("Library scan ended")

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
            # find the images
            filelist = [f for f in sorted(compress.namelist()) if os.path.splitext(f)[1] in IMGEXT]
            return len(filelist)

        elif kind.mime == 'application/pdf':
            pdffile = open(file, "rb")
            pdf = PdfFileReader(pdffile)
            num = pdf.getNumPages()
            pdffile.close()
            return num
    except:
        logger.error("Something wrong happens while counting pages of {}".format(file))
        logger.error(traceback.format_exc())

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
            logger.error("File type unknown {}".format(file))
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
            logger.error("File format not handled {} {}".format(kind.mime, file))
            return False

        im = Image.open(cover)
        im.thumbnail(thumbsize)
        im.save(thumbnail, "JPEG")

        return True

    except:
        logger.error("Cannot create thumbnail {} for {}".format(thumbnail, file))
        logger.error(traceback.format_exc())
        return False

@route('/hint/author/<term>')
def authorHint(term):
    json = ''
    return json

@route('/scrap/serie/<text>')
def scrapSerie(text):
    logger.info("scrap '{}'".format(text))
    #https://www.bedetheque.com/search/albums?RechIdSerie=&RechIdAuteur=&csrf_token_bedetheque=3cc59c74f310bd58b0379d4561eba126&RechSerie=ca+vous+int%C3%A9resse&RechTitre=&RechEditeur=&RechCollection=&RechStyle=&RechAuteur=&RechISBN=&RechParution=&RechOrigine=&RechLangue=&RechMotCle=&RechDLDeb=&RechDLFin=&RechCoteMin=&RechCoteMax=&RechEO=0
    r = requests.get('https://www.bedetheque.com/ajax/series?term={}'.format(text))
    #[{"id":"36","label":"Nef des fous (La)","value":"Nef des fous (La)","desc":"skin\/flags\/France.png"}]
    print(r.text)

    return r.text

@route('/convert/<serie>/<album>')
def convert(serie, album):
    convert_thread(serie, album)
    #redirect('/settings')

def convert_thread(serie, album):
    logger.debug("convert: start"); ts_start = time.time()
    serie = Serie.get(Serie.urlname == serie)
    album = Album.get(Album.serie == serie, Album.urlname == album)

    file = os.path.join(LIBRARY, serie.dirname, album.filename)
    cbzfile = os.path.join(LIBRARY, serie.dirname, createFilename(album.name) + '.cbz')

    try:
        kind = filetype.guess(file)
        if kind.mime == 'application/zip' or kind.mime == 'application/x-rar-compressed':
            # nothing to do !
            pass

        elif kind.mime == 'application/pdf':
            with zipfile.ZipFile(cbzfile, 'w', compression=zipfile.ZIP_STORED) as cbz:
                with WandImage(filename=file, resolution=PDFDPI) as images:
                    pages = len(images.sequence)
                    for page in range(pages):
                        image = WandImage(images.sequence[page]).make_blob('jpeg')
                        cbz.writestr("page{:03d}.jpeg".format(page+1), image)

            logger.debug("convert: end {}s".format(time.time() - ts_start))
            shutil.move(file, CONVERTED_ARCHIVE)
            album.filename = cbzfile
            album.filetype = 'cbz'
            album.save()

    except:
        logger.error("Something wrong happens while converting album {}".format(album.name))
        logger.error(traceback.format_exc())


@route('/refresh/<serie>/<album>')
def updateComicInfo(serie,album):

    logger.info("Refresh {} / {}".format(serie, album))

    serie = Serie.get(Serie.urlname == serie)
    album = Album.get(Album.urlname == album, Album.serie == serie)

    getComicInfo(os.path.join(LIBRARY, serie.dirname, album.filename), album)

    redirect('/album/{}/{}'.format(serie.urlname, album.urlname))

def getComicInfo(file, album):
    archive = None
    try:
        kind = filetype.guess(file)
        if kind.mime == 'application/zip':
            archive = zipfile.ZipFile(file,'r')
        elif kind.mime == 'application/x-rar-compressed':
            archive = rarfile.RarFile(file,'r')

        if archive:
            if 'ComicInfo.xml' in archive.namelist():
                has_writer = False
                logger.info("Getting info from ComicInfo.xml")
                xml = objectify.fromstring(archive.read('ComicInfo.xml'))
                if hasattr(xml, 'Title'):
                    logger.debug('Title: {}'.format(xml.Title))
                    album.name = xml.Title
                if hasattr(xml, 'Number'):
                    logger.debug('Number: {}'.format(xml.Number))
                    album.volume = xml.Number
                if hasattr(xml, 'Summary'):
                    logger.debug('Summary: {}'.format(xml.Summary))
                    album.summary = xml.Summary
                if hasattr(xml, 'Publisher'):
                    logger.debug('Publisher: {}'.format(xml.Publisher))
                    publisher, created = Publisher.get_or_create(name=xml.Publisher)
                    if created:
                        publisher.save()
                    album.publisher = publisher
                if hasattr(xml, 'Imprint'):
                    logger.debug('Imprint: {}'.format(xml.Imprint))
                    imprint, created = Imprint.get_or_create(name=xml.Imprint)
                    if created:
                        imprint.save()
                    album.imprint = imprint
                if hasattr(xml, 'Year'):
                    logger.debug('Year: {}'.format(xml.Year))
                    album.year = xml.Year
                if hasattr(xml, 'Web'):
                    logger.debug('Web: {}'.format(xml.Web))
                    album.link = xml.Web
                if hasattr(xml, 'Writer'):
                    for writers in xml.Writer:
                        for writer in str(writers).split(", "):
                            logger.debug('Writer: {}'.format(writer))
                            author, created = Author.get_or_create(name=writer, job='writer')
                            if created:
                                author.save()
                            rel, created = AlbumAuthor.get_or_create(album=album, author=author)
                            if created:
                                rel.save()
                    has_writer = True
                if hasattr(xml, 'Penciller'):
                    for pencillers in xml.Penciller:
                        for penciller in str(pencillers).split(", "):
                            logger.debug('Penciller: {}'.format(penciller))
                            author, created = Author.get_or_create(name=penciller, job='penciller')
                            if created:
                                author.save()
                            rel, created = AlbumAuthor.get_or_create(album=album, author=author)
                            if created:
                                rel.save()
                if hasattr(xml, 'Colorist'):
                    for colorists in xml.Colorist:
                        for colorist in str(colorists).split(", "):
                            logger.debug('Colorist: {}'.format(colorist))
                            author, created = Author.get_or_create(name=colorist, job='colorist')
                            if created:
                                author.save()
                            rel, created = AlbumAuthor.get_or_create(album=album, author=author)
                            if created:
                                rel.save()
                # validate info
                if has_writer:
                    album.validated = True
                album.save()
    except:
        logger.error("Something wrong reading ComicInfo.xml from {}".format(file))
        logger.error(traceback.format_exc())



def scrapAlbum(text):
    r = requests.get('https://www.bedetheque.com/ajax/albums?term={}'.format(text))
    list = []

    for e in r.json():
        list.append(e['value'])
    return list



@route('/missing')
def findMissingAlbums():
    series = Serie.select(Serie, fn.Count(Album.id).alias('count')).join(Album).where(Serie.complete == False).group_by(Serie).order_by(Serie.urlname)
    return template('missing', series=series)

@route('/missinginfo/<serie>')
def getMissingInfo(serie):
    serie = Serie.select(Serie, fn.Count(Album.id).alias('count')).join(Album).where(Serie.urlname == serie).get()
    albums = Album.select(Album, Serie).join(Serie).where(Serie.id == serie.id).order_by(Album.volume.cast('int'), Album.name)

    volumes = []
    for album in albums:
        volumes.append(album.volume)

    online_complete = None
    online_nb = None
    missing = []
    url = ""

    if serie.link != "":
                
        r2 = requests.get(serie.link, allow_redirects=False)
        url = re.sub(r"(.*).html$", r"\1__10000.html", r2.headers["Location"])
        r3 = requests.get(url)

        m = re.search(r"<span class=\"parution-serie\">(.*?)<\/span>", r3.text)
        if m:            
            if m.group(1) in ["Série finie", "One shot", "Série abandonnée", "Série suspendue"]:
                online_complete = True
        m = re.search(r"Tomes :<\/label>(\d+)<\/li>", r3.text)
        if m:
            online_nb = int(m.group(1))
        res = re.findall(r"<span itemprop=\"name\">\s+(.*)<span class=\"numa\">(.*?)<\/span>\s+\.\s+(.*?)\s*<\/span>", r3.text)                

        for m in res:
            num = m[1] if m[0] == "" else m[0]
            title = m[2]

            if num not in volumes:
                missing.append({"volume": num, "title": title})

    return template('missinginfo', serie=serie, albums=albums, 
        online_complete=online_complete, online_nb=online_nb,
        missing=missing, url=url)


# https://www.bedetheque.com/ajax/series?term=namibia
# [{"id":"23675","label":"Namibia (Kenya - Saison 2)","value":"Namibia (Kenya - Saison 2)","desc":"skin\/flags\/France.png"}]

# https://www.bedetheque.com/serie/index/s/23675
# 301 -> 
# https://www.bedetheque.com/serie-23675-BD-Namibia-Kenya-Saison-2.html
# https://www.bedetheque.com/serie-12-BD-Thorgal__10000.html
# <span class="parution-serie">Série finie</span>
# <li><label>Tomes :</label>5</li>
#<span itemprop="name">
# 2<span class="numa"></span>
# .         
# Épisode 2 
# </span>

# text version
def findMissing():

    series = Serie.select(Serie, fn.Count(Album.id).alias('count')).join(Album).where(Serie.complete == False).group_by(Serie).order_by(Serie.urlname)    

    for serie in series:
        print("{} - {} albums".format(serie.name, serie.count))

        albums = Album.select(Album, Serie).join(Serie).where(Serie.id == serie.id).order_by(Album.volume.cast('int'), Album.name)

        volumes = []
        for album in albums:
            volumes.append(album.volume)
            #print("#{} {}".format(album.volume, album.name))

        online_complete = None
        online_nb = None
        missing = []
        url = ""

        if serie.link != "":
                    
            r2 = requests.get(serie.link, allow_redirects=False)
            url = re.sub(r"(.*).html$", r"\1__10000.html", r2.headers["Location"])
            r3 = requests.get(url)

            m = re.search(r"<span class=\"parution-serie\">(.*?)<\/span>", r3.text)
            if m:            
                if m.group(1) in ["Série finie", "One shot", "Série abandonnée", "Série suspendue"]:
                    online_complete = True                    
            m = re.search(r"Tomes :<\/label>(\d+)<\/li>", r3.text)
            if m:
                online_nb = int(m.group(1))
            res = re.findall(r"<span itemprop=\"name\">\s+(.*)<span class=\"numa\">(.*?)<\/span>\s+\.\s+(.*?)\s*<\/span>", r3.text)                

            print("online: {} volumes {}".format(online_nb, "complete" if online_complete else ""))

            for m in res:
                num = m[1] if m[0] == "" else m[0]
                title = m[2]

                if num not in volumes:
                    missing.append({"volume": num, "title": title})
                    print("#{} {}".format(num, title))
        #input("#### enter to continue ####")
        print()
        time.sleep(2)

if len(sys.argv) > 1 and sys.argv[1] == '--scan':
    print("Library scan")
    scanLibrary()
    sys.exit(0)
elif len(sys.argv) > 1 and sys.argv[1] == '--convert':
    import signal
    stop = False
    def handler(signum, frame):
        global stop
        stop = True
    signal.signal(signal.SIGINT, handler)
    print("Convert PDF to CBZ")
    pdflist = Album.select().where(Album.filetype == 'pdf')
    for album in pdflist:
        print("Convert {} - {}".format(album.serie.name, album.name))
        convert_thread(album.serie.urlname, album.urlname)
        if stop:
            print( "stopping")
            break
    sys.exit(0)
elif len(sys.argv) > 1 and sys.argv[1] == '--todo':
    for album in Album.select().where(Album.validated==False).order_by(Album.serie, Album.name):
        print("{} - {} ({})".format(album.serie.name, album.name, album.filename))
    sys.exit(0)  
elif len(sys.argv) > 1 and sys.argv[1] == '--missing':
    findMissing()
elif len(sys.argv) > 1 and sys.argv[1] == '--validateserie':
    series = Serie.select(Serie).where(Serie.link == '').order_by(Serie.urlname)
    for serie in series:
        print(f"\n{serie.name}")        
        r = requests.get(f"https://www.bedetheque.com/ajax/series?term={serie.name}")
        c = 0
        for entry in r.json():
            print(f"{c} - id: {entry['id']} label: {entry['label']}")
            c += 1
        print("- - - - - - - - - - - - - - -")
        print("o - enter other bedetheque id")
        print("n - next entry")        
        id = ""
        name = ""
        valid = False
        while valid == False:
            i = input("Select Serie: ")
            if i != "o" and i != "n":
                try:
                    i = int(i)
                except:
                    pass
                else:
                    if i >= 0 and i < c:
                        valid = True
                        id = r.json()[i]["id"]
                        name = r.json()[i]["label"]
            else:
                valid = True
        if i == "o":            
            valid = False
            while valid == False:
                i = input ("Bedetheque serie id: ")
                try:
                    i = int(i)
                except:
                    pass
                else:
                    if i > 0:
                        valid = True
                        id = str(i)
                        name = input("Serie's name: ")

        if i != "n":
            serie.link = f"https://www.bedetheque.com/serie/index/s/{id}"
            serie.name = name
            serie.urlname = createUrl(name)
            serie.save()



        
    sys.exit(0)



convert_lock = Lock()
scan_lock = Lock()

logger.info("Starting BDReader service")

run(host=HOST, port=PORT, reloader=True)
