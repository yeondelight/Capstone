import datetime
import json
from flask import request
from flask import Blueprint
from flask import send_file
from flask import render_template
from flask import send_from_directory
from flask import current_app as app  # app.config 사용을 위함

from hstack.config import DB
from hstack.models import Videopath
from hstack.models import Metadatum
from hstack.models import Keyword
from hstack.models import Timestamp
from sqlalchemy import and_

from hstack import makePPT

import os
import json
import datetime

bp = Blueprint('detail', __name__, url_prefix='/')


@bp.route('/detail/data/<path:filepath>')
def data(filepath):
    print(filepath)
    return send_from_directory('../media', filepath.split('media\\')[1].replace("\\", '/'))


@bp.route('/detail/download/<string:path>/<string:title>')
def download(path, title):
    filepath = os.path.join(app.config.get(
        'UPLOAD_FILE_DIR'), path, title+".pptx")
    print(filepath)
    return send_file(filepath)


@bp.route('/detail/<int:pk>', methods=['GET'])
def detailFile(pk):
    videoPath = DB.session.query(Videopath).filter(
        Videopath.id == pk).first().videoAddr
    textPath = DB.session.query(Videopath).filter(
        Videopath.id == pk).first().textAddr

    try:
        with open(textPath, 'r', encoding='UTF-8-sig') as f:
            scripts = f.readlines()
    except FileNotFoundError as err:
        print(err)
        scripts = []

    print("############################")
    print(textPath)

    keywordQ = and_(Keyword.id == pk, Keyword.expose == True)

    # 이미지 받아오기
    # pptImage = makePPT.getPPTImage(videoPath)

    # PPT 파일 생성
    title = DB.session.query(Videopath).filter(
        Videopath.id == pk).first().title
    # makePPT.getPPTFile(videoPath, title)

    # PPT 파일을 얻기 위한 폴더명 얻기
    pptPath = os.path.dirname(videoPath.split('Uploaded\\')[1])
    print("@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@")
    print(pptPath)

    return render_template('detail.html',
                           pk=pk,
                           videoaddr=videoPath,
                           scripts=scripts,
                           images=pptImage,
                           pptPath=pptPath,
                           #sKeyword = ScriptSearch.query.filter(ScriptSearch.sKeyword == words),
                           keywords=DB.session.query(
                               Keyword).filter(keywordQ).all(),
                           metadatas=DB.session.query(Metadatum).filter(
                               Metadatum.id == pk).all(),
                           timestamps=DB.session.query(Timestamp).filter(
                               Timestamp.id == pk).all(),
                           )

# pk logfile에 content 기록


def writeLog(pk, type, content):
    logPath = os.path.join(app.config.get('UPLOAD_LOG_DIR'), str(pk)+".txt")
    logFile = open(logPath, 'a')

    date = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    if (type == "search"):
        data = date + " " + content
    else:
        data = date + " *" + content

    print(logPath, data)

    logFile.write(data)
    logFile.close()


@bp.route('/detail/<int:pk>/<string:type>/<string:content>')
def logDetailInfo(pk, type, content):
    logPath = os.path.join(app.config.get('UPLOAD_LOG_DIR'), str(pk)+".txt")
    logFile = open(logPath, 'a', encoding='utf-8-sig')

    date = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    if (type == "search"):
        data = date + " " + content
    else:
        data = date + " *" + content

    logFile.write(data+'\n')
    logFile.close()
