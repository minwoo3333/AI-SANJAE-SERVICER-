from pymongo import MongoClient
# from openai import OpenAI
from dotenv import load_dotenv
import os
from model import preprocess, modelstart
import random
import math

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))

# OpenAI API 키 설정
api_key = os.environ["API_KEY"]

mogodbURL = f"mongodb+srv://{os.environ['MONGODB_KEY']}@cluster0.siectcp.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
# MomgoDB 연결
client = MongoClient(mogodbURL)
database = client["project2"]
collection = database["CaseLaw"]
collections = database["Nomusa"]
collectionl = database["rawdata"]

# 데이터에서 검색 조건에 맞는 결과 찾기
def search_caselaw(kinda, kindb, content):
    # 쿼리 조건을 담을 딕셔너리
    query = {}

    # result 값이 있으면 쿼리에 추가
    if kinda != '전체':
        query["kinda"] = kinda

    # classification 값이 있으면 쿼리에 추가
    if kindb != "전체":
        query["kindb"] = kindb

    # text 값이 있으면 content 필드를 부분 일치 검색 쿼리에 추가
    if content != '':
        query["content"] = {"$regex": content, "$options": "i"}

    try:
        # MongoDB에서 검색
        cursor = collection.find(query)
        
        # 검색 결과 처리
        results = []
        for doc in cursor:
        # MongoDB 문서에서 _id 필드 제외하기
            doc.pop('_id', None)
            results.append(doc)

        return results
    
    except Exception as e:
        print(f"Error occurred: {e}")
        return None
    
# 데이터에서 정보 찾기
def findcaselaw(accnum):
    data = collection.find_one({"accnum": accnum})
    if data:
        data["_id"] = str(data["_id"])
    return data

# model에서 결과 받기
def findanswer(text, select):
    if ("JAVA_HOME" in os.environ) == False:
        os.environ["JAVA_HOME"] = r"C:\Program Files\Java\jdk-22\bin\server"
        print("JAVA_HOME" in os.environ)
    Cleantext = preprocess(text)
    result = modelstart(Cleantext, select)
    print(len(result))
    print(result[0])
    print()
    print(result[1])
    print()
    print(result[2])
    print()
    print(result[3])
    print()
    print(result[4])

    link = collectionl.find_one({"index": int(result[0]["kinda"][0])})
    if result[0]["similarity"] > 0.5:
        if result[0]["kinda"][1] == "기각":
            return [f"'산재 불가능' 확률이 높습니다.", link["accnum"]]
        else:
            return [f"'산재 가능' 확률이 높습니다.", link['accnum']]
    elif (result[0]["similarity"] > 0.3):
        return f"진단시 받았던 병명/상황을 좀 더 상세하게 작성해 주세요."
    elif (result[0]["similarity"] <= 0.3):
        return f"판단할 수 없습니다."

# _id 제거
def idremove(doc):
    doc.pop('_id', None)
    return doc

# MongoDB에서 노무사 정보 찾기
def findNomusa():
    Nomusa = collections.find({})
    randomdata = list(Nomusa)
    idremovedata =  random.sample(randomdata, k=5)
    randomdatapost = [idremove(doc) for doc in idremovedata]

    return randomdatapost

# 금액 계산하기
def calculatorprice(text, select):
    if select == "휴업":
        price = int(text) / 30
        pay = price * 0.7

        if pay < 76960:
            pay = 76960
        elif pay > 172225:
            pay = 172225

        # math: 마지막 자리 올림처리
        result = math.ceil(pay / 10) * 10
        return f"휴업급여(일): {result:,}원"
    
    elif select == "장해":
        # 장해 등급에 따른 장해보상 연금 (일분)
        annual_list = {616:138, 737:164, 869:193, 1012:224, 1155:257, 1309:291, 1474:329}
        # 장해 등급에 따른 장해보상일시금 (일분)
        reward = {'1':1474, '2':1309, '3':1155, '4':1012, '5':869, '6':737, '7':616, '8':495, '9':385, '10':297, '11':220, '12':154, '13':99, '14':55}
        price = int(text.split(",")[0]) / 30
        lank = text.split(",")[1].strip()
        money = price * reward[lank] * 0.95
        money = math.ceil(money / 10) * 10

        if reward[lank] > 800:
            annual_day = annual_list[reward[lank]]
            annual_pay = price * annual_day / 12
            together_annual = math.ceil(annual_pay / 2 / 10) * 10
            together_pay = math.ceil(together_annual * 12 * 0.95 / 10) * 10
            annual_pay = math.ceil(annual_pay / 10) * 10
            return f'1. 장해보상일시금만 수령 : {money:,}원 \n2. 장해보상연금만 수령 : {annual_pay:,}원\n3. 연금과 일시금 같이 수령\n- 1년까지 연금: {together_annual:,}원\n- 1년 선지급 일시금: {together_pay:,}원 \n- 1년 이후부터 연금: {annual_pay:,}원'
        else:
            return f'장해보상일시금 : {money:,}원'

    elif select == "유족":
        price = int(text.split(",")[0]) / 30
        num_survior = int(text.split(",")[1].strip())

        if num_survior == 0:
            money = price * 1300
            return f"유복보상일시금: {money:,}원"
        else:
            basic_annual_pay = price * 365
            money = (basic_annual_pay * 0.47 + (basic_annual_pay * 0.05 * num_survior)) / 12
            money = math.ceil(money / 10) * 10
            return f"유족보상연금(1년에 달마다 받는 금액) : {money:,}원"
    
