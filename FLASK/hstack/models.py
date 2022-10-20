# coding: utf-8
from flask_sqlalchemy import SQLAlchemy


db = SQLAlchemy()



class KeywordSearch(db.Model):
    __tablename__ = 'keyword_search'

    kKeyword = db.Column(db.String(50), primary_key=True)
    cnt = db.Column(db.Integer)



class Keyword(db.Model):
    __tablename__ = 'keywords'

    id = db.Column(db.ForeignKey('videopath.id'), primary_key=True, nullable=False)
    keyword = db.Column(db.String(10), primary_key=True, nullable=False)
    expose = db.Column(db.Integer)
    sysdef = db.Column(db.Integer)
    percent = db.Column(db.Float)

    videopath = db.relationship('Videopath', primaryjoin='Keyword.id == Videopath.id', backref='keywords')



class PresenterSearch(db.Model):
    __tablename__ = 'presenter_search'

    pKeyword = db.Column(db.String(50), primary_key=True)
    cnt = db.Column(db.Integer)



class Searchsatisfy(db.Model):
    __tablename__ = 'searchsatisfy'

    val = db.Column(db.Integer, primary_key=True)
    cnt = db.Column(db.Integer)



class Timestamp(db.Model):
    __tablename__ = 'timestamp'

    id = db.Column(db.ForeignKey('videopath.id'), primary_key=True, nullable=False)
    time = db.Column(db.String(10), primary_key=True, nullable=False)
    subtitle = db.Column(db.String(100))
    expose = db.Column(db.Integer)
    sysdef = db.Column(db.Integer)

    videopath = db.relationship('Videopath', primaryjoin='Timestamp.id == Videopath.id', backref='timestamps')



class TitleSearch(db.Model):
    __tablename__ = 'title_search'

    tiKeyword = db.Column(db.String(50), primary_key=True)
    cnt = db.Column(db.Integer)



class TotalSearch(db.Model):
    __tablename__ = 'total_search'

    tKeyword = db.Column(db.String(50), primary_key=True)
    cnt = db.Column(db.Integer)



class Videopath(db.Model):
    __tablename__ = 'videopath'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(50))
    videoAddr = db.Column(db.String(200))
    audioAddr = db.Column(db.String(200))
    textAddr = db.Column(db.String(200))
    imageAddr = db.Column(db.String(200))
    extracted = db.Column(db.Integer)
    password = db.Column(db.String(10))


class Metadatum(Videopath):
    __tablename__ = 'metadata'

    id = db.Column(db.ForeignKey('videopath.id'), primary_key=True)
    title = db.Column(db.String(50))
    presenter = db.Column(db.String(50))
    category = db.Column(db.String(20))
    narrative = db.Column(db.String(30))
    presentation = db.Column(db.String(10))
    videoLength = db.Column(db.String(10))
    videoFrame = db.Column(db.String(10))
    videoType = db.Column(db.String(5))
    videoSize = db.Column(db.String(10))
    uploadDate = db.Column(db.Date)
    category_percent = db.Column(db.String(30))
    voiceManRate = db.Column(db.Float)
    voiceWomanRate = db.Column(db.Float)


class UploadTime(Videopath):
    __tablename__ = 'upload_time'

    id = db.Column(db.ForeignKey('videopath.id'), primary_key=True)
    time = db.Column(db.Float)
    size = db.Column(db.Float)
