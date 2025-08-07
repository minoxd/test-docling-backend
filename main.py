import os
import tempfile

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request

from utils.chunking import process

app = FastAPI()
templates = Jinja2Templates(directory="templates")

chunks_storage = {}


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/upload", response_class=HTMLResponse)
async def upload_file(request: Request, file: UploadFile = File(None), url: str = Form(None)):
    if not file and not url:
        raise HTTPException(status_code=400, detail="Please provide a file or URL")

    html_chunks = []
    if file:
        with tempfile.NamedTemporaryFile(delete=False, suffix=file.filename, dir='temp_uploads') as tmp:
            tmp.write(await file.read())
            tmp_path = tmp.name
        html_chunks = await process(source=tmp_path)
        os.remove(tmp_path)  # remove this line if you want to keep the file in the system 👍
    elif url:
        html_chunks = await process(source=url)

    # Store chunks with a simple key (for demo; consider session ID in production)
    key = str(len(chunks_storage))
    chunks_storage[key] = html_chunks

    return templates.TemplateResponse("results.html", {
        "request": request,
        "chunks": html_chunks,
        "chunk_key": key
    })


@app.get("/export/{chunk_key}", response_class=JSONResponse)
async def export_chunks(chunk_key: str):
    if chunk_key not in chunks_storage:
        raise HTTPException(status_code=404, detail="Chunks not found")
    return {"chunks": chunks_storage[chunk_key]}