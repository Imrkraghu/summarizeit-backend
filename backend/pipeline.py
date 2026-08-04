from summarizer import (
    start_processing_threads, 
    audio_queue, 
    processing_threads,
)
import queue
import time
from fastapi.responses import JSONResponse

# global cache dictionary
_cache = {}

def cache_set(key, value):
    _cache[key] = value

def cache_get(key, default=None):
    return _cache.get(key, default)


# Global variables to hold threads and results
record_thread = None
results_queue = None

# Global accumulator for the current session
current_session_data = {
    "transcriptions": [],
    "keywords": [],
    "summaries": []
}

def collect_results_from_queue():
    """
    Helper function to drain the queue into the global storage
    without blocking the main thread.
    """
    global results_queue, current_session_data
    
    if not results_queue:
        return

    while not results_queue.empty():
        try:
            # The workers in summarizer.py should now be using the 
            # 'smart_summarize' function that checks the DB
            transcription = results_queue.get_nowait()
            keywords = results_queue.get_nowait()  
            summaries = results_queue.get_nowait()

            if transcription and transcription.strip():
                current_session_data["transcriptions"].append(transcription)
            
            if keywords:
                current_session_data["keywords"].extend(keywords)
            
            if summaries:
                # 'summaries' list contains objects like {'keyword': 'X', 'text': 'Y'}
                current_session_data["summaries"].extend(summaries)
                
        except queue.Empty:
            break
        except Exception as e:
            print(f"Error draining queue: {e}")
            break

def format_response_data():
    """Helper to format the current data for JSON response"""
    combined_transcription = " | ".join(current_session_data["transcriptions"])
    
    # Remove duplicates for keywords in the UI list
    seen = set()
    unique_keywords = []
    for keyword in current_session_data["keywords"]:
        if keyword not in seen:
            seen.add(keyword)
            unique_keywords.append(keyword)

    return {
        "transcription": combined_transcription,
        "keywords": unique_keywords,
        "summaries": current_session_data["summaries"]
    }


async def get_latest_results():
    """Called by JS to get updates while recording/processing"""
    collect_results_from_queue() 
    data = format_response_data()
    
    is_processing = (audio_queue.qsize() > 0 or len(processing_threads) > 0)
    
    return JSONResponse({
        "transcription": data["transcription"],
        "keywords": data["keywords"],
        "summaries": data["summaries"],
        "is_processing": is_processing
    })

async def record_audio(request):
    """Start recording audio and processing threads"""
    global record_thread, results_queue, current_session_data

    if cache_get("recording_active", False):
        return JSONResponse({'error': 'Recording already in progress'}, status=400)

    try:
        # Reset Global Data
        current_session_data = {
            "transcriptions": [],
            "keywords": [],
            "summaries": []
        }
        
        cache_set("recording_active", False)
        time.sleep(0.1)
        
        # Clear queues
        while not audio_queue.empty():
            try:
                audio_queue.get_nowait()
                audio_queue.task_done()
            except queue.Empty:
                break

        processing_threads.clear()

        # Start threads
        results_queue = start_processing_threads(num_threads=3)

        return JSONResponse({
            "transcription": "",
            "keywords": [],
            "summaries": [],
            "message": "recording started successfully"
        })

    except Exception as e:
        cache_set("recording_active", False)
        return JSONResponse({'error': f'Failed to start recording: {str(e)}'}, status=500)

async def stop_recording():
    """Stop recording and collect all results"""
    global results_queue, current_session_data

    if not cache_get("recording_active", False):
        return JSONResponse({'error': 'No active recording to stop'}, status=400)

    try:
        cache_set("recording_active", False)


        audio_queue.join()

        for _ in processing_threads:
            audio_queue.put(None)

        for t in processing_threads:
            if t.is_alive():
                t.join(timeout=5)

        collect_results_from_queue()
        final_data = format_response_data()

        request.session['transcription'] = final_data["transcription"]
        request.session['keywords'] = final_data["keywords"]
        request.session['summaries'] = final_data["summaries"]

        processing_threads.clear()
        results_queue = None

        return JSONResponse({
            "transcription": final_data["transcription"],
            "keywords": final_data["keywords"],
            "summaries": final_data["summaries"],
            "message": "Recording stopped and processed successfully"
        })

    except Exception as e:
        cache_set("recording_active", False)
        return JSONResponse({'error': f'Error stopping recording: {str(e)}'}, status=500)


async def get_status():
    is_recording = cache_get("recording_active", False)
    queue_size = audio_queue.qsize() if audio_queue else 0
    
    return JSONResponse({
        'is_recording': is_recording,
        'queue_size': queue_size,
        'processing_threads': len(processing_threads)
    })
