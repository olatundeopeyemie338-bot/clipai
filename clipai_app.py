import os
import json
import subprocess
import tempfile
import threading
import uuid
import re
from flask import Flask, request, jsonify, send_file
from flask import send_from_directory
from anthropic import Anthropic

app = Flask(__name__)
client = Anthropic()

UPLOAD_FOLDER = "/tmp/uploads"
OUTPUT_FOLDER = "/tmp/outputs"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

jobs = {}  # job_id -> status dict

HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<title>ClipAI — Turn Long Videos Into Viral Shorts</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { background: #0a0a0f; color: #e2e8f0; font-family: 'Inter', system-ui, sans-serif; min-height: 100vh; }

  .nav { display: flex; align-items: center; padding: 20px 40px; border-bottom: 1px solid #1e1e2e; }
  .logo { font-size: 1.4rem; font-weight: 800; background: linear-gradient(135deg, #a78bfa, #ec4899); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
  .nav-tag { margin-left: 12px; background: #1e1e2e; color: #a78bfa; font-size: 0.7rem; padding: 3px 10px; border-radius: 20px; font-weight: 600; letter-spacing: 0.05em; }

  .hero { text-align: center; padding: 60px 20px 40px; }
  .hero h1 { font-size: clamp(2rem, 5vw, 3.2rem); font-weight: 900; line-height: 1.15; margin-bottom: 16px; }
  .hero h1 span { background: linear-gradient(135deg, #a78bfa, #ec4899, #f97316); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
  .hero p { color: #94a3b8; font-size: 1.1rem; max-width: 520px; margin: 0 auto; }

  .upload-zone { max-width: 680px; margin: 40px auto 0; padding: 0 20px; }
  .drop-area {
    border: 2px dashed #2d2d4e;
    border-radius: 20px;
    padding: 50px 30px;
    text-align: center;
    cursor: pointer;
    transition: all 0.3s;
    background: #0f0f1a;
    position: relative;
  }
  .drop-area:hover, .drop-area.dragover { border-color: #a78bfa; background: #13132a; }
  .drop-icon { font-size: 3rem; margin-bottom: 16px; }
  .drop-area h3 { font-size: 1.1rem; font-weight: 700; margin-bottom: 8px; }
  .drop-area p { color: #64748b; font-size: 0.9rem; }
  .drop-area input[type=file] { position: absolute; inset: 0; opacity: 0; cursor: pointer; }

  .settings { margin-top: 24px; display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
  .setting-group label { display: block; font-size: 0.8rem; color: #94a3b8; font-weight: 600; margin-bottom: 8px; text-transform: uppercase; letter-spacing: 0.05em; }
  .setting-group select, .setting-group input[type=range] {
    width: 100%; background: #0f0f1a; border: 1px solid #2d2d4e; border-radius: 10px;
    color: #e2e8f0; padding: 10px 14px; font-size: 0.9rem; outline: none;
  }
  .setting-group select:focus { border-color: #a78bfa; }
  .range-val { color: #a78bfa; font-weight: 700; }

  .btn-upload {
    width: 100%; margin-top: 24px; padding: 16px;
    background: linear-gradient(135deg, #7c3aed, #db2777);
    border: none; border-radius: 14px; color: white;
    font-size: 1rem; font-weight: 700; cursor: pointer;
    transition: opacity 0.2s, transform 0.1s;
    letter-spacing: 0.02em;
  }
  .btn-upload:hover { opacity: 0.9; transform: translateY(-1px); }
  .btn-upload:disabled { opacity: 0.5; cursor: not-allowed; transform: none; }

  .progress-section { max-width: 680px; margin: 32px auto 0; padding: 0 20px; display: none; }
  .progress-card { background: #0f0f1a; border: 1px solid #1e1e2e; border-radius: 20px; padding: 28px; }
  .progress-card h3 { font-size: 1rem; font-weight: 700; margin-bottom: 20px; }
  .steps { display: flex; flex-direction: column; gap: 14px; }
  .step { display: flex; align-items: center; gap: 14px; }
  .step-icon { width: 36px; height: 36px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 1rem; flex-shrink: 0; background: #1e1e2e; }
  .step-icon.done { background: #14532d; }
  .step-icon.active { background: #3b1d8a; animation: pulse 1.5s infinite; }
  .step-icon.error { background: #7f1d1d; }
  @keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.5} }
  .step-text { font-size: 0.9rem; color: #94a3b8; }
  .step-text.active { color: #e2e8f0; font-weight: 600; }
  .step-text.done { color: #4ade80; }

  .progress-bar-wrap { margin-top: 20px; background: #1e1e2e; border-radius: 99px; height: 6px; overflow: hidden; }
  .progress-bar-fill { height: 100%; background: linear-gradient(90deg, #7c3aed, #db2777); border-radius: 99px; transition: width 0.5s; width: 0%; }

  .results-section { max-width: 1000px; margin: 40px auto 60px; padding: 0 20px; display: none; }
  .results-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px; flex-wrap: wrap; gap: 12px; }
  .results-header h2 { font-size: 1.5rem; font-weight: 800; }
  .btn-new { background: #1e1e2e; border: 1px solid #2d2d4e; color: #e2e8f0; padding: 10px 20px; border-radius: 10px; cursor: pointer; font-size: 0.9rem; font-weight: 600; }
  .btn-new:hover { border-color: #a78bfa; }

  .clips-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 20px; }
  .clip-card { background: #0f0f1a; border: 1px solid #1e1e2e; border-radius: 16px; overflow: hidden; transition: border-color 0.2s, transform 0.2s; }
  .clip-card:hover { border-color: #a78bfa; transform: translateY(-2px); }
  .clip-preview { position: relative; background: #000; aspect-ratio: 9/16; display: flex; align-items: center; justify-content: center; max-height: 320px; }
  .clip-preview video { width: 100%; height: 100%; object-fit: contain; }
  .virality-badge {
    position: absolute; top: 10px; right: 10px;
    background: rgba(0,0,0,0.75); backdrop-filter: blur(8px);
    border-radius: 20px; padding: 4px 10px;
    font-size: 0.75rem; font-weight: 800;
    display: flex; align-items: center; gap: 4px;
  }
  .virality-badge.high { color: #4ade80; border: 1px solid #166534; }
  .virality-badge.mid { color: #fbbf24; border: 1px solid #78350f; }
  .virality-badge.low { color: #f87171; border: 1px solid #7f1d1d; }
  .clip-info { padding: 16px; }
  .clip-info h4 { font-size: 0.85rem; font-weight: 700; margin-bottom: 6px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
  .clip-meta { display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 12px; }
  .tag { background: #1e1e2e; color: #94a3b8; font-size: 0.7rem; padding: 3px 8px; border-radius: 6px; }
  .clip-reason { font-size: 0.78rem; color: #64748b; line-height: 1.5; margin-bottom: 14px; }
  .btn-download {
    width: 100%; padding: 10px; background: linear-gradient(135deg, #7c3aed, #db2777);
    border: none; border-radius: 10px; color: white; font-size: 0.85rem;
    font-weight: 700; cursor: pointer; transition: opacity 0.2s;
  }
  .btn-download:hover { opacity: 0.85; }

  .error-msg { color: #f87171; text-align: center; margin-top: 16px; font-size: 0.9rem; display: none; }
  .file-chosen { margin-top: 12px; color: #a78bfa; font-size: 0.85rem; text-align: center; }
</style>
</head>
<body>

<nav class="nav">
  <div class="logo">ClipAI</div>
  <span class="nav-tag">FREE · NO WATERMARK</span>
</nav>

<div class="hero">
  <h1>Turn Long Videos Into<br/><span>Viral Short Clips</span></h1>
  <p>AI picks the best moments, adds captions, reframes to 9:16, and scores each clip's viral potential.</p>
</div>

<div class="upload-zone">
  <div class="drop-area" id="dropArea">
    <div class="drop-icon">🎬</div>
    <h3>Drop your video here</h3>
    <p>MP4, MOV, MKV, AVI — up to 500MB</p>
    <input type="file" id="fileInput" accept="video/*"/>
  </div>
  <div class="file-chosen" id="fileChosen"></div>

  <div class="settings">
    <div class="setting-group">
      <label>Number of clips</label>
      <select id="numClips">
        <option value="3">3 clips</option>
        <option value="5" selected>5 clips</option>
        <option value="8">8 clips</option>
        <option value="10">10 clips</option>
      </select>
    </div>
    <div class="setting-group">
      <label>Clip length (seconds)</label>
      <select id="clipLen">
        <option value="30">30s</option>
        <option value="45">45s</option>
        <option value="60" selected>60s</option>
        <option value="90">90s</option>
      </select>
    </div>
  </div>

  <button class="btn-upload" id="uploadBtn" onclick="startProcess()" disabled>
    ✨ Generate Clips
  </button>
  <div class="error-msg" id="errorMsg"></div>
</div>

<div class="progress-section" id="progressSection">
  <div class="progress-card">
    <h3>⚙️ Processing your video...</h3>
    <div class="steps" id="stepsContainer"></div>
    <div class="progress-bar-wrap">
      <div class="progress-bar-fill" id="progressBar"></div>
    </div>
  </div>
</div>

<div class="results-section" id="resultsSection">
  <div class="results-header">
    <h2>🎉 Your Clips Are Ready!</h2>
    <button class="btn-new" onclick="resetApp()">+ New Video</button>
  </div>
  <div class="clips-grid" id="clipsGrid"></div>
</div>

<script>
const fileInput = document.getElementById('fileInput');
const dropArea = document.getElementById('dropArea');
const uploadBtn = document.getElementById('uploadBtn');
const fileChosen = document.getElementById('fileChosen');

fileInput.addEventListener('change', () => {
  if (fileInput.files[0]) {
    fileChosen.textContent = '✅ ' + fileInput.files[0].name;
    uploadBtn.disabled = false;
  }
});

['dragover','dragleave','drop'].forEach(e => {
  dropArea.addEventListener(e, ev => {
    ev.preventDefault();
    if (e === 'dragover') dropArea.classList.add('dragover');
    else dropArea.classList.remove('dragover');
    if (e === 'drop' && ev.dataTransfer.files[0]) {
      fileInput.files = ev.dataTransfer.files;
      fileChosen.textContent = '✅ ' + ev.dataTransfer.files[0].name;
      uploadBtn.disabled = false;
    }
  });
});

let currentJobId = null;
let pollInterval = null;

const STEPS = [
  { key: 'upload', label: 'Uploading video', icon: '📤' },
  { key: 'audio', label: 'Extracting audio', icon: '🎵' },
  { key: 'transcribe', label: 'Transcribing with AI', icon: '📝' },
  { key: 'analyze', label: 'Finding best moments', icon: '🧠' },
  { key: 'clips', label: 'Cutting & reframing clips', icon: '✂️' },
  { key: 'captions', label: 'Burning in captions', icon: '💬' },
  { key: 'done', label: 'All done!', icon: '🎉' },
];

function renderSteps(currentStep, errorStep) {
  const container = document.getElementById('stepsContainer');
  const currentIdx = STEPS.findIndex(s => s.key === currentStep);
  container.innerHTML = STEPS.map((step, i) => {
    let iconClass = '', textClass = '', icon = step.icon;
    if (step.key === errorStep) { iconClass = 'error'; icon = '❌'; textClass = ''; }
    else if (i < currentIdx) { iconClass = 'done'; icon = '✅'; textClass = 'done'; }
    else if (i === currentIdx) { iconClass = 'active'; textClass = 'active'; }
    return `<div class="step">
      <div class="step-icon ${iconClass}">${icon}</div>
      <div class="step-text ${textClass}">${step.label}</div>
    </div>`;
  }).join('');
  const pct = Math.min(100, Math.round((currentIdx / (STEPS.length - 1)) * 100));
  document.getElementById('progressBar').style.width = pct + '%';
}

async function startProcess() {
  const file = fileInput.files[0];
  if (!file) return;
  uploadBtn.disabled = true;
  document.getElementById('errorMsg').style.display = 'none';

  document.getElementById('progressSection').style.display = 'block';
  document.getElementById('resultsSection').style.display = 'none';
  renderSteps('upload', null);
  document.getElementById('progressSection').scrollIntoView({ behavior: 'smooth' });

  const formData = new FormData();
  formData.append('video', file);
  formData.append('num_clips', document.getElementById('numClips').value);
  formData.append('clip_length', document.getElementById('clipLen').value);

  try {
    const res = await fetch('/upload', { method: 'POST', body: formData });
    const data = await res.json();
    if (!data.job_id) throw new Error(data.error || 'Upload failed');
    currentJobId = data.job_id;
    renderSteps('audio', null);
    pollInterval = setInterval(pollStatus, 2500);
  } catch (e) {
    showError(e.message);
  }
}

async function pollStatus() {
  try {
    const res = await fetch('/status/' + currentJobId);
    const data = await res.json();
    renderSteps(data.step, data.error_step || null);
    if (data.step === 'done') {
      clearInterval(pollInterval);
      showResults(data.clips);
    } else if (data.status === 'error') {
      clearInterval(pollInterval);
      showError(data.message || 'Something went wrong');
    }
  } catch(e) {}
}

function showResults(clips) {
  document.getElementById('progressSection').style.display = 'none';
  document.getElementById('resultsSection').style.display = 'block';
  const grid = document.getElementById('clipsGrid');
  grid.innerHTML = clips.map((clip, i) => {
    const score = clip.virality_score;
    const badgeClass = score >= 75 ? 'high' : score >= 50 ? 'mid' : 'low';
    const emoji = score >= 75 ? '🔥' : score >= 50 ? '⚡' : '📊';
    return `<div class="clip-card">
      <div class="clip-preview">
        <video controls preload="metadata" src="/clip/${currentJobId}/${clip.filename}"></video>
        <div class="virality-badge ${badgeClass}">${emoji} ${score}/100</div>
      </div>
      <div class="clip-info">
        <h4>${clip.title}</h4>
        <div class="clip-meta">
          <span class="tag">⏱ ${clip.duration}s</span>
          <span class="tag">📐 9:16</span>
          <span class="tag">💬 Captions</span>
        </div>
        <div class="clip-reason">${clip.reason}</div>
        <button class="btn-download" onclick="downloadClip('${clip.filename}')">⬇️ Download</button>
      </div>
    </div>`;
  }).join('');
  document.getElementById('resultsSection').scrollIntoView({ behavior: 'smooth' });
}

function downloadClip(filename) {
  const a = document.createElement('a');
  a.href = '/clip/' + currentJobId + '/' + filename;
  a.download = filename;
  a.click();
}

function showError(msg) {
  uploadBtn.disabled = false;
  document.getElementById('progressSection').style.display = 'none';
  const el = document.getElementById('errorMsg');
  el.textContent = '❌ ' + msg;
  el.style.display = 'block';
}

function resetApp() {
  document.getElementById('resultsSection').style.display = 'none';
  fileInput.value = '';
  fileChosen.textContent = '';
  uploadBtn.disabled = true;
  window.scrollTo({ top: 0, behavior: 'smooth' });
}
</script>
</body>
</html>"""


@app.route("/")
def index():
    return HTML


@app.route("/upload", methods=["POST"])
def upload():
    if "video" not in request.files:
        return jsonify({"error": "No video file"}), 400
    file = request.files["video"]
    num_clips = int(request.form.get("num_clips", 5))
    clip_length = int(request.form.get("clip_length", 60))

    job_id = str(uuid.uuid4())[:8]
    job_dir = os.path.join(OUTPUT_FOLDER, job_id)
    os.makedirs(job_dir, exist_ok=True)

    ext = os.path.splitext(file.filename)[1] or ".mp4"
    video_path = os.path.join(UPLOAD_FOLDER, f"{job_id}{ext}")
    file.save(video_path)

    jobs[job_id] = {"status": "running", "step": "audio", "clips": []}
    thread = threading.Thread(target=process_video, args=(job_id, video_path, job_dir, num_clips, clip_length))
    thread.daemon = True
    thread.start()

    return jsonify({"job_id": job_id})


@app.route("/status/<job_id>")
def status(job_id):
    if job_id not in jobs:
        return jsonify({"status": "error", "message": "Job not found"}), 404
    return jsonify(jobs[job_id])


@app.route("/clip/<job_id>/<filename>")
def serve_clip(job_id, filename):
    job_dir = os.path.join(OUTPUT_FOLDER, job_id)
    return send_from_directory(job_dir, filename)


def get_video_duration(video_path):
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", video_path],
        capture_output=True, text=True
    )
    return float(result.stdout.strip())


def extract_audio(video_path, audio_path):
    subprocess.run([
        "ffmpeg", "-i", video_path, "-vn", "-acodec", "pcm_s16le",
        "-ar", "16000", "-ac", "1", audio_path, "-y", "-loglevel", "error"
    ], check=True)


def transcribe_audio(audio_path):
    """Use ffmpeg + a simple approach to get transcript via whisper CLI if available, else use chunked approach"""
    # Try whisper CLI
    result = subprocess.run(["which", "whisper"], capture_output=True, text=True)
    if result.returncode == 0:
        out_dir = os.path.dirname(audio_path)
        subprocess.run([
            "whisper", audio_path, "--model", "tiny", "--output_format", "json",
            "--output_dir", out_dir, "--language", "en", "--verbose", "False"
        ], capture_output=True, text=True)
        json_path = audio_path.replace(".wav", ".json")
        if os.path.exists(json_path):
            with open(json_path) as f:
                data = json.load(f)
            segments = [{"start": s["start"], "end": s["end"], "text": s["text"].strip()} for s in data.get("segments", [])]
            return segments

    # Fallback: use Claude to create mock timestamps based on duration
    return None


def analyze_with_claude(transcript_text, duration, num_clips, clip_length, job_id):
    """Ask Claude to pick the best clip moments and score them"""
    jobs[job_id]["step"] = "analyze"

    if transcript_text:
        prompt = f"""You are an expert viral content strategist. Analyze this video transcript and find the {num_clips} best moments for short viral clips.

Video duration: {duration:.0f} seconds
Desired clip length: ~{clip_length} seconds each

TRANSCRIPT (with timestamps):
{transcript_text}

For each clip, pick the single most engaging, surprising, funny, or valuable segment. Clips should:
- Start with a strong hook (don't start mid-sentence)
- Contain a complete thought or story arc
- Be between {max(15, clip_length-15)} and {clip_length+15} seconds long
- Not overlap with each other

Return ONLY a JSON array like this (no markdown, no extra text):
[
  {{
    "title": "Short catchy title for this clip",
    "start": 12.5,
    "end": 67.3,
    "virality_score": 87,
    "reason": "One sentence explaining why this moment is viral-worthy"
  }}
]

Virality score: 0-100. 80+ = highly viral potential (strong hook, surprising, emotional, or actionable). 60-79 = good content. Below 60 = average."""
    else:
        # No transcript - distribute clips evenly and let Claude score them conceptually
        prompt = f"""A video is {duration:.0f} seconds long. Generate {num_clips} clip suggestions spread throughout the video, each ~{clip_length} seconds long.

Return ONLY a JSON array (no markdown):
[
  {{
    "title": "Clip [N]",
    "start": <number>,
    "end": <number>,
    "virality_score": <50-85>,
    "reason": "This segment captures a key moment in the video."
  }}
]

Space them out evenly. Each clip should be {clip_length} seconds. Don't go past {duration:.0f} seconds."""

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}]
    )

    text = response.content[0].text.strip()
    # Strip markdown if present
    text = re.sub(r"```json\s*|\s*```", "", text).strip()
    clips_data = json.loads(text)
    return clips_data


def cut_clip_with_captions(video_path, start, end, output_path, caption_segments):
    """Cut clip, reframe to 9:16, and burn captions"""
    duration = end - start

    # Get video dimensions
    probe = subprocess.run([
        "ffprobe", "-v", "error", "-select_streams", "v:0",
        "-show_entries", "stream=width,height",
        "-of", "csv=p=0", video_path
    ], capture_output=True, text=True)
    dims = probe.stdout.s
