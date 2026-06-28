import os
import json
import subprocess
import threading
import uuid
import re
from flask import Flask, request, jsonify, send_from_directory

app = Flask(__name__)

UPLOAD_FOLDER = "/tmp/uploads"
OUTPUT_FOLDER = "/tmp/outputs"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

jobs = {}

# Get ffmpeg/ffprobe path from imageio-ffmpeg
def get_ffmpeg_exe():
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except:
        return "ffmpeg"

def get_ffprobe_exe():
    # imageio_ffmpeg puts ffmpeg in a known path, ffprobe is next to it
    try:
        import imageio_ffmpeg
        ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()
        ffprobe_path = ffmpeg_path.replace("ffmpeg", "ffprobe")
        if os.path.exists(ffprobe_path):
            return ffprobe_path
        # Try system
        r = subprocess.run(["which", "ffprobe"], capture_output=True, text=True)
        if r.returncode == 0:
            return r.stdout.strip()
        # Use ffmpeg to get info instead
        return None
    except:
        return None

HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<title>ClipAI — Viral Short Clips</title>
<style>
* { box-sizing: border-box; margin: 0; padding: 0; }
body { background: #0a0a0f; color: #e2e8f0; font-family: system-ui, sans-serif; min-height: 100vh; }
.nav { display: flex; align-items: center; padding: 20px; border-bottom: 1px solid #1e1e2e; }
.logo { font-size: 1.4rem; font-weight: 800; color: #a78bfa; }
.tag { margin-left: 12px; background: #1e1e2e; color: #a78bfa; font-size: 0.7rem; padding: 3px 10px; border-radius: 20px; }
.hero { text-align: center; padding: 40px 20px 24px; }
.hero h1 { font-size: 1.9rem; font-weight: 900; margin-bottom: 10px; }
.hero h1 span { color: #a78bfa; }
.hero p { color: #94a3b8; font-size: 0.9rem; }
.box { max-width: 600px; margin: 24px auto; padding: 0 20px; }
.drop { border: 2px dashed #2d2d4e; border-radius: 16px; padding: 36px 20px; text-align: center; cursor: pointer; background: #0f0f1a; position: relative; }
.drop:hover { border-color: #a78bfa; }
.drop input { position: absolute; inset: 0; opacity: 0; cursor: pointer; width: 100%; height: 100%; }
.drop h3 { margin: 10px 0 6px; }
.drop p { color: #64748b; font-size: 0.85rem; }
.row { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; margin-top: 18px; }
label { display: block; font-size: 0.8rem; color: #94a3b8; margin-bottom: 6px; font-weight: 600; }
select { width: 100%; background: #0f0f1a; border: 1px solid #2d2d4e; border-radius: 8px; color: #e2e8f0; padding: 10px; font-size: 0.9rem; }
.btn { width: 100%; margin-top: 18px; padding: 14px; background: #7c3aed; border: none; border-radius: 12px; color: white; font-size: 1rem; font-weight: 700; cursor: pointer; }
.btn:disabled { opacity: 0.4; cursor: not-allowed; }
.chosen { margin-top: 10px; color: #a78bfa; font-size: 0.85rem; text-align: center; }
.progress { max-width: 600px; margin: 20px auto; padding: 0 20px; display: none; }
.pcard { background: #0f0f1a; border: 1px solid #1e1e2e; border-radius: 16px; padding: 24px; }
.step { display: flex; align-items: center; gap: 12px; margin-bottom: 12px; }
.sicon { width: 32px; height: 32px; border-radius: 50%; background: #1e1e2e; display: flex; align-items: center; justify-content: center; flex-shrink: 0; font-size: 0.9rem; }
.sicon.active { background: #3b1d8a; }
.sicon.done { background: #14532d; }
.stext { font-size: 0.9rem; color: #64748b; }
.stext.active { color: white; font-weight: 600; }
.stext.done { color: #4ade80; }
.bar { background: #1e1e2e; border-radius: 99px; height: 6px; margin-top: 16px; }
.fill { height: 100%; background: #7c3aed; border-radius: 99px; transition: width 0.5s; width: 0; }
.results { max-width: 600px; margin: 24px auto 60px; padding: 0 20px; display: none; }
.rhead { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.rhead h2 { font-size: 1.2rem; font-weight: 800; }
.nbtn { background: #1e1e2e; border: 1px solid #2d2d4e; color: #e2e8f0; padding: 8px 16px; border-radius: 8px; cursor: pointer; font-size: 0.85rem; }
.clip-item { background: #0f0f1a; border: 1px solid #1e1e2e; border-radius: 14px; margin-bottom: 16px; overflow: hidden; }
.clip-top { padding: 14px 14px 8px; }
.clip-title { font-size: 0.9rem; font-weight: 700; margin-bottom: 8px; }
.clip-meta { display: flex; gap: 8px; margin-bottom: 8px; flex-wrap: wrap; }
.badge { padding: 3px 8px; border-radius: 6px; font-size: 0.72rem; font-weight: 700; }
.badge.high { background: #14532d; color: #4ade80; }
.badge.mid { background: #78350f; color: #fbbf24; }
.badge.low { background: #7f1d1d; color: #f87171; }
.tag2 { background: #1e1e2e; color: #94a3b8; padding: 3px 8px; border-radius: 6px; font-size: 0.72rem; }
.clip-reason { font-size: 0.78rem; color: #64748b; line-height: 1.5; padding: 0 14px 12px; }
.dl-btn { display: block; width: 100%; padding: 14px; background: linear-gradient(135deg, #7c3aed, #db2777); border: none; color: white; font-size: 0.95rem; font-weight: 700; cursor: pointer; text-align: center; text-decoration: none; }
.err { color: #f87171; text-align: center; margin-top: 12px; display: none; font-size: 0.85rem; padding: 12px; background: #1a0000; border-radius: 8px; border: 1px solid #7f1d1d; }
</style>
</head>
<body>
<nav class="nav"><div class="logo">ClipAI</div><span class="tag">FREE · NO WATERMARK</span></nav>
<div class="hero">
  <h1>Turn Long Videos Into<br/><span>Viral Clips</span></h1>
  <p>AI finds best moments · 9:16 reframe · Virality score</p>
</div>
<div class="box">
  <div class="drop" id="drop">
    <div style="font-size:2.5rem">🎬</div>
    <h3>Tap to upload video</h3>
    <p>MP4, MOV, MKV — up to 500MB</p>
    <input type="file" id="file" accept="video/*"/>
  </div>
  <div class="chosen" id="chosen"></div>
  <div class="row">
    <div><label>Number of clips</label>
    <select id="num"><option value="3">3 clips</option><option value="5" selected>5 clips</option><option value="8">8 clips</option></select></div>
    <div><label>Clip length</label>
    <select id="len"><option value="30">30s</option><option value="45">45s</option><option value="60" selected>60s</option><option value="90">90s</option></select></div>
  </div>
  <button class="btn" id="btn" onclick="start()" disabled>✨ Generate Clips</button>
  <div class="err" id="err"></div>
</div>
<div class="progress" id="prog">
  <div class="pcard">
    <h3 style="margin-bottom:16px">⚙️ Processing your video...</h3>
    <div id="steps"></div>
    <div class="bar"><div class="fill" id="fill"></div></div>
  </div>
</div>
<div class="results" id="results">
  <div class="rhead"><h2>🎉 Your Clips Are Ready!</h2><button class="nbtn" onclick="resetApp()">+ New</button></div>
  <div id="cliplist"></div>
</div>
<script>
const STEPS=[
  {key:'upload',label:'Uploading video',icon:'📤'},
  {key:'audio',label:'Extracting audio',icon:'🎵'},
  {key:'transcribe',label:'Analyzing video',icon:'🧠'},
  {key:'analyze',label:'Finding best moments',icon:'🎯'},
  {key:'clips',label:'Cutting clips',icon:'✂️'},
  {key:'captions',label:'Finishing up',icon:'💬'},
  {key:'done',label:'Done!',icon:'🎉'},
];
let jobId=null,timer=null;
document.getElementById('file').onchange=e=>{
  if(e.target.files[0]){document.getElementById('chosen').textContent='✅ '+e.target.files[0].name;document.getElementById('btn').disabled=false;}
};
function renderSteps(cur,errStep){
  const idx=STEPS.findIndex(s=>s.key===cur);
  document.getElementById('steps').innerHTML=STEPS.map((s,i)=>{
    let ic='',tc='',icon=s.icon;
    if(s.key===errStep){ic='error';icon='❌';}
    else if(i<idx){ic='done';icon='✅';tc='done';}
    else if(i===idx){ic='active';tc='active';}
    return `<div class="step"><div class="sicon ${ic}">${icon}</div><div class="stext ${tc}">${s.label}</div></div>`;
  }).join('');
  document.getElementById('fill').style.width=Math.min(100,Math.round(idx/(STEPS.length-1)*100))+'%';
}
async function start(){
  const f=document.getElementById('file').files[0];if(!f)return;
  document.getElementById('btn').disabled=true;
  document.getElementById('err').style.display='none';
  document.getElementById('prog').style.display='block';
  document.getElementById('results').style.display='none';
  renderSteps('upload',null);
  document.getElementById('prog').scrollIntoView({behavior:'smooth'});
  const fd=new FormData();
  fd.append('video',f);fd.append('num_clips',document.getElementById('num').value);fd.append('clip_length',document.getElementById('len').value);
  try{
    const r=await fetch('/upload',{method:'POST',body:fd});
    const d=await r.json();
    if(!d.job_id)throw new Error(d.error||'Upload failed');
    jobId=d.job_id;renderSteps('audio',null);
    timer=setInterval(poll,3000);
  }catch(e){showErr(e.message);}
}
async function poll(){
  try{
    const r=await fetch('/status/'+jobId);const d=await r.json();
    renderSteps(d.step,d.error_step||null);
    if(d.step==='done'&&d.clips&&d.clips.length>0){clearInterval(timer);showResults(d.clips);}
    else if(d.status==='error'){clearInterval(timer);showErr(d.message||'Error. Please try again.');}
  }catch(e){}
}
function showResults(clips){
  document.getElementById('prog').style.display='none';
  document.getElementById('results').style.display='block';
  document.getElementById('cliplist').innerHTML=clips.map((c,i)=>{
    const s=c.virality_score||70;
    const bc=s>=75?'high':s>=50?'mid':'low';
    const em=s>=75?'🔥':s>=50?'⚡':'📊';
    return `<div class="clip-item"><div class="clip-top">
      <div class="clip-title">${i+1}. ${c.title}</div>
      <div class="clip-meta"><span class="badge ${bc}">${em} ${s}/100 Virality</span><span class="tag2">⏱ ${c.duration}s</span><span class="tag2">📐 9:16</span></div>
    </div><div class="clip-reason">${c.reason}</div>
    <a class="dl-btn" href="/download/${jobId}/${c.filename}" download="${c.filename}">⬇️ Download Clip ${i+1}</a>
    </div>`;
  }).join('');
  document.getElementById('results').scrollIntoView({behavior:'smooth'});
}
function showErr(m){document.getElementById('btn').disabled=false;document.getElementById('prog').style.display='none';const e=document.getElementById('err');e.textContent='❌ '+m;e.style.display='block';}
function resetApp(){document.getElementById('results').style.display='none';document.getElementById('file').value='';document.getElementById('chosen').textContent='';document.getElementById('btn').disabled=true;window.scrollTo({top:0,behavior:'smooth'});}
</script>
</body></html>"""

@app.route("/")
def index():
    return HTML

@app.route("/health")
def health():
    ffmpeg = get_ffmpeg_exe()
    return jsonify({"status": "ok", "ffmpeg": ffmpeg})

@app.route("/upload", methods=["POST"])
def upload():
    try:
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
        t = threading.Thread(target=process_video, args=(job_id, video_path, job_dir, num_clips, clip_length))
        t.daemon = True
        t.start()
        return jsonify({"job_id": job_id})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/status/<job_id>")
def status(job_id):
    if job_id not in jobs:
        return jsonify({"status": "error", "message": "Job not found"}), 404
    return jsonify(jobs[job_id])

@app.route("/download/<job_id>/<filename>")
def download_clip(job_id, filename):
    job_dir = os.path.join(OUTPUT_FOLDER, job_id)
    if not os.path.exists(os.path.join(job_dir, filename)):
        return jsonify({"error": "File not found — please regenerate"}), 404
    return send_from_directory(job_dir, filename, as_attachment=True, download_name=filename)

def get_duration(path):
    ffmpeg_exe = get_ffmpeg_exe()
    ffprobe_exe = get_ffprobe_exe()
    if ffprobe_exe:
        r = subprocess.run([ffprobe_exe,"-v","error","-show_entries","format=duration",
                            "-of","default=noprint_wrappers=1:nokey=1",path],
                           capture_output=True, text=True)
        return float(r.stdout.strip())
    else:
        # Use ffmpeg to get duration
        r = subprocess.run([ffmpeg_exe,"-i",path], capture_output=True, text=True)
        output = r.stderr
        match = re.search(r"Duration: (\d+):(\d+):(\d+\.?\d*)", output)
        if match:
            h,m,s = float(match.group(1)),float(match.group(2)),float(match.group(3))
            return h*3600 + m*60 + s
        raise Exception("Could not get video duration")

def get_dimensions(path):
    ffmpeg_exe = get_ffmpeg_exe()
    ffprobe_exe = get_ffprobe_exe()
    if ffprobe_exe:
        r = subprocess.run([ffprobe_exe,"-v","error","-select_streams","v:0",
                            "-show_entries","stream=width,height","-of","csv=p=0",path],
                           capture_output=True, text=True)
        dims = r.stdout.strip().split(",")
        return int(dims[0]), int(dims[1])
    else:
        r = subprocess.run([ffmpeg_exe,"-i",path], capture_output=True, text=True)
        match = re.search(r"(\d{2,4})x(\d{2,4})", r.stderr)
        if match:
            return int(match.group(1)), int(match.group(2))
        return 1920, 1080

def extract_audio(video, audio):
    ffmpeg_exe = get_ffmpeg_exe()
    subprocess.run([ffmpeg_exe,"-i",video,"-vn","-acodec","pcm_s16le",
                    "-ar","16000","-ac","1",audio,"-y","-loglevel","error"], check=True)

def analyze_with_claude(duration, num_clips, clip_length, job_id):
    jobs[job_id]["step"] = "analyze"
    api_key = os.environ.get("ANTHROPIC_API_KEY","")
    if not api_key:
        raise Exception("ANTHROPIC_API_KEY not set in Railway Variables")
    import urllib.request as ur
    prompt = f"""A video is {duration:.0f} seconds long. Generate exactly {num_clips} short clip suggestions, each ~{clip_length} seconds. Space them evenly.

Return ONLY a valid JSON array, no markdown:
[{{"title":"Catchy title","start":0,"end":{clip_length},"virality_score":80,"reason":"Why this clip is engaging"}}]

Rules: never exceed {duration:.0f}s total, no overlaps, each clip ~{clip_length}s."""

    data = json.dumps({"model":"claude-sonnet-4-6","max_tokens":1000,
                       "messages":[{"role":"user","content":prompt}]}).encode()
    req = ur.Request("https://api.anthropic.com/v1/messages", data=data,
                     headers={"Content-Type":"application/json","x-api-key":api_key,
                               "anthropic-version":"2023-06-01"})
    with ur.urlopen(req, timeout=30) as resp:
        result = json.loads(resp.read())
    text = result["content"][0]["text"].strip()
    text = re.sub(r"```json\s*|\s*```","",text).strip()
    return json.loads(text)

def cut_clip(video, start, end, output):
    ffmpeg_exe = get_ffmpeg_exe()
    duration = end - start
    w, h = get_dimensions(video)
    if w/h > 9/16:
        nw = int(h*9/16); x = (w-nw)//2
        crop = f"crop={nw}:{h}:{x}:0,scale=1080:1920"
    else:
        nh = int(w*16/9); y = max(0,(h-nh)//2)
        crop = f"crop={w}:{nh}:0:{y},scale=1080:1920"
    subprocess.run([ffmpeg_exe,"-ss",str(start),"-i",video,"-t",str(duration),
                    "-vf",crop,"-c:v","libx264","-preset","fast","-crf","23",
                    "-c:a","aac","-b:a","128k","-movflags","+faststart",
                    output,"-y","-loglevel","error"], check=True)

def process_video(job_id, video_path, job_dir, num_clips, clip_length):
    try:
        duration = get_duration(video_path)
        jobs[job_id]["step"] = "audio"
        audio_path = os.path.join(job_dir, "audio.wav")
        extract_audio(video_path, audio_path)
        jobs[job_id]["step"] = "transcribe"
        clips_data = analyze_with_claude(duration, num_clips, clip_length, job_id)
        jobs[job_id]["step"] = "clips"
        final = []
        for i, c in enumerate(clips_data[:num_clips]):
            start = max(0, float(c["start"]))
            end = min(duration, float(c["end"]))
            if end-start < 5: end = min(duration, start+clip_length)
            fn = f"clip_{i+1:02d}_score{c.get('virality_score',70)}.mp4"
            cut_clip(video_path, start, end, os.path.join(job_dir, fn))
            jobs[job_id]["step"] = "captions"
            final.append({"filename":fn,"title":c.get("title",f"Clip {i+1}"),
                          "virality_score":c.get("virality_score",70),
                          "reason":c.get("reason",""),"duration":round(end-start)})
        final.sort(key=lambda x: x["virality_score"], reverse=True)
        jobs[job_id].update({"status":"done","step":"done","clips":final})
        try: os.remove(audio_path); os.remove(video_path)
        except: pass
    except Exception as e:
        jobs[job_id].update({"status":"error","step":"done",
                              "error_step":jobs[job_id].get("step","clips"),"message":str(e)})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    print(f"Starting ClipAI on port {port}")
    ffmpeg = get_ffmpeg_exe()
    print(f"FFmpeg path: {ffmpeg}")
    app.run(debug=False, host="0.0.0.0", port=port)
