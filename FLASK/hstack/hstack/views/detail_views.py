# detail_views.py
#
# 특정 영상의 상세 메타데이터를 확인하는 router
#
#
# [routes]
# - detailFile(pk)
#   : '/detail/<int:pk>', methods=['GET']
#   : id = pk인 영상의 메타데이터들을 DB에서 얻어 출력.
#
# - data(filepath)
#   : '/detail/data/<path:filepath>'
#   : 비디오, 이미지, Script 등 파일 전송.
#   : filepath 경로에 있는 파일을 파일 시스템에서 찾아 전달.
#
# - download(path, title)
#   : '/detail/download/<string:path>/<string:title>'
#   : ppt 파일 다운로드
#   : path 경로에 있는 파일을 title 이름으로 다운로드합니다.
#
# - logDetailInfo(pk, type, content)
#   : '/detail/<int:pk>/<string:type>/<string:content>'
#   : logs/{{pk}}.txt 파일에 type, content에 대한 로그를 기록합니다.
#   : 상세페이지 open, close, Script 내부 검색어를 기록합니다.



from flask import request
from flask import Blueprint
from flask import send_file
from flask import render_template
from flask import send_from_directory
from flask import current_app as app # app.config 사용을 위함

from hstack.config import DB, OS
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
    if OS == "Windows":
        return send_from_directory('../media', filepath.split('media\\')[1].replace("\\", '/'))
    else :
        return send_from_directory('../media', filepath.split('media/')[1])

@bp.route('/detail/download/<string:extension>/<string:path>/<string:title>')
def download(extension, path, title):
    filepath = os.path.join('..', app.config.get('UPLOAD_FILE_DIR'), path, title+'.'+extension)
    return send_file(filepath)

@bp.route('/detail/<int:pk>', methods=['GET'])
def detailFile(pk):
    videoPath = DB.session.query(Videopath).filter(Videopath.id == pk).first().videoAddr 
    textPath = DB.session.query(Videopath).filter(Videopath.id == pk).first().textAddr

    try:
        with open(textPath, 'r', encoding='UTF-8-sig') as f:
            scripts = f.readlines()
    except FileNotFoundError as err:
        print("Error: "+err)
        scripts = []

    keywordQ = and_(Keyword.id == pk, Keyword.expose == True)

    # 이미지 받아오기
    pptImage = makePPT.getPPTImage(videoPath)

    # PPT 파일 생성
    # TODO : use video title for make ppt/pdf
    # title = DB.session.query(Videopath).filter(Videopath.id == pk).first().title
    title = 'extracted'
    makePPT.getPPTFile(videoPath, title)

    # PPT 파일 바탕으로 PDF 파일 생성
    makePPT.makePDFFile(videoPath, title)

    # PPT 파일을 얻기 위한 폴더명 얻기
    if OS == "Windows":
        pptPath = os.path.dirname(videoPath.split('Uploaded\\')[1])
    else :
        pptPath = os.path.dirname(videoPath.split('Uploaded')[1])

    return render_template('detail.html',
        pk = pk,
        videoaddr = videoPath,
        scripts = scripts,
        images = pptImage,
        pptPath = pptPath,
        #sKeyword = ScriptSearch.query.filter(ScriptSearch.sKeyword == words),
        keywords = DB.session.query(Keyword).filter(keywordQ).all(),
        metadatas = DB.session.query(Metadatum).filter(Metadatum.id == pk).all(),
        timestamps =  DB.session.query(Timestamp).filter(Timestamp.id == pk).all(),
    )

@bp.route('/detail/<int:pk>/<string:type>/<string:content>')
def logDetailInfo(pk, type, content):
    logPath = os.path.join(app.config.get('UPLOAD_LOG_DIR'), str(pk)+".txt")
    logFile = open(logPath, 'a', encoding='utf-8-sig')

    date = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    if (type == "search"): data = date + " " + content
    else:                  data = date + " *" + content
    
    logFile.write(data+'\n')
    logFile.close()