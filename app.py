from fastapi import FastAPI
import os
import nltk 
# from huggingface_hub import InferenceClient
from dotenv import load_dotenv
import wikipediaapi
import speech_recognition as sr
app = FastAPI()

@app.get("/summarizeit")
async def summarizeit(q:str):
    return summarizer(q)
async def summarizer(q:str):
    load_dotenv()
    # client = InferenceClient(
    #     model="facebook/bart-large-cnn",
    #     token=os.getenv("HF_TOKEN")
    # )
    # return (client.summarization(q))
    return {"message": "Summarization functionality is currently disabled."}

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
    if page_py.exists():
        return page_py.summary
    else:
        return "No summary found for the given query."

def is_resource_available(resource_path):
    try:
        nltk.data.find(resource_path)
        return True
    except LookupError:
        return False

@app.get("/transcribe")
async def transcribe_audio():
    return await transcriber()

async def transcriber(OUTPUT_FILENAME):
    recognizer = sr.Recognizer()
    with sr.AudioFile(OUTPUT_FILENAME) as source:
        audio = recognizer.record(source)
    try:
        text = recognizer.recognize_google(audio)
        print("Transcription:", text)
        base_name = os.path.splitext(os.path.basename(OUTPUT_FILENAME))[0]
        transcription_file = os.path.join("transcriptions", f"{base_name}_transcription.txt")
        os.makedirs(os.path.dirname(transcription_file), exist_ok=True)
        with open(transcription_file, "w") as f:
            f.write(text)
        return text, transcription_file
    except sr.UnknownValueError:
        print("Speech Recognition could not understand the audio.")
    except sr.RequestError as e:
        print(f"Could not request results; {e}")
    return "", None

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
            for keyword in keyword_list:
                print(f"Summary for the keyword {keyword} is available,\n")
                summaries[keyword] = response
    return summaries