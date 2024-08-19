# pip install fastapi
# pip install uvicorn

import os
import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from data import search_caselaw, findcaselaw, findanswer, findNomusa, calculatorprice
from dotenv import load_dotenv
from typing import List
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

origins = [
    "http://54.180.228.231",
    "http://localhost:8000"
]

# 허용하는 api 설정 배포 시 중요함 > 설정이 안되어있으면 서버에서 요청한 url을 찾지 못한다.
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class SearchRequest(BaseModel):
    result: str
    classification: str
    text: str
class CaseLawRequest(BaseModel):
    accnum: str
class AIRequest(BaseModel):
    text: str
    select: str
class AICalCulRequest(BaseModel):
    text: str
    select: str

base_dir = os.path.dirname(os.path.abspath(__file__))
templates = Jinja2Templates(directory=os.path.join(base_dir, "Client/templates"))
app.mount("/static", StaticFiles(directory=os.path.join(base_dir, "Client/static")), name="static")
load_dotenv(os.path.join(base_dir, ".env"))

# HTML 렌더링
# 메인 페이지
@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse("main.html", {"request": request})

# 산재 검색 페이지
@app.get("/CaseLaw", response_class=HTMLResponse)
async def search_sanjae(request: Request):
    return templates.TemplateResponse("caselawPage.html", {"request": request})

# 산재 상세내용 페이지
@app.get('/CaseLaw/data', response_class=HTMLResponse)
async def detail_sanjae(accnum: str, request: Request):
    return templates.TemplateResponse("caselawDetail.html", {"request": request, "accnum": accnum})

# AI 판별 서비스 페이지
@ app.get("/AI", response_class=HTMLResponse)
async def service_ai(request: Request):
    return templates.TemplateResponse("AIPage.html", {"request": request})

# data
@app.post("/search")
async def search(request: SearchRequest):
    result = request.result
    classification = request.classification
    text = request.text
    search = search_caselaw(result, classification, text)
    return search
@app.post('/CaseLaw/data')
async def detail_sanjae(request: CaseLawRequest):
    accnum = request.accnum
    search = findcaselaw(accnum)
    return search
@app.post('/AI')
async def answerReturn(request: AIRequest):
    text = request.text
    select = request.select
    result = findanswer(text, select)
    return result
@app.post('/AI/nomusa')
async def FindNomusa():
    data = findNomusa()
    return data
@app.post('/AI/Amount')
async def calculator(request: AICalCulRequest):
    text = request.text
    select = request.select
    result = calculatorprice(text, select)
    return result

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=os.environ["PORT"], reload=True)
