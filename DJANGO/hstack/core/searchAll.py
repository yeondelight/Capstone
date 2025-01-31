# 2022.04.28
# search(searchTexts)로 실행 -> list로 메타데이터 가져옴

from imghdr import what
from operator import index
import os
import platform
from re import I
from unicodedata import category

from importlib_metadata import metadata

from . import models
from unicodedata import category
from django.db.models import Q


# 상수 설정
OS = platform.system()

class Total:

    resultVideoIDList = set()
    finalDict = {}
    rankcount = {} # 정확도 합 카운트
    rankDict = {} #rank 딕셔너리
    rankDetail = [] #정확도 detail 텍스트
    detail = {}


    def searchWordFromDB(self,searchTexts):
        #resultVideoIDList = set()
        for searchText in searchTexts:
            # 쿼리셋.values('필드이름') : 해당 필드와 값들을 딕셔너리로 제공 ex : [{'id': 1234}, {'id': 5678}, {'id': 1212}]
            # 쿼리셋.values_list('필드이름') : 해당 필드의 값들을 튜플로 제공
            # 쿼리셋.values_list('필드이름', flat=True) : 해당 필드의 값들을 리스트로 제공

            # [1234, 5678, 1212] << 이런 식으로 나올 것이라 예상
            for k in models.Keywords.objects.filter(keyword__contains = searchText).exclude(expose = 0).values_list('id', flat=True):
                self.resultVideoIDList.add(k)    # id를 resultVideoIDList 집합에 저장
            for ti in models.Metadata.objects.filter(title__contains = searchText).values_list('id', flat=True).distinct():
                self.resultVideoIDList.add(ti)
            for p in models.Metadata.objects.filter(presenter__contains = searchText).values_list('id', flat=True).distinct():
                self.resultVideoIDList.add(p)
            for to in models.Timestamp.objects.filter(subtitle__contains = searchText).values_list('id', flat=True):
               self.resultVideoIDList.add(to)

     #키워드와 인덱스 확률 계산
    def getPercent(self, videoId, div, cnt):
        if (cnt == 0) :
            return 0
        if(div == "key"):
            keyTotal = models.Keywords.objects.filter(id = videoId).filter(expose=1).all()
            count1 = keyTotal.count()
            percent = ((cnt/5)/count1)*100 #점수를 주었기 때문에 5로 다시 나누어 줌
            return round(percent,1) # 소수점 한자리
        if(div == "subtitle"):
            subtitleTotal = models.Timestamp.objects.filter(id = videoId).all()
            count2 = subtitleTotal.count()
            percent = ((cnt/5)/count2)*100 #점수를 주었기 때문에 5로 다시 나누어 줌
            return round(percent,1) # 소수점 한자리
        if(div == "title"):
            return 100 
        if(div == "present"):
            return 100 
    
    def getPercentDic(self, searchTexts, videoId):
         percentDic = {"keyword":0,"title":0,"present":0,"index":0}
         for searchText in searchTexts:
            print(searchText)

            #
            for keyW in models.Keywords.objects.filter(id = videoId, expose = 1).filter(keyword__contains = searchText).values_list('keyword', flat=True):
                if(searchText in keyW):
                    self.rankcount["keyword"] += 5
                else:
                    self.rankcount["keyword"] += 0
                
            cnt = self.rankcount["keyword"]
            percentDic['keyword'] = self.getPercent(videoId, "key", cnt)
            #
            if models.Metadata.objects.filter(id = videoId).filter(title__contains = searchText).exists():
                self.rankcount["title"] = 50
                percentDic['title'] = self.getPercent(videoId, "title", 100)
                #self.rankDetail.append("100")
            else:
                percentDic['title'] = 0
                #self.rankDetail.append("0")
            #
            if models.Metadata.objects.filter(id = videoId).filter(presenter__contains = searchText).exists():
                self.rankcount["present"] = 50
                percentDic['present'] = self.getPercent(videoId, "present", 100)
                #self.rankDetail.append("100")
            else:
                percentDic['present'] = 0
                #self.rankDetail.append("0")
            #
            for subT in models.Timestamp.objects.filter(id = videoId).filter(subtitle__contains = searchText).values_list('subtitle', flat=True):
                if(searchText in subT):
                    self.rankcount["subtitle"] += 5
                else:
                    self.rankcount["subtitle"] += 0
                
            cnt = self.rankcount["subtitle"]
            percentDic['index'] = self.getPercent(videoId, "subtitle", cnt)


            print("((((((((((((((((((((((((((((((((())))))))))))))))))))))))))))))")
            print(percentDic)
            return percentDic

    def getWeight(self, percentDic, count):
        total = 0
        if count == 1:
            total = percentDic['title'] + percentDic['present'] + percentDic['keyword']

        elif count == 2: # 주어진 세부사항이 2가지인 경우
            if percentDic['keyword']==0:    
                total = (percentDic['title'] + percentDic['present']) * 0.5
            elif percentDic['title'] == 0:
                if percentDic['present'] != 0:  # keyword와 presenter가 나온 경우
                    total = (percentDic['present']* 0.6 + percentDic['keyword']* 0.4)
                else:   # keyword만 나온 경우 (keyword가 50% 이상/이하 경우 나눔)
                    if percentDic['keyword']<50:
                        total = percentDic['keyword']* 0.9
                    else:
                        total = percentDic['keyword']
            else:   # title과 keyword만 나온 경우
                total = (percentDic['title']* 0.6 + percentDic['keyword']* 0.4)

        elif count == 3:    # 주어진 세부사항이 3가지인 경우
            if percentDic['title']==0: # keyword만/ presenter만/ keyword와 presenter만 나온 경우
                if percentDic['present']==0:    # keyword만 값이 나온 경우
                    total = (percentDic['keyword']*0.6)
                elif percentDic['keyword']==0:    # presenter만 값이 나온 경우
                    total = (percentDic['present']*0.6)
                else:    # keyword와 presenter만 값이 나온 경우
                    total = (percentDic['present']*0.5) + (percentDic['keyword']*0.25)
            elif percentDic['present']==0: # title만/ keyword와 title만 나온 경우
                if percentDic['keyword']==0:    # title만 값이 나온 경우
                    total = (percentDic['title']*0.6)
                else:   # keyword와 title만 값이 나온 경우
                    total = (percentDic['title']*0.5) + (percentDic['keyword']*0.25)
            elif percentDic['keyword']==0:
                total = (percentDic['title']*0.37) + (percentDic['present']*0.37)

            else:
                total = (percentDic['title']*0.4) + (percentDic['present']*0.4) + (percentDic['keyword']*0.2)

        return round(total, 2)

     # 입력 값 일치율대로 점수 부여 & 디테일 리스트 추가
    def getrank(self, videoId, All, T, K, P): #ranking algo
        self.rankcount = {"keyword":0,"title":0,"present":0,"subtitle":0} #rank 알고리즘 초기화
        percentDic = {"keyword":0,"title":0,"present":0}
        midResultDic = {"keyword":0,"title":0,"present":0, "index":0}

        percSum = 0

        searchTexts = []
        if All != None:  # 전체 검색을 한 경우
            for i in All: # searchTexts는 All만
                searchTexts.append(i)
                percentDicRes = self.getPercentDic(searchTexts, videoId)
                print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
                print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
                print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
                print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
                print(percentDicRes)
                t = percentDicRes['title']
                p = percentDicRes['present']
                k = percentDicRes['keyword']
                i = percentDicRes['index']
                k_i = 0

                if k >=50 or i >=50:
                    k_i = (k+i)/4 + 50
                else:
                    k_i = (k+i)/2

                if t==100 and p==100:                                       ###########################################################
                    percSum += 95 + k_i*0.05
                elif t==100 or p==100 :
                    percSum += 90 + k_i*0.05
                else :
                    percSum += k_i

                # 중간결산
                midResultDic['keyword'] += percentDicRes['keyword']
                midResultDic['index'] += percentDicRes['index']
                midResultDic['title'] += percentDicRes['title']
                midResultDic['present'] += percentDicRes['present']


            print(percentDicRes)
            print(midResultDic)

            # 최종 결산
            if (midResultDic['title'] > 100) :      midResultDic['title'] = 100     # title
            if (midResultDic['present'] > 100) :    midResultDic['present'] = 100   # presenter
            # midResultDic['index'] = midResultDic['index'] / len(searchTexts)        # index
            # midResultDic['keyword'] = midResultDic['keyword'] / len(searchTexts)    # keyword

            keywordPerc = 0
            indexPerc = 0
            indexPerc = midResultDic['index'] / len(searchTexts)        # index
            keywordPerc = midResultDic['keyword'] / len(searchTexts)    # keyword

            # keyword + index merge
            if keywordPerc > indexPerc:
                alpha = (100 - keywordPerc)/100.0
                indexPerc = alpha * indexPerc
            else :
                alpha = (100 - indexPerc)/100.0
                keywordPerc = alpha * keywordPerc
            midResultDic['keyword'] = round(keywordPerc + indexPerc, 2)
            
            self.rankDetail.append(str(midResultDic['title']))
            self.rankDetail.append(str(midResultDic['present']))
            self.rankDetail.append(str(midResultDic['keyword']))

            # total
            #perc = str(round((midResultDic['index']+midResultDic['keyword']+midResultDic['title']+midResultDic['present'])/4 ,1))
            perc = str(round(percSum / len(searchTexts),2))
            
            self.rankDetail.append(perc)
            # 순서: title, presenter, keyword, total

            print("@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@")
            print(self.rankDetail)

            #return(sum(self.rankcount.values()), self.rankDetail)
            return(float(perc), self.rankDetail, True)

        else:
            count = 0
            if T != None:
                count += 1
                for i in T:
                    searchTexts.append(i)
                for searchText in searchTexts:
                    titleQ = Q()
                    titleQ &= Q(id = videoId)
                    titleQ &= Q(title__contains = searchText)
                    if models.Metadata.objects.filter(titleQ).exists():
                        percentDic['title'] = self.getPercent(videoId, "title", 100)

            searchTexts = []
            if P != None:
                count += 1
                for i in P:
                    searchTexts.append(i)
                for searchText in searchTexts:
                    presentQ = Q()
                    presentQ &= Q(id = videoId)
                    presentQ &= Q(presenter__contains = searchText)
                    if models.Metadata.objects.filter(presentQ).exists():
                        percentDic['present'] = self.getPercent(videoId, "present", 100)

            searchTexts = []
            if K != None:
                count += 1
                keywordPerc = 0
                indexPerc = 0
                for i in K:
                    searchTexts.append(i)
                for searchText in searchTexts:
                    self.rankcount["keyword"] = 0
                    self.rankcount["subtitle"] = 0
                    keywordQ = Q()
                    keywordQ &= Q(id = videoId)
                    keywordQ &= Q(expose = 1)
                    keywordQ &= Q(keyword__contains = searchText)
                    for keyW in models.Keywords.objects.filter(keywordQ).values_list('keyword', flat=True):
                        if(searchText in keyW):
                            self.rankcount["keyword"] += 5
                        else:
                            self.rankcount["keyword"] += 0
                        
                    cnt = self.rankcount["keyword"]
                    keywordPerc += self.getPercent(videoId, "key", cnt)
                    #
                    for subT in models.Timestamp.objects.filter(id = videoId).filter(subtitle__contains = searchText).values_list('subtitle', flat=True):
                        if(searchText in subT):
                            self.rankcount["subtitle"] += 5
                        else:
                            self.rankcount["subtitle"] += 0
                        
                    cnt = self.rankcount["subtitle"]
                    indexPerc += self.getPercent(videoId, "subtitle", cnt)

                keywordPerc = keywordPerc/len(searchTexts)
                indexPerc = indexPerc/len(searchTexts)

                if keywordPerc > indexPerc:
                    alpha = (100 - keywordPerc)/100.0
                    indexPerc = alpha * indexPerc
                else :
                    alpha = (100 - indexPerc)/100.0
                    keywordPerc = alpha * keywordPerc
                percentDic['keyword'] = round(keywordPerc + indexPerc,2)

            # else의 계산
            
            print("$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$")
            print(percentDic)

            perc = self.getWeight(percentDic, count)
            print(perc)

            if perc > 0:
                isValid = True
                
                # 순서: title, presenter, keyword, total
                self.rankDetail.append(str(percentDic['title']))
                self.rankDetail.append(str(percentDic['present']))
                self.rankDetail.append(str(percentDic['keyword']))
                self.rankDetail.append(perc)

                print("$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$")
                print(self.rankDetail)
                
                #return(sum(self.rankcount.values()), self.rankDetail)
            else:
                isValid = False
            
            return(float(perc), self.rankDetail, isValid)

    def getVideoMetadataFromID(self, videoId):
        # 아래는 단어찾은 비디오 id로 메타데이터 얻는 법
        # values_list() - 쿼리셋을 튜플로 변환 # [(5, 'post #1'), (6, 'title #1'), (7, 'title #2')]
        # values_list('title') # [('post #1',), ('title #1',), ('title #2',)]
        # values_list는 flat가능 -> 튜플이 아닌 리스트로 값 반환 그러나 값이 여러개일때는 사용X
        # values_list() - [5, 6, 7]  # values_list('title', flat=True) - ['post #1', 'title #1', 'title #2']
        print(videoId)
        self.finalDict = {} # 초기화
        keywordQ = Q()
        keywordQ &= Q(id = videoId)
        keywordQ &= Q(expose=True)
        metadataList = list(models.Metadata.objects.filter(id = videoId).all().values()) # values_list()로 하면 key없는 list형태로 반환
        keywordList = list(models.Keywords.objects.filter(keywordQ).all().values_list('keyword', flat=True).distinct()) # list형태
        #filePath = list(models.Videopath.objects.filter(id = videoId).all().values_list('videoaddr','imageaddr')) # imageaddr
        #timestamp = list(models.Timestamp.objects.filter(id = videoId).all().values())
        print("*************************************")
        print("*************************************")
        print("*************************************")
        print("*************************************")
        print("*************************************")
        print("*************************************")
        print("*************************************")
        print(metadataList)
        print(keywordList)
        self.finalDict['id'] = videoId
        self.finalDict['metadata'] = metadataList
        self.finalDict['keyword'] = keywordList
        self.finalDict['thumbnail'] = None

        if OS == 'Windows':
            filePath = "\\media" + models.Videopath.objects.get(id = videoId).imageaddr.split('media')[1]
        else :
            filePath = "/media" + models.Videopath.objects.get(id = videoId).imageaddr.split('media')[2]

        count = 0
        for file in os.listdir(models.Videopath.objects.get(id = videoId).imageaddr):
            if file.split(".")[1] == "jpg":
                count+=1
                if count > 1:
                    fileName = file
                    self.finalDict['thumbnail'] = os.path.join(filePath, fileName)
                    break

        if self.finalDict['thumbnail'] == None:
            self.finalDict['thumbnail'] = '/static/img/defThumbnail.jpg'
        
        #self.finalDict['filePath']=filePath
        #self.finalDict['timestamp']=timestamp

        return self.finalDict #해도 되고 밖에서 Total.finalDict 해도 되고 

    # 2022년 5월 16일 videoIdList를 받아와 filter search를 할 때 쓰임
    def getDetailVideoList(videoId, search_type, search_detail_type):
        finalDict = {} # 초기화
        keywordQ = Q()
        keywordQ &= Q(id = videoId)
        keywordQ &= Q(expose=True)

        if search_type == "category":
            if models.Metadata.objects.filter(id = videoId).filter(category__contains = search_detail_type).exists():
                metadataList = list(models.Metadata.objects.filter(id = videoId).all().values())
                keywordList = list(models.Keywords.objects.filter(keywordQ).all().values_list('keyword', flat=True).distinct())
                finalDict['id'] = videoId
                finalDict['metadata'] = metadataList 
                finalDict['keyword']=keywordList
                if OS == 'Windows':
                    filePath = "\\media" + models.Videopath.objects.get(id = videoId).imageaddr.split('media')[1]
                else :
                    filePath = "/media" + models.Videopath.objects.get(id = videoId).imageaddr.split('media')[1]

                fileName = os.listdir(models.Videopath.objects.get(id = videoId).imageaddr)[0]
                finalDict['thumbnail'] = os.path.join(filePath, fileName)
        elif search_type == "method":
            if models.Metadata.objects.filter(id = videoId).filter(method__contains = search_detail_type).exists():
                metadataList = list(models.Metadata.objects.filter(id = videoId).all().values())
                keywordList = list(models.Keywords.objects.filter(keywordQ).all().values_list('keyword', flat=True).distinct())
                finalDict['id'] = videoId
                finalDict['metadata'] = metadataList
                finalDict['keyword']=keywordList
                if OS == 'Windows':
                    filePath = "\\media" + models.Videopath.objects.get(id = videoId).imageaddr.split('media')[1]
                else :
                    filePath = "/media" + models.Videopath.objects.get(id = videoId).imageaddr.split('media')[2]
                    
                fileName = os.listdir(models.Videopath.objects.get(id = videoId).imageaddr)[0]
                finalDict['thumbnail'] = os.path.join(filePath, fileName)
        elif search_type == "narrative":
            if models.Metadata.objects.filter(id = videoId).filter(narrative__contains = search_detail_type).exists():
                metadataList = list(models.Metadata.objects.filter(id = videoId).all().values())
                keywordList = list(models.Keywords.objects.filter(keywordQ).all().values_list('keyword', flat=True).distinct())
                finalDict['id'] = videoId
                finalDict['metadata'] = metadataList
                finalDict['keyword']=keywordList
                if OS == 'Windows':
                    filePath = "\\media" + models.Videopath.objects.get(id = videoId).imageaddr.split('media')[1]
                else :
                    filePath = "/media" + models.Videopath.objects.get(id = videoId).imageaddr.split('media')[1]
                    
                fileName = os.listdir(models.Videopath.objects.get(id = videoId).imageaddr)[0]
                finalDict['thumbnail'] = os.path.join(filePath, fileName)

        return finalDict

from django.db.models import Max, Min, Avg
def searchTest(All, T, K, P):
    # searchTexts로 저장
    searchTexts = []
    if All != None:
        for i in All:
            searchTexts.append(i)
    else:
        if T != None:
            for i in T:
                searchTexts.append(i)
        if K != None:
            for i in K:
                searchTexts.append(i)
        if P != None:
            for i in P:
                searchTexts.append(i)

    titleSet = findAt(searchTexts, 0)
    presenterSet = findAt(searchTexts, 1)
    keywordSet = findAt(searchTexts, 2)
    categorySet = findAt(searchTexts, 3)
    
    weight = [0.3,0.3,0.2,0.2] # Title Presenter Keyword Category
    whatzero = []
    if len(titleSet) == 0:
        weight[0] = 0
        whatzero.append(0)
    if len(presenterSet) == 0:
        weight[1] = 0
        whatzero.append(1)
    if len(keywordSet) == 0:
        weight[2] = 0
        whatzero.append(2)
    if len(categorySet) == 0:
        weight[3] = 0
        whatzero.append(3)

    # weight 정리
    weight = organize_weight(weight, whatzero)
    # 검색 대상이 되는 비디오 리스트 = video (type = set)
    video = set()
    video = titleSet.union(presenterSet)
    video.update(keywordSet)
    video.update(categorySet)
    print(video)
    # id 당 T P K C 확률 구하기
    perc = {}
    for vi in video:
        print("$$$$$$$$$$$$$$$$$$")
        print(vi)
        in_perc = []
        if weight[0] != 0:  # T의 확률 구하기
            p = 0
            for searchText in searchTexts:
                if vi in titleSet:
                    p += 1
            if p > 0:
                in_perc.append(1)
            else:
                in_perc.append(0)
        else:
            in_perc.append(0)
        if weight[1] != 0: # P의 확률 구하기
            p = 0
            for searchText in searchTexts:
                if vi in presenterSet:
                    p += 1
            if p > 0:
                in_perc.append(1)
            else:
                in_perc.append(0)
        else:
            in_perc.append(0)
        if weight[2] != 0: # K의 확률 구하기
            if vi in keywordSet:
                p = 0
                for searchText in searchTexts:
                    print(searchText)
                    p += getKeywordPerc(vi,searchText)
                    print(p)
                in_perc.append(p)
            else:
                in_perc.append(0)
        else:
            in_perc.append(0)
        #if weight[3] != 0: # C의 확률 구하기
        #     if vi in keywordSet:
        #         p = 0
        #         for searchText in searchTexts:
        #             p += getCategoryPerc(vi,searchText)
        #         in_perc.append(p)
        #     else:
        #         in_perc.append(0)
        # else:
        #     in_perc.append(0)
        perc[vi] = in_perc
        print(in_perc)
        print(perc)
    print("^^^^^^^^^^^")
    print(in_perc)
    print(perc)
    # ranking 결과
    print(weight)
    ranking_res = {}
    for videoid in perc:
        print(perc[videoid])
        cnt = 0
        sum = 0
        for p in perc[videoid]:
            sum+=p*weight[cnt]
            print(p*weight[cnt])
            cnt+=1
        print("**!!")
        print(sum)
        # if sum == 0:
        #     continue
        ranking_res[videoid]=sum
    print("***************")
    print(ranking_res)
    

def getKeywordPerc(videoid, searchText):
    # keyword의 값 구해보기 예시: 77번
    # keyword는 포함이 아니라 정확히 같은 경우, 즉 1개만 나올때만 해야함
    # 이게 맞나싶지만 확률을 구하기 위해선 그래야 함
    # 누가 나 좀 살려줘
    k_v = list(models.Keywords.objects.filter(id = videoid).values_list('percent', flat=True).distinct())
    k_v2 = list(models.Keywords.objects.filter(id = videoid).filter(keyword = searchText).values_list('percent', flat=True).distinct())
    # max 값 구하고 싶다면 아래처럼 - Django에서
    # obj = models.Keywords.objects.filter(id = 77).aggregate(percent=Max('percent'))
    # print(obj)
    # print(obj['percent'])
    if max(k_v) == 0 or len(k_v2) == 0:
        return 0
    m = round(1/max(k_v),3)
    print(k_v2)
    print(k_v2[0])
    print(m)
    return round(k_v2[0]*m,3)

def organize_weight(weight, whatzero):
    n = 4 - len(whatzero)
    sum = 0
    while len(whatzero)>0:
        p = whatzero.pop()
        if p==2:
            sum += round(0.2 / n,2)
        elif p == 3:
            sum += round(0.2 / n,2)
        elif p==0:
            sum += round(0.3 / n,2)
        elif p==1:
            sum += round(0.3 / n,2)
    #print(sum)
    c = 0
    for w in weight:
        if w != 0:
            weight[c] += sum
        c+=1
    #print(weight)
    return weight                  
def findAt(searchTexts, index):
    result = set()
    for searchText in searchTexts:
        if index == 0:
            sql = list(models.Metadata.objects.filter(title__contains = searchText).values_list('id', flat=True).distinct())
        elif index == 1:
            sql = list(models.Metadata.objects.filter(presenter__contains = searchText).values_list('id', flat=True).distinct())
        elif index == 2:
            sql = list(models.Keywords.objects.filter(keyword__contains = searchText).values_list('id', flat=True).distinct())
        elif index == 3:
            sql = list(models.Metadata.objects.filter(category__contains = searchText).values_list('id', flat=True).distinct())

        for l in sql:
            result.add(l)
    print(result)
    if len(result) == 0:
        return set()
    else:
        return result

#searchTexts = ["황기", "메모리"]   
def search(All, T, K, P):
    # searchTexts로 저장
    searchTexts = []
    if All != None:
        for i in All:
            searchTexts.append(i)
    else:
        if T != None:
            for i in T:
                searchTexts.append(i)
        if K != None:
            for i in K:
                searchTexts.append(i)
        if P != None:
            for i in P:
                searchTexts.append(i)

    a = Total()
    a.resultVideoIDList = set() # 두번째를 위해 초기화
    a.searchWordFromDB(searchTexts) # 찾고자 하는 단어를 가진 메타데이터 비디오id를 (resultVideoIDList) set으로 가져옴
    print("&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&")
    print(a.resultVideoIDList)
    #resultVideoIDList
    searchResultMeta = []

    maxlist = [] # 알고리즘을 거친 후의 id 리스트
    rankDict = {} # 정확도 보내는 딕셔너리
    tttt = {}

    #ranking algorithm
    for i in list(a.resultVideoIDList): # (resultVideoIDList)에 저장되어 있는 id로 메타데이터 가져옴
        if models.Videopath.objects.get(id = i).extracted == 1 or models.Videopath.objects.get(id = i).extracted == 2:
            #print(i) #id
            # a.getrank(searchTexts,i) #해당 videoId의 정확도
            a.rankDetail = [] #초기화
            #rankDict[i], a.detail[i], isValid = a.getrank(i, All=All, T=T, K=K, P=P)
            rank, details, isValid = a.getrank(i, All=All, T=T, K=K, P=P)

            if isValid:
                rankDict[i] = rank
                a.detail[i] = details
                tttt[i] = a.detail[i]

            # perc 값이 0인 경우 유효하지 않은 값이기 때문에 제거해야한다.
            if not isValid:
                print("&&&&&&&&&&& NOT VALID &&&&&&&&&&&&&")


    # for i in rangelist(a.resultVideoIDList):
    #     print(rankDict[i]['전체스코어'])

    #value 큰 순서대로 딕셔너리 재배열
    sdict = sorted(rankDict.items(), key=lambda x: x[1], reverse=True)

    maxlist = dict(sdict) #list형태의 딕셔너리를 딕셔너리 형태로 전환
    print(maxlist.keys())
    for j in maxlist:
        a.getVideoMetadataFromID(j) #id 받아오기
        searchResultMeta.append(a.finalDict)
        searchResultMeta.append(a.detail[j])

    videoIdList = list(maxlist.keys())
    searchResultMeta = list(searchResultMeta)
    categoryList = extractCategories(videoIdList)
    typeList = extractType(videoIdList)
    dataList = extractData(videoIdList)

    return (videoIdList, searchResultMeta, categoryList, typeList, dataList, tttt)


# 2022년 5월 16일 videoIdList를 받아와 filter search를 할 때 쓰임
def detailSearch(videoIdList, search_type, search_detail_type, All, T, K, P):
    searchResultMeta = []
    newVideoIdList = list()

    # searchTexts로 저장
    searchTexts = []
    if All != None:
        for i in All:
            searchTexts.append(i)
    else:
        if T != None:
            for i in T:
                searchTexts.append(i)
        if K != None:
            for i in K:
                searchTexts.append(i)
        if P != None:
            for i in P:
                searchTexts.append(i)
    
    for i in videoIdList:
        if models.Videopath.objects.get(id = i).extracted == 1 or models.Videopath.objects.get(id = i).extracted == 2:
            res = Total.getDetailVideoList(i, search_type, search_detail_type)
            if len(res) != 0:
                #searchResultMeta.append(res)
                newVideoIdList.append(i)

            ##
    maxlist = [] # 알고리즘을 거친 후의 id 리스트
    rankDict = {} # 정확도 보내는 딕셔너리
    tttt = {}
    a = Total()
    #ranking algorithm
    for i in list(newVideoIdList): # (resultVideoIDList)에 저장되어 있는 id로 메타데이터 가져옴
        if models.Videopath.objects.get(id = i).extracted == 1 or models.Videopath.objects.get(id = i).extracted == 2:
            #print(i) #id
            # a.getrank(searchTexts,i) #해당 videoId의 정확도
            a.rankDetail = [] #초기화
            rank, details, isValid = a.getrank(i, All=All, T=T, K=K, P=P)

            if isValid:
                rankDict[i] = rank
                a.detail[i] = details
                tttt[i] = a.detail[i]

            # perc 값이 0인 경우 유효하지 않은 값이기 때문에 제거해야한다.
            if not isValid:
                print("&&&&&&&&&&& NOT VALID &&&&&&&&&&&&&")


    # for i in rangelist(a.resultVideoIDList):
    #     print(rankDict[i]['전체스코어'])

    #value 큰 순서대로 딕셔너리 재배열
    sdict = sorted(rankDict.items(), key=lambda x: x[1], reverse=True)

    maxlist = dict(sdict) #list형태의 딕셔너리를 딕셔너리 형태로 전환
    print(maxlist.keys())
    for j in maxlist:
        a.getVideoMetadataFromID(j) #id 받아오기
        searchResultMeta.append(a.finalDict)
        searchResultMeta.append(a.detail[j])

    videoIdList = list(maxlist.keys())
    searchResultMeta = list(searchResultMeta)
    print(videoIdList)
    ##
    
    categoryList = extractCategories(videoIdList)
    typeList = extractType(videoIdList)
    dataList = extractData(videoIdList)

    return (videoIdList, searchResultMeta, categoryList, typeList, dataList, tttt)


# 각 videoId에서 narrative를 뽑아낸다.
def extractType(videoIdList):
    typeList = set()
    for videoId in videoIdList:
        if(models.Metadata.objects.get(id = videoId).narrative):
            types = models.Metadata.objects.get(id = videoId).narrative
            types = types.split(',')
            print(types)
            for c in types:
                typeList.add(c)

    return typeList

# 각 videoId에서 Categories를 뽑아낸다.
def extractCategories(videoIdList):
    categoryList = set()
    for videoId in videoIdList:
        if(models.Metadata.objects.get(id = videoId).category):
            category = models.Metadata.objects.get(id = videoId).category
            category = category.split(',')
            print(category)
            for c in category:
                categoryList.add(c)

    return categoryList

# 각 videoId에서 method를 뽑아낸다.
def extractData(videoIdList):
    dataList = set()
    for videoId in videoIdList:
        if(models.Metadata.objects.get(id = videoId).method):
            datas = models.Metadata.objects.get(id = videoId).method
            datas = datas.split(',')
            print(datas)
            for c in datas:
                dataList.add(c)

    return dataList    