from fastapi import FastAPI, UploadFile, File, Request
from fastapi.middleware.cors import CORSMiddleware
from pipeline import get_status, get_latest_results, stop_recording
from summarizer import transcriber, extract_keywords_from_text as tokenization, wikisearch, summarizer, run_summarizer_pipeline
from fastapi.responses import JSONResponse

app = FastAPI()
UPLOAD_DIR = "media/recordings"

origins = [
    "http://localhost",
    "http://localhost:3000",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/summarizeit")
async def summarizeit(q: str):
    return await summarizer(q)


@app.get("/tokens")
async def tokens(q: str):
    return await tokenization(q)


@app.get("/search")
async def search(q: str):
    return await wikisearch(q)

@app.post("/transcribe/")
async def transcribe_audio(audio_file: UploadFile = File(...)):

    result = await transcriber(audio_file)
    return JSONResponse(result)
@app.post("/process/")
async def process_audio(audio_file: UploadFile = File(...)):
    result = await run_summarizer_pipeline(audio_file)
    return JSONResponse(result)

# Frontend calls this with POST, not GET.
@app.post("/stop/")
async def stop():
    return await stop_recording()


@app.get("/status/")
async def status():
    return await get_status()


@app.get("/results/")
async def results():
    return await get_latest_results()