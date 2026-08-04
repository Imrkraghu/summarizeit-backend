import { useEffect, useRef, useState } from 'react';
import '../style/Dashboard.css';

// Point these at your backend. Override with a .env value (REACT_APP_BACKEND_URL)
// if the API lives on a different host/port than the React dev server.
const API_BASE = process.env.REACT_APP_BACKEND_URL || '';
const ENDPOINTS = {
  status: `${API_BASE}/status/`,
  latestResults: `${API_BASE}/results/`,
  uploadChunk: `${API_BASE}/process/`,
  stopRecording: `${API_BASE}/stop/`,
};

const NAV_LINKS = [
  { href: '/about', label: 'About Us' },
  { href: '/team', label: 'Team' },
  { href: '/projects', label: 'Projects' },
  { href: '/contact', label: 'Contact' },
];

const SEGMENT_MS = 10000; // length of each recorded clip before it's sent off

export default function Dashboard() {
  const [menuOpen, setMenuOpen] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [finalizing, setFinalizing] = useState(false);
  const [segmentsSent, setSegmentsSent] = useState(0);
  const [micError, setMicError] = useState('');

  const [dotStatus, setDotStatus] = useState('idle'); // idle | recording | processing
  const [statusText, setStatusText] = useState('Ready to record');
  const [systemStatusText, setSystemStatusText] = useState('Idle');
  const [audioQueueSize, setAudioQueueSize] = useState(0);
  const [activeThreads, setActiveThreads] = useState(0);
  const [showProcessingInfo, setShowProcessingInfo] = useState(false);

  const [transcription, setTranscription] = useState('');
  const [keywords, setKeywords] = useState([]);
  const [summaries, setSummaries] = useState([]);

  const statusIntervalRef = useRef(null);
  const resultsIntervalRef = useRef(null);
  const isRecordingRef = useRef(false);

  const streamRef = useRef(null);
  const recorderRef = useRef(null);
  const segmentTimerRef = useRef(null);
  const chunkIndexRef = useRef(0);

  useEffect(() => {
    isRecordingRef.current = isRecording;
  }, [isRecording]);

  // ---- polling: status + progressive results ----

  const updateStatus = async () => {
    try {
      const res = await fetch(ENDPOINTS.status, { method: 'GET' });
      const data = await res.json();

      if (data.is_recording) {
        setDotStatus('recording');
        setStatusText('Recording...');
      } else if (data.queue_size > 0 || data.processing_threads > 0) {
        setDotStatus('processing');
        setStatusText('Processing...');
      } else {
        setDotStatus('idle');
        setStatusText('Ready');
      }

      setSystemStatusText(
        data.is_recording ? 'Recording' : data.queue_size > 0 ? 'Processing' : 'Idle'
      );
      setAudioQueueSize(data.queue_size);
      setActiveThreads(data.processing_threads);
      setShowProcessingInfo(data.is_recording || data.queue_size > 0 || data.processing_threads > 0);
    } catch (err) {
      console.error(err);
    }
  };

  const stopPolling = () => {
    if (statusIntervalRef.current) clearInterval(statusIntervalRef.current);
    if (resultsIntervalRef.current) clearInterval(resultsIntervalRef.current);
    statusIntervalRef.current = null;
    resultsIntervalRef.current = null;
  };

  const fetchResults = async () => {
    try {
      const res = await fetch(ENDPOINTS.latestResults, { method: 'GET' });
      const data = await res.json();

      // Data is applied as soon as it arrives, so the screen updates mid-recording,
      // not just after the user stops.
      if (data.transcription && data.transcription.trim()) {
        setTranscription(data.transcription);
      }
      if (data.keywords && data.keywords.length > 0) {
        setKeywords(data.keywords);
      }
      if (data.summaries && data.summaries.length > 0) {
        setSummaries(data.summaries);
      }

      // Only stop polling once recording has been stopped AND the backend
      // confirms there's nothing left in flight.
      if (!isRecordingRef.current && !data.is_processing) {
        stopPolling();
        setFinalizing(false);
      }
    } catch (err) {
      console.error(err);
    }
  };

  const startPolling = () => {
    stopPolling();
    statusIntervalRef.current = setInterval(updateStatus, 1500);
    resultsIntervalRef.current = setInterval(fetchResults, 2000);
  };

  // ---- audio capture: MediaRecorder, chunked in fixed-length segments ----

  const uploadChunk = async (blob, index) => {
    try {
      const formData = new FormData();
      formData.append('audio_file', blob, `chunk_${index}.webm`);
      await fetch(ENDPOINTS.uploadChunk, { method: 'POST', body: formData });
      setSegmentsSent((n) => n + 1);
    } catch (err) {
      console.error('Chunk upload failed', err);
    }
  };

  const recordNextSegment = () => {
    if (!streamRef.current || !isRecordingRef.current) return;

    const recorder = new MediaRecorder(streamRef.current, { mimeType: 'audio/webm' });
    const localChunks = [];

    recorder.ondataavailable = (e) => {
      if (e.data && e.data.size > 0) localChunks.push(e.data);
    };

    recorder.onstop = () => {
      const blob = new Blob(localChunks, { type: 'audio/webm' });
      const index = chunkIndexRef.current;
      chunkIndexRef.current += 1;

      // Fire-and-forget upload — recording of the next segment (or shutdown)
      // does not wait on this request finishing.
      uploadChunk(blob, index);

      if (isRecordingRef.current) {
        // Still recording -> immediately start capturing the next 10s clip.
        recordNextSegment();
      } else {
        // User pressed stop -> this was the final (possibly shorter) segment.
        // Backend processing continues; polling stays alive until it's done.
        setFinalizing(true);
      }
    };

    recorderRef.current = recorder;
    recorder.start();

    segmentTimerRef.current = setTimeout(() => {
      if (recorder.state !== 'inactive') recorder.stop();
    }, SEGMENT_MS);
  };

  const startRecording = async () => {
    setMicError('');
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;
      chunkIndexRef.current = 0;

      setSegmentsSent(0);
      setTranscription('');
      setKeywords([]);
      setSummaries([]);
      setFinalizing(false);

      isRecordingRef.current = true;
      setIsRecording(true);

      startPolling();
      recordNextSegment();
    } catch (err) {
      setMicError('Could not access microphone: ' + err.message);
      resetUI();
    }
  };

  const stopRecording = async () => {
    // Stop capturing new audio immediately.
    isRecordingRef.current = false;
    setIsRecording(false);

    if (segmentTimerRef.current) {
      clearTimeout(segmentTimerRef.current);
      segmentTimerRef.current = null;
    }

    if (recorderRef.current && recorderRef.current.state !== 'inactive') {
      // Triggers onstop -> uploads the final (short) segment -> setFinalizing(true)
      recorderRef.current.stop();
    } else {
      setFinalizing(true);
    }

    if (streamRef.current) {
      streamRef.current.getTracks().forEach((t) => t.stop());
      streamRef.current = null;
    }

    // Let the backend know no more audio is coming. Processing of what's
    // already queued keeps running — polling (started in startRecording)
    // stays active until fetchResults sees is_processing: false.
    try {
      await fetch(ENDPOINTS.stopRecording, { method: 'POST' });
    } catch (err) {
      console.error('Stop signal failed', err);
    }
  };

  const resetUI = () => {
    isRecordingRef.current = false;
    setIsRecording(false);
    setFinalizing(false);

    if (segmentTimerRef.current) clearTimeout(segmentTimerRef.current);
    if (recorderRef.current && recorderRef.current.state !== 'inactive') {
      recorderRef.current.stop();
    }
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((t) => t.stop());
      streamRef.current = null;
    }
    stopPolling();
  };

  useEffect(() => {
    updateStatus();
    return () => {
      stopPolling();
      if (segmentTimerRef.current) clearTimeout(segmentTimerRef.current);
      if (streamRef.current) streamRef.current.getTracks().forEach((t) => t.stop());
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <>
      {/* Navbar */}
      <div className="si-nav">
        <div className="si-nav__inner">
          <a href="/home" className="si-nav__brand">SummarizeIT</a>
          <nav className="si-nav__links">
            <a href="/home">Home</a>
            {NAV_LINKS.map((l) => (
              <a key={l.href} href={l.href}>{l.label}</a>
            ))}
          </nav>
          <button
            className="si-nav__toggle"
            onClick={() => setMenuOpen((v) => !v)}
            title="Toggle Navigation Menu"
          >
            &#9776;
          </button>
        </div>
        {menuOpen && (
          <div className="si-nav__mobile">
            {NAV_LINKS.map((l) => (
              <a key={l.href} href={l.href} onClick={() => setMenuOpen(false)}>{l.label}</a>
            ))}
          </div>
        )}
      </div>

      {/* Header */}
      <header className="si-hero">
        <div className="si-hero__waveform" aria-hidden="true">
          {Array.from({ length: 48 }).map((_, i) => (
            <span key={i} style={{ animationDelay: `${(i % 12) * 0.09}s` }} />
          ))}
        </div>
        <div className="si-hero__content">
          <p className="si-eyebrow">Record · Transcribe · Summarize</p>
          <h1 className="si-hero__title">SummarizeIT</h1>
          <p className="si-hero__subtitle">Live speech in, structured insight out.</p>

          {!isRecording && !finalizing && (
            <button className="si-btn" onClick={startRecording}>
              🎙️ Start Recording
            </button>
          )}

          {isRecording && (
            <button className="si-btn si-btn--recording" onClick={stopRecording}>
              ⏹️ Stop Recording
            </button>
          )}

          {!isRecording && finalizing && (
            <button className="si-btn" disabled>
              🔄 Finalizing...
            </button>
          )}

          {micError && <p className="si-mic-error">{micError}</p>}

          <div className="si-status-row">
            <span className={`status-indicator status-${dotStatus}`} />
            <span>{statusText}</span>
          </div>

          {(showProcessingInfo || isRecording) && (
            <div className="processing-info">
              Clips sent: {segmentsSent} &nbsp;|&nbsp; Processing threads: {activeThreads} &nbsp;|&nbsp; Queue size: {audioQueueSize}
            </div>
          )}
        </div>
      </header>

      <div className="si-dashboard">
        {/* Control Panel */}
        <div className="si-card">
          <div className="si-card__header">
            <span>🎛️ Control Panel</span>
            <button className="si-btn-ghost" onClick={updateStatus}>Refresh Status</button>
          </div>
          <div className="si-card__body">
            <div className="si-status-grid">
              <p><strong>Status:</strong> {systemStatusText}</p>
              <p><strong>Audio Segments Queued:</strong> {audioQueueSize}</p>
              <p><strong>Active Processing Threads:</strong> {activeThreads}</p>
              <p><strong>Clips Sent This Session:</strong> {segmentsSent}</p>
            </div>
          </div>
        </div>

        {/* Transcribed Text */}
        <div className="si-card">
          <div className="si-card__header">📝 Transcribed Text</div>
          <div className="si-card__body">
            {transcription ? (
              <pre>{transcription}</pre>
            ) : (
              <p className="text-muted">No transcription yet. Start recording to see transcribed text appear here.</p>
            )}
          </div>
        </div>

        {/* Extracted Keywords */}
        <div className="si-card">
          <div className="si-card__header">🔍 Extracted Keywords</div>
          <div className="si-card__body">
            {keywords.length > 0 ? (
              <ul className="si-keyword-list">
                {keywords.map((kw, i) => (
                  <li key={`${kw}-${i}`}>{kw}</li>
                ))}
              </ul>
            ) : (
              <p className="text-muted">No keywords extracted yet. Keywords will appear here after processing.</p>
            )}
          </div>
        </div>

        {/* Keyword Summaries */}
        <div className="si-card">
          <div className="si-card__header">🧠 Keyword Summaries</div>
          <div className="si-card__body">
            {summaries.length > 0 ? (
              summaries.map((s, i) => (
                <div className="summary-box" key={`${s.keyword}-${i}`}>
                  <strong>{s.keyword}</strong>: {s.text}
                </div>
              ))
            ) : (
              <p className="text-muted">No summaries available yet. Summaries will be generated for valid keywords.</p>
            )}
          </div>
        </div>
      </div>

      <footer className="si-footer">
        <p>Powered by <a href="https://github.com/Imrkraghu/" target="_blank" rel="noreferrer">imrkraghu</a></p>
      </footer>
    </>
  );
}