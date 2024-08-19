import pandas as pd
from konlpy.tag import Okt
from sentence_transformers import SentenceTransformer, util
from pymongo import MongoClient
import os
from dotenv import load_dotenv


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))
mogodbURL = f"mongodb+srv://{os.environ['MONGODB_KEY']}@cluster0.siectcp.mongodb.net/"
# mogodbURL = f"mongodb+srv://{os.environ['MONGODB_KEY']}@cluster0.siectcp.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
# MomgoDB 연결
client = MongoClient(mogodbURL)
database = client["project2"]
collection = database["embedding"]

# 확장된 불용어 리스트
stopwords = [
    '이', '그', '저', '것', '수', '들', '등', '및', '에서', '이다', '것이다', '그것', '이것', '저것', '안', '앞', '위', '뒤',
    '어디', '때문', '인해', '그리고', '그러나', '그래서', '또', '한', '다시', '매우', '좀', '조금', '아주', '잘', '갖고', '가진',
    '같은', '같이', '때문에', '그럼', '그렇지', '아니', '또한', '하게', '누가', '만약', '뭔가', '어떤', '일단', '즉', '뿐', '때문',
    '대해', '관한', '대한', '그런', '이런', '저런', '어느', '아무', '너희', '우리', '너', '나', '그녀', '그들', '여러분', '어디',
    '무엇', '무슨', '왜', '어떻게', '언제', '누구', '입니다', '있는', '없는', '어떤', '같이', '처럼', '이렇게', '저렇게', '하여',
    '아', '휴', '아이구', '아이쿠', '아이고', '어', '나', '우리', '저희', '따라', '의해', '때문', '부터', '대로', '하', '것들',
    '그때', '그런데', '다', '더', '때', '되어', '한테', '그리고', '그래서', '이후', '인한', '이와', '보다', '처럼', '아무', '으로', '에게'
]

# 형태소 분석 및 불용어 제거 함수
def preprocess(text):
    okt = Okt()
    tokens = okt.morphs(text)
    tokens = [word for word in tokens if word not in stopwords and len(word) > 1]
    return ' '.join(tokens)

def modelstart(user_input, kindb):
    # 사전학습된 SentenceTransformer 모델 로드
    model = SentenceTransformer(os.environ['MODEL_NAME'])

    print(kindb)
    # 종류 6개중 하나를 골랐을 경우(그 해당 데이터 df에 저장)
    data = list(collection.find({"kindb": kindb}))
    df = pd.DataFrame(data, columns=["kinda", "content", "embedding", "index"])

    # 사용자 키워드 입력 및 전처리
    user_embedding = model.encode(user_input)

    # 유사도 계산
    similarities = []
    for i, case_embedding in enumerate(df['embedding']):
        similarity = util.pytorch_cos_sim(user_embedding, case_embedding).item()
        similarities.append((i, similarity))

    # 유사도에 따라 정렬
    sorted_similarities = sorted(similarities, key=lambda x: x[1], reverse=True)

    # 결과 출력
    top_5_similarities = []
    for index, similarity in sorted_similarities[:5]:
        content = df['content'].loc[index]  # 데이터의 요약문장
        kinda = df["index"].loc[index], df['kinda'].loc[index] # 그 데이터의 index와 kinda 값
        top_5_similarities.append({
            "content": content,
            "kinda": kinda,
            "similarity": similarity
        })

    return top_5_similarities
