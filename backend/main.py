"""FastAPI backend for Smart Document Reader."""

import json
import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

app = FastAPI(title="Smart Document Reader API")

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("Missing SUPABASE_URL / SUPABASE_KEY in .env")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


# ---------- Data models ----------

class DocumentCreate(BaseModel):
    filename: str
    text: str
    summary: str
    info: dict
    stats: dict


class ChatCreate(BaseModel):
    doc_id: int
    question: str
    answer: str


# ---------- Routes ----------

@app.get("/")
def root():
    return {"message": "Smart Document Reader API is running"}


@app.get("/api/documents")
def list_documents():
    try:
        res = (supabase.table("documents")
               .select("id, filename, summary, saved_at")
               .order("id", desc=True)
               .execute())
        return {"status": "success", "count": len(res.data), "data": res.data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/documents/{doc_id}")
def get_document(doc_id: int):
    try:
        res = supabase.table("documents").select("*").eq("id", doc_id).execute()
        if not res.data:
            raise HTTPException(status_code=404, detail="Document not found")
        return {"status": "success", "data": res.data[0]}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/documents", status_code=201)
def create_document(doc: DocumentCreate):
    try:
        payload = {
            "filename": doc.filename,
            "text": doc.text,
            "summary": doc.summary,
            "info": json.dumps(doc.info),
            "stats": json.dumps(doc.stats),
        }
        res = supabase.table("documents").insert(payload).execute()
        return {"status": "success", "data": res.data[0]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/chats", status_code=201)
def create_chat(chat: ChatCreate):
    try:
        payload = {
            "doc_id": chat.doc_id,
            "question": chat.question,
            "answer": chat.answer,
        }
        res = supabase.table("chat_history").insert(payload).execute()
        return {"status": "success", "data": res.data[0]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/documents/{doc_id}")
def delete_document(doc_id: int):
    try:
        supabase.table("chat_history").delete().eq("doc_id", doc_id).execute()
        res = supabase.table("documents").delete().eq("id", doc_id).execute()
        if not res.data:
            raise HTTPException(status_code=404, detail="Document not found")
        return {"status": "success", "message": f"Document {doc_id} deleted"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/test-error")
def test_error():
    raise HTTPException(status_code=400, detail="This is a deliberate test error")