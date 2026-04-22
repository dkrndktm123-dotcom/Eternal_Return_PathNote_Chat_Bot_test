from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from db import init_db
from crawler import parse_patch
from rag import ingest_chunks, search, format_answer
from schemas import AskResponse, IngestResponse

app = FastAPI(title="ER PATCH ARCADE API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup():
    init_db()

@app.post("/ingest", response_model=IngestResponse)
def ingest(limit: int = Query(10, ge=1, le=30)):
    chunks = parse_patch(limit=limit)
    if not chunks:
        raise HTTPException(status_code=500, detail="패치 chunk 생성 실패")
    ingest_chunks(chunks)
    return IngestResponse(message="ingested", count=len(chunks))

@app.post("/ask", response_model=AskResponse)
def ask(q: str = Query(...)):
    rows, category_hint, entity_hint = search(q, top_k=50)
    answer = format_answer(q, rows, category_hint, entity_hint)
    return AskResponse(answer=answer)
