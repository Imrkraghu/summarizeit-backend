from fastapi import FastAPI, UploadFile, File
import os
from fastapi.responses import JSONResponse
import nltk 
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from huggingface_hub import InferenceClient
from dotenv import load_dotenv
import wikipediaapi
import speech_recognition as sr
from moviepy import AudioFileClip
app = FastAPI()

@app.get("/summarizeit")
async def summarizeit(q:str):
    return await summarizer(q)
async def summarizer(q:str):
    load_dotenv()
    client = InferenceClient(
        model="facebook/bart-large-cnn",
        token=os.getenv("HF_TOKEN")
    )
    return (client.summarization(q))

@app.get("/tokens")
async def tokens(q:str):
    return await tokenization(q)

async def tokenization(q:str| None = None):
    NLTK_CUSTOM_PATH = os.path.join('nltk_resources')
    os.makedirs(NLTK_CUSTOM_PATH, exist_ok=True)
    nltk.data.path.append(NLTK_CUSTOM_PATH)
    for resource in ['punkt', 'stopwords', 'punkt_tab']:
        if not is_resource_available(f'tokenizers/{resource}') and not is_resource_available(f'corpora/{resource}'):
            nltk.download(resource, download_dir=NLTK_CUSTOM_PATH)
    tokens = nltk.word_tokenize(q)
    tokens = q.split()
    stop_words = set(nltk.corpus.stopwords.words("english"))
    filtered_keywords = [token for token in tokens if token not in stop_words ]
    # after filtering the keywords lets store them somewhere
    KEYWORD_PATH = os.path.join("keywords")
    file_path = os.path.join(KEYWORD_PATH, "keywords.txt")
    os.makedirs(KEYWORD_PATH, exist_ok=True)
    with open(file_path,"w") as file:
        for keyword in range(len(filtered_keywords)):
            file.write(f"{filtered_keywords[keyword]},\n")
    return({
            "filtered_keywords_length":len(filtered_keywords),
            "keywords": filtered_keywords}
    )

@app.get("/search")
async def search(q:str):
    return await wikisearch(q)

async def wikisearch(q:str):
    load_dotenv()
    username = os.getenv("PROJECT_NAME")
    usermail = os.getenv("PROJECT_MAIL")
    wiki_wiki = wikipediaapi.Wikipedia( user_agent = f"{username} ({usermail})", language ='en')
    page_py = wiki_wiki.page(q)
    if page_py.exists() and len(page_py.summary) >30:
        return page_py.summary
    else:
        return "No summary found for the given query."

def is_resource_available(resource_path):
    try:
        nltk.data.find(resource_path)
        return True
    except LookupError:
        return False

@app.post("/transcribe/")
async def transcribe_audio(audio_file: UploadFile = File(...)):

    result = await transcriber(audio_file)
    return JSONResponse(result)

def convert_to_wav(input_path, output_path):
    clip = AudioFileClip(input_path)
    clip.write_audiofile(output_path)  # 16-bit PCM WAV
    clip.close()
    return output_path

async def transcriber(audio_file):
    for folder in ["recordings", "transcriptions", "keywords"]:
        os.makedirs(os.path.join("media", folder), exist_ok=True)

    output_path = os.path.join("media", "recordings", audio_file.filename)

    # Write the uploaded bytes to disk FIRST — everything downstream needs
    # the file to actually exist.
    with open(output_path, "wb") as f:
        f.write(await audio_file.read())

    # THEN convert, if it needs converting.
    if output_path.endswith((".mp3", ".webm", ".mp4")):
        wav_path = output_path.rsplit(".", 1)[0] + ".wav"
        convert_to_wav(output_path, wav_path)
        output_path = wav_path

    recognizer = sr.Recognizer()
    with sr.AudioFile(output_path) as source:
        audio = recognizer.record(source)

    try:
        text = recognizer.recognize_google(audio)
        base_name = os.path.splitext(os.path.basename(output_path))[0]
        transcription_file = os.path.join(
            "media", "transcriptions", f"{base_name}_transcription.txt"
        )
        with open(transcription_file, "w") as f:
            f.write(text)

        return {"text": text, "file": transcription_file}
    except sr.UnknownValueError:
        return {"text": "", "file": None}
    except sr.RequestError as e:
        print(f"Could not request results; {e}")
        return {"text": "", "file": None}

@app.get("/")
async def main(querry:str | None = None):
    print("Welcome to the SummarizeIt API")
    if querry is None:
        querry = "Language models"
    output = await tokens(querry)
    keyword_list = output["keywords"]
    summaries = {}
    print("keyword list", keyword_list)
    print(f"Filtered keywords are : {keyword_list}")
    for keyword in keyword_list:
        print(f"Searching for Filtered keyword {keyword} in Wikipedia Database :")
        response = await wikisearch(keyword)
        if response == "No summary found for the given query.":
            print("No summary available skipping for next keyword")
            continue
        else:
                print(f"Summary for the keyword {keyword} is available,\n")
                summaries[keyword] = response
    return {"summaries": summaries}


@app.post("process/")
async def run_summarizer_pipeline(audio_file: UploadFile = File(...)):
    for folder in ["recordings", "transcriptions", "keywords"]:
        os.makedirs(os.path.join("media", folder), exist_ok=True)

    summaries = []

    result = await transcriber(audio_file)
    transcription = result["text"]
    transcription_file = result["file"]

    if not transcription.strip() or not transcription_file:
        print("No transcription available")
        return {"transcription": "", "keywords": [], "summaries": []}

    filtered_keywords, keywords_file = await tokenization(transcription_file)
    if not keywords_file:
        print("No keyword file created")
        return {"transcription": transcription, "keywords": [], "summaries": []}

    if not filtered_keywords:
        print("No valid keywords found")
        return {"transcription": transcription, "keywords": [], "summaries": []}

    for keyword in filtered_keywords:
        try:
            summary = await wikisearch(keyword)
            if summary == "No summary found for the given query.":
                print(f"No summary available for {keyword}, skipping.")
                continue
            else:
                summarized = summarizer(summary)
            summaries.append({"keyword": keyword, "text": summarized})
        except Exception as e:
            print(f"Error while fetching summary for {keyword}: {e}")

    return {
        "transcription": transcription,
        "keywords": filtered_keywords,
        "summaries": summaries,
    }