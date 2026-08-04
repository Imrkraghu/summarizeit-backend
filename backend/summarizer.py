import os
import speech_recognition as sr
from collections import Counter
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
import queue
from huggingface_hub import InferenceClient
from dotenv import load_dotenv
import wikipediaapi
import pandas as pd
import threading
from moviepy import AudioFileClip

# Global threading variables
audio_queue = queue.Queue()
processing_threads = []
recording_counter = 0

# NLTK Setup
NLTK_CUSTOM_PATH = os.path.join('nltk_resources')
os.makedirs(NLTK_CUSTOM_PATH, exist_ok=True)
nltk.data.path.append(NLTK_CUSTOM_PATH)



# global cache dictionary
_cache = {}

def cache_set(key, value):
    _cache[key] = value

def cache_get(key, default=None):
    return _cache.get(key, default)


def is_resource_available(resource_path):
    try:
        nltk.data.find(resource_path)
        return True
    except LookupError:
        return False


for resource in ['punkt', 'stopwords', 'punkt_tab']:
    if not is_resource_available(f'tokenizers/{resource}') and not is_resource_available(f'corpora/{resource}'):
        nltk.download(resource, download_dir=NLTK_CUSTOM_PATH)

def record_audio_to_file(audio_bytes=None, OUTPUT_FILENAME=None, duration=10):
    global recording_counter
    if OUTPUT_FILENAME is None:
        recording_counter += 1
        OUTPUT_FILENAME = os.path.join("recordings", f"recorded_audio_{recording_counter}.webm")
    output_dir = os.path.dirname(OUTPUT_FILENAME)
    os.makedirs(output_dir, exist_ok=True)

    if audio_bytes is not None:
        # Audio was already recorded client-side (browser MediaRecorder) —
        # just persist the bytes we were given instead of capturing locally.
        try:
            with open(OUTPUT_FILENAME, 'wb') as f:
                f.write(audio_bytes)
            return OUTPUT_FILENAME
        except OSError as e:
            print(f"OSError: {e}")
            return None

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

# Extract Keywords
async def extract_keywords_from_text(query: str = None, transcription_file: str = None):
    # Decide source of text
    if transcription_file:
        with open(transcription_file, "r") as file:
            text = file.read()
    elif query:
        text = query
    else:
        raise ValueError("Either query or transcription_file must be provided")

    # Tokenize and clean
    words = word_tokenize(text)
    words = [word.lower() for word in words if word.isalnum()]
    stop_words = set(stopwords.words("english"))
    filtered_words = [word for word in words if word not in stop_words]

    # Frequency analysis
    word_freq = Counter(filtered_words)
    keywords = [kw for kw, _ in word_freq.most_common(10)]

    # Save keywords only if a file path was passed
    keywords_file = None
    if transcription_file:
        base_name = os.path.splitext(os.path.basename(transcription_file))[0]
        keywords_file = os.path.join("media", "keywords", f"{base_name}_keywords.txt")
        os.makedirs(os.path.dirname(keywords_file), exist_ok=True)
        with open(keywords_file, "w") as file:
            for keyword in keywords:
                file.write(f"{keyword}\n")

    print("Top keywords:", keywords)
    return keywords, keywords_file

# Filter Keywords
def extract_valid_keywords(keywords_file):
    with open(keywords_file, "r") as file:
        keywords = [kw.strip() for kw in file.readlines()]
    dataset_path = os.path.join("data", "dataset.csv")
    df = pd.read_csv(dataset_path)
    valid_set = set()
    for column in df.columns:
        valid_set.update(df[column].dropna().str.lower().str.strip().tolist())
    filtered_keywords = [kw for kw in keywords if kw.lower() in valid_set]
    print("Filtered keywords:", filtered_keywords)
    return filtered_keywords


async def summarizer(q:str):
    load_dotenv()
    client = InferenceClient(
        model="facebook/bart-large-cnn",
        token=os.getenv("HF_TOKEN")
    )
    return (client.summarization(q))

async def wikisearch(q:str):
    load_dotenv()
    username = os.getenv("PROJECT_NAME")
    usermail = os.getenv("PROJECT_MAIL")
    wiki_wiki = wikipediaapi.Wikipedia( user_agent = f"{username} ({usermail})", language ='en')
    page_py = wiki_wiki.page(q)
    if page_py.exists() and len(page_py.summary) > 30:
        return page_py.summary
    else:
        return "No summary found for the given query."

# Fetch Wikipedia & Summarize
async def fetch_summary_for_keyword(keyword):
    try:
        extracted_text = await wikisearch(keyword)
        if (extracted_text == "No summary found for the given query."):
            return "No summary available"
        else:
            return await summarizer(extracted_text)
    except Exception as e:
        print(f"Failed to summarize {keyword}: {e}")
        return "Summary unavailable."

# Main Pipeline
async def run_summarizer_pipeline(audio_file):
    for folder in ["recordings", "transcriptions", "keywords"]:
        os.makedirs(os.path.join("media", folder), exist_ok=True)

    summaries = []

    result = await transcriber(audio_file)
    transcription = result["text"]
    transcription_file = result["file"]

    if not transcription.strip() or not transcription_file:
        print("No transcription available")
        return {"transcription": "", "keywords": [], "summaries": []}

    keywords, keywords_file = await extract_keywords_from_text(transcription_file)
    if not keywords_file:
        print("No keyword file created")
        return {"transcription": transcription, "keywords": [], "summaries": []}
    filtered_keywords = extract_valid_keywords(keywords_file)

    if not filtered_keywords:
        print("No valid keywords found")
        return {"transcription": transcription, "keywords": [], "summaries": []}

    for keyword in filtered_keywords:
        try:
            summary = await fetch_summary_for_keyword(keyword)
            summaries.append({"keyword": keyword, "text": summary})
        except Exception as e:
            print(f"Error while fetching summary for {keyword}: {e}")

    return {
        "transcription": transcription,
        "keywords": filtered_keywords,
        "summaries": summaries,
    }


def process_audio_worker(results):
    while True:
        try:
            audio_path = audio_queue.get(timeout=2)
            if audio_path is None:
                break
            print(f"Processing audio file: {audio_path}")
            run_summarizer_pipeline(audio_path, results)
            audio_queue.task_done()
        except queue.Empty:
            if not cache_get("recording_active", False):
                break
            continue
        except Exception as e:
            print(f"Error processing audio: {e}")
            audio_queue.task_done()
    print("Processing worker stopped")

def start_processing_threads(num_threads=1):
    results = queue.Queue()
    processing_threads.clear()
    for i in range(num_threads):
        t = threading.Thread(target=process_audio_worker, args=(results,), daemon=True)
        t.start()
        processing_threads.append(t)
        print(f"Started processing thread {i+1}")
    return results

def stop_all(record_thread):
    print("Stopping all threads...")
    cache_set("recording_active", False)
    if record_thread:
        record_thread.join()
        print("Recording thread joined")
    audio_queue.join()
    print("Audio queue emptied")
    for _ in processing_threads:
        audio_queue.put(None)
    for t in processing_threads:
        t.join()
    processing_threads.clear()
    print("All threads stopped")