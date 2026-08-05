# Project Summarizeit

Summarizeit is a **FastAPI-based pipeline** that takes audio input, transcribes it into text, extracts meaningful keywords, and generates concise summaries using **Wikipedia** and **Hugging Face models**.  

It is designed for developers and researchers who want to quickly convert spoken content into structured summaries with keyword filtering.

---

## 🚀 Features
- **Audio Transcription**: Converts `.wav` / `.webm` recordings into text using `speech_recognition`.
- **Keyword Extraction**: Uses `NLTK` for tokenization, stopword removal, and frequency analysis.
- **Keyword Validation**: Filters extracted keywords against a dataset (`dataset.csv`).
- **Wikipedia Search**: Fetches summaries for valid keywords using `wikipediaapi`.
- **Text Summarization**: Uses Hugging Face’s `facebook/bart-large-cnn` model for concise summaries.
- **Pipeline Integration**: End-to-end function `run_summarizer_pipeline` handles transcription → keywords → summaries.

---

## 📂 Project Structure
```
Project-Summarizeit/
│
├── app.py                # FastAPI entry point
│── media/
│   ├── recordings/           # Saved audio files
│   ├── transcriptions/       # Text transcriptions
│   └── keywords/             # Extracted keyword files
│── requirements.txt          # Python dependencies
│── README.md                 # Documentation
```

---

## ⚙️ Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/Imrkraghu/Project-Summarizeit.git
   cd Project-Summarizeit
   ```

2. Create a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate   # Linux/macOS
   .venv\Scripts\activate      # Windows
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Download required NLTK resources:
   ```python
   import nltk
   nltk.download("punkt")
   nltk.download("stopwords")
   ```

---

## 🔑 Environment Variables
Create a `.env` file in the project root with:
```
HF_TOKEN=your_huggingface_api_token
PROJECT_NAME=Summarizeit
PROJECT_MAIL=your_email@example.com
```

---

## ▶️ Usage
Run the FastAPI server:
```bash
uvicorn backend.app:app --reload
```



---

## 🛠️ Example Output
```json
{
  "transcription": "Artificial intelligence is transforming industries...",
  "keywords": ["artificial", "intelligence", "industries"],
  "summaries": [
    {"keyword": "artificial", "text": "Artificial intelligence refers to..."},
    {"keyword": "intelligence", "text": "Intelligence is the ability to..."}
  ]
}
