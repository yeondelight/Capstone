from flask import url_for
from flask import request
from flask import redirect
from flask import Blueprint
from flask import render_template
from flask import current_app as app # app.config 사용을 위함

from hstack import searchAll
from hstack.config import DB
from hstack.models import Videopath
from hstack.models import Metadatum

import os
import requests
import background

from werkzeug.utils import secure_filename
from sqlalchemy import and_

# 상수 설정
bp = Blueprint('main', __name__, url_prefix='/')


# send to uploadAPI
@background.task
def send2API(title, presenter, password, uploadURL):
    # API로 request
    reqUrl = 'http://127.0.0.1:8000/upload'
    data = {
        'title' : title,
        'presenter' : presenter,
        'uploadURL' : uploadURL,
        'password' : password,
        'canSearch' : True
    }
    res = requests.post(reqUrl, data=data)
    res.apparent_encoding
    print(res.encoding)
    print(res.text)
    print("password for Editing : " + password)
    


@bp.route('/')
def home():
    return render_template('home.html')

@bp.route('/uploadFile/', methods=['GET', 'POST'])
def uploadFile():
    if request.method == "POST":
        existError = {}
        fileTitle = request.form.get("title")
        filePresenter = request.form.get("presenter")
        password = request.form.get("password")
        uploadedFile = request.files["videoFile"]

        if (fileTitle == ""):
            existError['nameError'] = "영상 제목을 입력해주세요."
        if (filePresenter == ""):
            existError['presenterError'] = "영상 소유자를 입력해주세요."
        if (password == ""):
            existError['passwordError'] = "파일 수정을 위한 비밀번호를 입력해주세요."
        if (secure_filename(uploadedFile.filename) == ""):
            existError['fileError'] = "영상 파일을 첨부해주세요."

        if existError:
            return render_template('upload.html', error=existError)

        # save Video
        
        # if filename Duplicates
        uploadName = secure_filename(uploadedFile.filename)
        fileDirPath = os.path.join(app.config.get('UPLOAD_FILE_DIR'), uploadName.split('.')[0])
        dupNum = 1
        while os.path.exists(fileDirPath):
            splitedName = uploadName.split('.')
            uploadName = splitedName[0] + str(dupNum) + '.' + splitedName[1]
            dupNum += 1
            fileDirPath = os.path.join(app.config.get('UPLOAD_FILE_DIR'), uploadName.split('.')[0])

        os.makedirs(fileDirPath, 777, True)
        os.chmod(fileDirPath, 0o777)
        uploadURL = os.path.join(fileDirPath, uploadName)
        uploadedFile.save(uploadURL)

        # API로 request
        send2API(fileTitle, filePresenter, password, uploadURL)
        
        return redirect(url_for('main.home'))
                        
    return render_template('upload.html', error="")

@bp.route('/uploadFile/lists', methods=['GET', 'POST'])
def uploadList():
    if request.method == "GET":
        videoPathList = Videopath.query.filter(Videopath.extracted == True).all()
        videoIdList = list()
        for videopath in videoPathList:
            videoIdList.append(videopath.id)
        
        videoMetaList = list()
        for i in videoIdList: # (resultVideoIDList)에 저장되어 있는 id로 메타데이터 가져옴
            videoMetaList.append(searchAll.Total().getVideoMetadataFromID(i))

        if not videoIdList :
            return render_template('uploadLists.html', code = 404)
        else :
            return render_template('uploadLists.html',
                code = 200,
                categoryList = searchAll.extractCategories(videoIdList),
                typeList = searchAll.extractType(videoIdList),
                dataList = searchAll.extractData(videoIdList),
                videoMetaList = videoMetaList,
                videoIdList = videoIdList,
                category = "",
                narrative = "",
                method = ""
            )
    else:
        # 이하 detailSearch
        # 수정을 요하는 videoIdList 받기
        videoPathList = Videopath.query.filter(Videopath.extracted == True).all()
        videoIdList = list()
        for videopath in videoPathList:
            videoIdList.append(videopath.id)

        # filter 요소 받기
        category = request.form.get('category')
        narrative = request.form.get('narrative')
        method = request.form.get('method')

        excpIdList = set()
        newVideoIdList = list()
        newVideoMetaList = list()
        
        # filter를 통해 빼는 것들의 index 받기
        for id in videoIdList:
            if category != "":
                if DB.session.query(Metadatum).filter(and_(Metadatum.id == id, Metadatum.category.contains(category))).first() == None:
                    excpIdList.add(id)
            if narrative != "":
                if DB.session.query(Metadatum).filter(and_(Metadatum.id == id, Metadatum.narrative.contains(narrative))).first() == None:
                    excpIdList.add(id)
            if method != "":
                if DB.session.query(Metadatum).filter(and_(Metadatum.id == id, Metadatum.method.contains(method))).first() == None:
                    excpIdList.add(id)

        # id 제거
        for i in range(0, len(videoIdList)):
            if videoIdList[i] not in excpIdList:
                newVideoIdList.append(videoIdList[i])
                newVideoMetaList.append(searchAll.Total().getVideoMetadataFromID(videoIdList[i]))

        print(newVideoMetaList)

        if not newVideoIdList :
            return render_template('uploadLists.html', code = 404)
        else :
            return render_template('uploadLists.html',
                code = 200,
                categoryList = searchAll.extractCategories(newVideoIdList),
                typeList = searchAll.extractType(newVideoIdList),
                dataList = searchAll.extractData(newVideoIdList),
                videoMetaList = newVideoMetaList,
                videoIdList = newVideoIdList,
                category = category,
                narrative = narrative,
                method = method
            )