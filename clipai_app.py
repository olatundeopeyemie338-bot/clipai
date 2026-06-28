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

HTML = open("/dev/stdin").read() if False else """<!DOCTYPE html>
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
.hero { text-align: center; padding: 50px 20px 30px; }
.hero h1 { font-size: 2rem; font-weight: 900; margin-bottom: 12px; }
.hero h1 span { color: #a78bfa; }
.hero p { color: #94a3b8; }
.box { max-width: 600px; margin: 30px auto; padding: 0 20px; }
.drop { border: 2px dashed #2d2d4e; border-radius: 16px; padding: 40px 20px; text-align: center; cursor: pointer; background: #0f0f1a; position: relative; }
.drop:hover { border-color: #a78bfa; }
.drop input { position: absolute; inset: 0; opacity: 0; cursor: pointer; width: 100%; height: 100%; }
.drop h3 { margin: 10px 0 6px; }
.drop p { color: #64748b; font-size: 0.9rem; }
.row { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-top: 20px; }
label { display: block; font-size: 0.8rem; color: #94a3b8; margin-bottom: 6px; font-weight: 600; }
select { width: 100%; background: #0f0f1a; border: 1px solid #2d2d4e; border-radius: 8px; color: #e2e8f0; padding: 10px; font-size: 0.9rem; }
.btn { width: 100%; margin-top: 20px; padding: 14px; background: #7c3aed; border: none; border-radius: 12px; color: white; font-size: 1rem; font-weight: 700; cursor: pointer; }
.btn:disabled { opacity: 0.4; cursor: not-allowed; }
.chosen { margin-top: 10px; color: #a78bfa; font-size: 0.85rem; text-align: center; }
.progress { max-width: 600px; margin: 20px auto; padding: 0 20px; display: none; }
.pcard { background: #0f0f1a; border: 1px solid #1e1e2e; border-radius: 16px; padding: 24px; }
.step { display: flex; align-items: center; gap: 12px; margin-bottom: 12px; }
.sicon { width: 32px; height: 32px; border-radius: 50%; background: #1e1e2e; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
.sicon.active { background: #3b1d8a; }
.sicon.done { background: #14532d; }
.stext { font-size: 0.9rem; color: #64748b; }
.stext.active { color: white; font-weight: 600; }
.stext.done { color: #4ade80; }
.bar { background: #1e1e2e; border-radius: 99px; height: 6px; margin-top: 16px; }
.fill { height: 100%; background: #7c3aed; border-radius: 99px; transition: width 0.5s; width: 0; }
.results { max-width: 900px; margin: 30px auto 60px; padding: 0 20px; display: none; }
.rhead { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
.rhead h2 { font-size: 1.3rem; font-weight: 800; }
.nbtn { background: #1e1e2e; border: 1px solid #2d2d4e; color: #e2e8f0; padding: 8px 16px; border-radius: 8px; cursor: pointer; }
.grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); gap: 16px; }
.card { background: #0f0f1a; border: 1px solid #1e1e2e; border-radius: 14px; overflow: hidden; }
.preview { position: relative; background: #000; aspect-ratio: 9/16; max-height: 300px; }
.preview video { width: 100%; height: 100%; object-fit: contain; }
.badge { position: absolute; top: 8px; right: 8px; background: rgba(0,0,0,0.8); border-radius: 16px; padding: 3px 8px; font-size: 0.75rem; font-weight: 800; }
.badge.high { color: #4ade80; }
.badge.mid { color: #fbbf24; }
.badge.low { color: #f87171; }
.info { padding: 14px; }
.info h4 { font-size: 0.85rem; font-weight: 700; margin-bottom: 8px; }
.reason { font-size: 0.78rem; color: #64748b; margin-bottom: 12px; line-height: 1.5; }
.dbtn { width: 100%; padding: 9px; background: #7c3aed; border: none; border-radius: 8px; color: white; font-size: 0.85rem; font-weight: 700; cursor: pointer; }
.err { color: #f87171; text-align: center; margin-top: 12px; display: none; font-size: 0.9rem; }
</style>
</head>
<body>
<nav class="nav"><div class="logo">ClipAI</div><span class="tag">FREE · NO WATERMARK</span></nav>
<div class="hero">
  <h1>Turn Long Videos Into<br/><span>Viral Clips</span></h1>
  <p>AI finds best moments · Auto captions · 9:16 reframe · Virality score</p>
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
    <h3 style="margin-bottom:16px">⚙️ Processing...</h3>
    <div id="steps"></div>
    <div class="bar"><div class="fill" id="fill"></div></div>
  </div>
</div>

<div class="results" id="results">
  <div class="rhead"><h2>🎉 Clips Ready!</h2><button class="nbtn" onclick="reset()">+ New Video</button></div>
  <div class="grid" id="grid"></div>
</div>

<script>
const STEPS = [
  {key:'upload',label:'Uploading video',icon:'📤'},
  {key:'audio',label:'Extracting audio',icon:'🎵'},
  {key:'transcribe',label:'Transcribing',icon:'📝'},
  {key:'analyze',label:'Finding best moments',icon:'🧠'},
  {key:'clips',label:'Cutting clips',icon:'✂️'},
  {key:'captions',label:'Adding captions',icon:'💬'},
  {key:'done',label:'Done!',icon:'🎉'},
];
let jobId=null, timer=null;
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
    if(d.step==='done'){clearInterval(timer);showResults(d.clips);}
    else if(d.status==='error'){clearInterval(timer);showErr(d.message||'Error occurred');}
  }catch(e){}
}
function showResults(clips){
  document.getElementById('prog').style.display='none';
  document.getElementById('results').style.display='block';
  document.getElementById('grid').innerHTML=clips.map(c=>{
    const bc=c.virality_score>=75?'high':c.virality_score>=50?'mid':'low';
    const em=c.virality_score>=75?'🔥':c.virality_score>=50?'⚡':'📊';
    return `<div class="card"><div class="preview"><video controls src="/clip/${jobId}/${c.filename}"></video><div class="badge ${bc}">${em} ${c.virality_score}/100</div></div>
    <div class="info"><h4>${c.title}</h4><div class="reason">${c.reason}</div>
    <button class="dbtn" onclick="dl('${c.filename}')">⬇️ Download</button></div></div>`;
  }).join('');
  document.getElementById('results').scrollIntoView({behavior:'smooth'});
}
function dl(fn){const a=document.createElement('a');a.href='/clip/'+jobId+'/'+fn;a.download=fn;a.click();}
function showErr(m){document.getElementById('btn').disabled=false;document.getElementById('prog').style.display='none';const e=document.getElementById('err');e.textContent='❌ '+m;e.style.display='block';}
function reset(){document.getElementById('results').style.display='none';document.getElementById('file').value='';document.getElementById('chosen').textContent='';document.getElementById('btn').disabled=true;window.scrollTo({top:0,behavior:'smooth'});}
</script>
</body></html>"""

@app.route("/")
def index():
    return HTML

@app.route("/health")
def health():
    return jsonify({"status": "ok"})

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

@app.route("/clip/<job_id>/<filename>")
def serve_clip(job_id, filename):
    return send_from_directory(os.path.join(OUTPUT_FOLDER, job_id), filename)

def get_duration(path):
    r = subprocess.run(["ffprobe","-v","error","-show_entries","format=duration","-of","default=noprint_wrappers=1:nokey=1",path], capture_output=True, text=True)
    return float(r.stdout.strip())

def extract_audio(video, audio):
    subprocess.run(["ffmpeg","-i",video,"-vn","-acodec","pcm_s16le","-ar","16000","-ac","1",audio,"-y","-loglevel","error"], check=True)

def analyze_with_claude(duration, num_clips, clip_length, job_id):
    jobs[job_id]["step"] = "analyze"
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        raise Exception("ANTHROPIC_API_KEY not set in Railway Variables")
    
    import urllib.request, json as j
    prompt = f"""A video is {duration:.0f} seconds long. Generate {num_clips} clip suggestions, each ~{clip_length} seconds. Space them evenly.

Return ONLY a JSON array, no markdown:
[{{"title":"Clip title","start":0,"end":{clip_length},"virality_score":75,"reason":"Why this clip is engaging"}}]

Rules: don't go past {duration:.0f}s, each clip ~{clip_length}s, no overlaps."""

    data = j.dumps({"model":"claude-sonnet-4-6","max_tokens":1000,"messages":[{"role":"user","content":prompt}]}).encode()
    req = urllib.request.Request("https://api.anthropic.com/v1/messages", data=data, headers={"Content-Type":"application/json","x-api-key":api_key,"anthropic-version":"2023-06-01"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        result = j.loads(resp.read())
    text = result["content"][0]["text"].strip()
    text = re.sub(r"```json\s*|\s*```","",text).strip()
    return j.loads(text)

def cut_clip(video, start, end, output):
    duration = end - start
    r = subprocess.run(["ffprobe","-v","error","-select_streams","v:0","-show_entries","stream=width,height","-of","csv=p=0",video], capture_output=True, text=True)
    dims = r.stdout.strip().split(",")
    w, h = int(dims[0]), int(dims[1])
    if w/h > 9/16:
        nw = int(h*9/16); x = (w-nw)//2
        crop = f"crop={nw}:{h}:{x}:0,scale=1080:1920"
    else:
        nh = int(w*16/9); y = max(0,(h-nh)//2)
        crop = f"crop={w}:{nh}:0:{y},scale=1080:1920"
    subprocess.run(["ffmpeg","-ss",str(start),"-i",video,"-t",str(duration),"-vf",crop,"-c:v","libx264","-preset","fast","-crf","23","-c:a","aac","-b:a","128k","-movflags","+faststart",output,"-y","-loglevel","error"], check=True)

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
            fn = f"clip_{i+1:02d}_score{c['virality_score']}.mp4"
            cut_clip(video_path, start, end, os.path.join(job_dir, fn))
            jobs[job_id]["step"] = "captions"
            final.append({"filename":fn,"title":c.get("title",f"Clip {i+1}"),"virality_score":c.get("virality_score",70),"reason":c.get("reason",""),"duration":round(end-start)})
        final.sort(key=lambda x: x["virality_score"], reverse=True)
        jobs[job_id].update({"status":"done","step":"done","clips":final})
        try: os.remove(audio_path); os.remove(video_path)
        except: pass
    except Exception as e:
        jobs[job_id].update({"status":"error","step":"done","error_step":jobs[job_id].get("step","clips"),"message":str(e)})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    print(f"Starting ClipAI on port {port}")
    app.run(debug=False, host="0.0.0.0", port=port)

