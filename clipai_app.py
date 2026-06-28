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

# Logo embedded as base64
LOGO_B64 = "iVBORw0KGgoAAAANSUhEUgAAAfQAAAH0CAYAAADL1t+KAAAAUGVYSWZNTQAqAAAACAAEAQAABAAAAAEAAAAAAQEABAAAAAEAAAAAh2kABAAAAAEAAAA+ARIABAAAAAEAAAAAAAAAAAABkggABAAAAAEAAAAAAAAAALFNWc4AAAqOaVRYdFhNTDpjb20uYWRvYmUueG1wAAAAAAA8P3hwYWNrZXQgYmVnaW49Ij8iIGlkPSJXNU0wTXBDZWhpSHpyZVN6TlRjemtjOWQiPz4KPHg6eG1wbWV0YSB4bWxuczp4PSJhZG9iZTpuczptZXRhLyIgeDp4bXB0az0iQWRvYmUgWE1QIENvcmUgVGVzdC5TTkFQU0hPVCI+CiAgPHJkZjpSREYgeG1sbnM6cmRmPSJodHRwOi8vd3d3LnczLm9yZy8xOTk5LzAyLzIyLXJkZi1zeW50YXgtbnMjIj4KICAgIDxyZGY6RGVzY3JpcHRpb24gcmRmOmFib3V0PSIiCiAgICAgICAgeG1sbnM6QXR0cmliPSJodHRwOi8vbnMuYXR0cmlidXRpb24uY29tL2Fkcy8xLjAvIj4KICAgICAgPEF0dHJpYjpBZHM+CiAgICAgICAgPHJkZjpTZXE+CiAgICAgICAgICA8cmRmOmxpCiAgICAgICAgICAgIEF0dHJpYjpGYklkPSI1MjUyNjU5MTQxNzk1ODAiCiAgICAgICAgICAgIEF0dHJpYjpDcmVhdGVkPSIyMDI2LTA2LTI4IgogICAgICAgICAgICBBdHRyaWI6VG91Y2hUeXBlPSIyIgogICAgICAgICAgICBBdHRyaWI6RXh0SWQ9ImM4MDQ1Zjg1LTRhYmQtNGYyNC1iYmJjLWUwOTYyOThjZWIxMyIvPgogICAgICAgIDwvcmRmOlNlcT4KICAgICAgPC9BdHRyaWI6QWRzPgogICAgPC9yZGY6RGVzY3JpcHRpb24+CiAgPC9yZGY6UkRGPgo8L3g6eG1wbWV0YT4KICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAg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"

def ensure_logo():
    logo_path = os.path.join("/tmp", "logo.png")
    if not os.path.exists(logo_path):
        import base64
        with open(logo_path, 'wb') as f:
            f.write(base64.b64decode(LOGO_B64))
    return logo_path

def get_ffmpeg_exe():
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except:
        return "ffmpeg"

def get_ffprobe_exe():
    try:
        import imageio_ffmpeg
        ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()
        ffprobe_path = ffmpeg_path.replace("ffmpeg", "ffprobe")
        if os.path.exists(ffprobe_path):
            return ffprobe_path
        r = subprocess.run(["which", "ffprobe"], capture_output=True, text=True)
        if r.returncode == 0:
            return r.stdout.strip()
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
.tag { margin-left: 8px; background: #1e1e2e; color: #a78bfa; font-size: 0.7rem; padding: 3px 10px; border-radius: 20px; }
.hero { text-align: center; padding: 30px 20px 20px; }
.hero h1 { font-size: 1.8rem; font-weight: 900; margin-bottom: 8px; }
.hero h1 span { color: #a78bfa; }
.hero p { color: #94a3b8; font-size: 0.85rem; }
.box { max-width: 600px; margin: 20px auto; padding: 0 20px; }
.drop { border: 2px dashed #2d2d4e; border-radius: 16px; padding: 30px 20px; text-align: center; cursor: pointer; background: #0f0f1a; position: relative; }
.drop:hover { border-color: #a78bfa; }
.drop input { position: absolute; inset: 0; opacity: 0; cursor: pointer; width: 100%; height: 100%; }
.section-title { font-size: 0.75rem; color: #64748b; font-weight: 700; text-transform: uppercase; letter-spacing: 0.08em; margin: 18px 0 8px; display: flex; align-items: center; gap: 6px; }
.section-title span { flex: 1; height: 1px; background: #1e1e2e; }
.row { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
label { display: block; font-size: 0.78rem; color: #94a3b8; margin-bottom: 5px; font-weight: 600; }
select { width: 100%; background: #0f0f1a; border: 1px solid #2d2d4e; border-radius: 8px; color: #e2e8f0; padding: 9px; font-size: 0.85rem; }
.topics { display: flex; flex-wrap: wrap; gap: 6px; }
.topic { background: #1e1e2e; border: 1px solid #2d2d4e; color: #94a3b8; padding: 5px 12px; border-radius: 20px; cursor: pointer; font-size: 0.78rem; transition: all 0.2s; }
.topic.active { background: #3b1d8a; border-color: #a78bfa; color: white; }
.toggles { display: flex; flex-direction: column; gap: 6px; }
.toggle-row { display: flex; align-items: center; justify-content: space-between; background: #0f0f1a; border: 1px solid #1e1e2e; border-radius: 10px; padding: 10px 14px; }
.tl { font-size: 0.82rem; font-weight: 600; }
.ts { font-size: 0.72rem; color: #64748b; margin-top: 2px; }
.toggle { position: relative; width: 40px; height: 22px; flex-shrink: 0; }
.toggle input { opacity: 0; width: 0; height: 0; }
.slider { position: absolute; inset: 0; background: #2d2d4e; border-radius: 22px; cursor: pointer; transition: 0.3s; }
.slider:before { content: ""; position: absolute; width: 16px; height: 16px; left: 3px; bottom: 3px; background: white; border-radius: 50%; transition: 0.3s; }
input:checked + .slider { background: #7c3aed; }
input:checked + .slider:before { transform: translateX(18px); }

/* Copyright section */
.cp-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 6px; }
.cp-item { background: #0f0f1a; border: 1px solid #1e1e2e; border-radius: 10px; padding: 10px; cursor: pointer; transition: all 0.2s; }
.cp-item.active { border-color: #a78bfa; background: #13132a; }
.cp-item input { display: none; }
.cp-icon { font-size: 1.2rem; margin-bottom: 4px; }
.cp-name { font-size: 0.78rem; font-weight: 700; }
.cp-desc { font-size: 0.68rem; color: #64748b; margin-top: 2px; }

.btn { width: 100%; margin-top: 16px; padding: 14px; background: linear-gradient(135deg, #7c3aed, #db2777); border: none; border-radius: 12px; color: white; font-size: 1rem; font-weight: 700; cursor: pointer; }
.btn:disabled { opacity: 0.4; cursor: not-allowed; }
.chosen { margin-top: 8px; color: #a78bfa; font-size: 0.82rem; text-align: center; }
.progress { max-width: 600px; margin: 16px auto; padding: 0 20px; display: none; }
.pcard { background: #0f0f1a; border: 1px solid #1e1e2e; border-radius: 16px; padding: 20px; }
.step { display: flex; align-items: center; gap: 10px; margin-bottom: 10px; }
.sicon { width: 30px; height: 30px; border-radius: 50%; background: #1e1e2e; display: flex; align-items: center; justify-content: center; flex-shrink: 0; font-size: 0.85rem; }
.sicon.active { background: #3b1d8a; }
.sicon.done { background: #14532d; }
.stext { font-size: 0.85rem; color: #64748b; }
.stext.active { color: white; font-weight: 600; }
.stext.done { color: #4ade80; }
.bar { background: #1e1e2e; border-radius: 99px; height: 5px; margin-top: 14px; }
.fill { height: 100%; background: linear-gradient(90deg, #7c3aed, #db2777); border-radius: 99px; transition: width 0.5s; width: 0; }
.results { max-width: 600px; margin: 20px auto 60px; padding: 0 20px; display: none; }
.rhead { display: flex; justify-content: space-between; align-items: center; margin-bottom: 14px; }
.rhead h2 { font-size: 1.1rem; font-weight: 800; }
.nbtn { background: #1e1e2e; border: 1px solid #2d2d4e; color: #e2e8f0; padding: 7px 14px; border-radius: 8px; cursor: pointer; font-size: 0.82rem; }
.clip-item { background: #0f0f1a; border: 1px solid #1e1e2e; border-radius: 14px; margin-bottom: 14px; overflow: hidden; }
.clip-top { padding: 12px 12px 6px; }
.clip-title { font-size: 0.88rem; font-weight: 700; margin-bottom: 6px; }
.clip-meta { display: flex; gap: 6px; margin-bottom: 6px; flex-wrap: wrap; }
.badge { padding: 3px 7px; border-radius: 6px; font-size: 0.7rem; font-weight: 700; }
.badge.high { background: #14532d; color: #4ade80; }
.badge.mid { background: #78350f; color: #fbbf24; }
.badge.low { background: #7f1d1d; color: #f87171; }
.tag2 { background: #1e1e2e; color: #94a3b8; padding: 3px 7px; border-radius: 6px; font-size: 0.7rem; }
.cp-tags { display: flex; flex-wrap: wrap; gap: 4px; padding: 0 12px 10px; }
.cp-tag { background: #1a0a2e; color: #a78bfa; padding: 2px 7px; border-radius: 4px; font-size: 0.68rem; }
.clip-reason { font-size: 0.76rem; color: #64748b; line-height: 1.5; padding: 0 12px 10px; }
.dl-btn { display: block; width: 100%; padding: 13px; background: linear-gradient(135deg, #7c3aed, #db2777); border: none; color: white; font-size: 0.9rem; font-weight: 700; cursor: pointer; text-align: center; text-decoration: none; }
.err { color: #f87171; margin-top: 10px; display: none; font-size: 0.8rem; padding: 10px; background: #1a0000; border-radius: 8px; border: 1px solid #7f1d1d; word-break: break-word; }
</style>
</head>
<body>
<nav class="nav"><div class="logo">ClipAI</div><span class="tag">FREE · NO WATERMARK</span></nav>
<div class="hero">
  <h1>Turn Long Videos Into<br/><span>Viral Clips</span></h1>
  <p>AI clips · Copyright protection · Captions · 9:16</p>
</div>
<div class="box">
  <div class="drop" id="drop">
    <div style="font-size:2rem">🎬</div>
    <h3 style="margin:8px 0 4px">Tap to upload video</h3>
    <p style="color:#64748b;font-size:0.82rem">MP4, MOV, MKV — up to 500MB</p>
    <input type="file" id="file" accept="video/*"/>
  </div>
  <div class="chosen" id="chosen"></div>

  <div class="section-title">Or paste a video link <span></span></div>
  <div style="display:flex;gap:8px;margin-bottom:4px">
    <input type="url" id="urlInput" placeholder="YouTube, TikTok, Instagram link..."
      style="flex:1;background:#0f0f1a;border:1px solid #2d2d4e;border-radius:8px;color:#e2e8f0;padding:10px;font-size:0.85rem"/>
    <button onclick="useUrl()" style="background:#3b1d8a;border:none;border-radius:8px;color:white;padding:10px 14px;font-size:0.82rem;font-weight:700;cursor:pointer;white-space:nowrap">Use Link</button>
  </div>
  <div style="font-size:0.72rem;color:#64748b;margin-bottom:4px">Supports YouTube · TikTok · Instagram · Facebook · Twitter/X</div>

  <div class="section-title">Clip Settings <span></span></div>
  <div class="row">
    <div><label>Number of clips</label>
    <select id="num"><option value="3">3 clips</option><option value="5" selected>5 clips</option><option value="8">8 clips</option></select></div>
    <div><label>Clip length</label>
    <select id="len"><option value="30">30s</option><option value="45">45s</option><option value="60" selected>60s</option><option value="90">90s</option></select></div>
  </div>

  <div class="section-title">Content Focus <span></span></div>
  <div class="topics">
    <div class="topic active" onclick="selectTopic(this,'general')">🎯 General</div>
    <div class="topic" onclick="selectTopic(this,'funny')">😂 Funny</div>
    <div class="topic" onclick="selectTopic(this,'emotional')">❤️ Emotional</div>
    <div class="topic" onclick="selectTopic(this,'educational')">📚 Educational</div>
    <div class="topic" onclick="selectTopic(this,'motivational')">💪 Motivational</div>
    <div class="topic" onclick="selectTopic(this,'shocking')">😱 Shocking</div>
  </div>

  <div class="section-title">Video Features <span></span></div>
  <div class="toggles">
    <div class="toggle-row">
      <div><div class="tl">📐 9:16 Reframe</div><div class="ts">Optimized for TikTok/Reels/Shorts</div></div>
      <label class="toggle"><input type="checkbox" id="reframe" checked/><span class="slider"></span></label>
    </div>
    <div class="toggle-row">
      <div><div class="tl">💬 Auto Captions</div><div class="ts">Burns subtitles into video</div></div>
      <label class="toggle"><input type="checkbox" id="captions" checked/><span class="slider"></span></label>
    </div>
    <div id="captionStyleSection" class="toggle-row" style="flex-direction:column;align-items:flex-start;gap:10px">
      <div><div class="tl">💬 Caption Style</div><div class="ts">Choose how captions look</div></div>
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;width:100%">
        <div class="cap-style active" onclick="selectCapStyle(this,'classic')" style="background:#13132a;border:1px solid #a78bfa;border-radius:8px;padding:10px;cursor:pointer;text-align:center">
          <div style="font-size:0.8rem;font-weight:700;color:white">Classic</div>
          <div style="font-size:0.68rem;color:#94a3b8;margin-top:3px">White text, black outline</div>
        </div>
        <div class="cap-style" onclick="selectCapStyle(this,'bold')" style="background:#0f0f1a;border:1px solid #2d2d4e;border-radius:8px;padding:10px;cursor:pointer;text-align:center">
          <div style="font-size:0.8rem;font-weight:700;color:#fbbf24">Bold Yellow</div>
          <div style="font-size:0.68rem;color:#94a3b8;margin-top:3px">Big yellow words</div>
        </div>
        <div class="cap-style" onclick="selectCapStyle(this,'tiktok')" style="background:#0f0f1a;border:1px solid #2d2d4e;border-radius:8px;padding:10px;cursor:pointer;text-align:center">
          <div style="font-size:0.8rem;font-weight:700;color:#ff0050">TikTok Style</div>
          <div style="font-size:0.68rem;color:#94a3b8;margin-top:3px">Red highlight box</div>
        </div>
        <div class="cap-style" onclick="selectCapStyle(this,'minimal')" style="background:#0f0f1a;border:1px solid #2d2d4e;border-radius:8px;padding:10px;cursor:pointer;text-align:center">
          <div style="font-size:0.8rem;font-weight:700;color:#94a3b8">Minimal</div>
          <div style="font-size:0.68rem;color:#64748b;margin-top:3px">Small subtle text</div>
        </div>
        <div class="cap-style" onclick="selectCapStyle(this,'fire')" style="background:#0f0f1a;border:1px solid #2d2d4e;border-radius:8px;padding:10px;cursor:pointer;text-align:center">
          <div style="font-size:0.8rem;font-weight:700;color:#f97316">🔥 Fire</div>
          <div style="font-size:0.68rem;color:#94a3b8;margin-top:3px">Orange glow effect</div>
        </div>
        <div class="cap-style" onclick="selectCapStyle(this,'neon')" style="background:#0f0f1a;border:1px solid #2d2d4e;border-radius:8px;padding:10px;cursor:pointer;text-align:center">
          <div style="font-size:0.8rem;font-weight:700;color:#a78bfa">⚡ Neon</div>
          <div style="font-size:0.68rem;color:#94a3b8;margin-top:3px">Purple glow</div>
        </div>
      </div>
    </div>
    <div class="toggle-row">
      <div><div class="tl">🔄 Mirror Flip</div><div class="ts">Horizontally flips video</div></div>
      <label class="toggle"><input type="checkbox" id="mirror"/><span class="slider"></span></label>
    </div>
    <div class="toggle-row">
      <div><div class="tl">🎨 Color Grade</div><div class="ts">Adjusts brightness & contrast</div></div>
      <label class="toggle"><input type="checkbox" id="colorgrade" checked/><span class="slider"></span></label>
    </div>
    <div class="toggle-row">
      <div><div class="tl">⚡ Speed Adjust</div><div class="ts">Slight speed change (101%)</div></div>
      <label class="toggle"><input type="checkbox" id="speed" checked/><span class="slider"></span></label>
    </div>
    <div class="toggle-row">
      <div><div class="tl">🎵 Pitch Shift Audio</div><div class="ts">Slightly shifts audio pitch</div></div>
      <label class="toggle"><input type="checkbox" id="pitch" checked/><span class="slider"></span></label>
    </div>
    <div class="toggle-row">
      <div><div class="tl">🎶 Background Music</div><div class="ts">Adds soft beat under your clip</div></div>
      <label class="toggle"><input type="checkbox" id="music"/><span class="slider"></span></label>
    </div>
  </div>

  <div class="section-title">Copyright Protection Level <span></span></div>
  <div class="cp-grid">
    <div class="cp-item active" onclick="selectCP(this,'none')">
      <div class="cp-icon">🟢</div>
      <div class="cp-name">None</div>
      <div class="cp-desc">Original quality, no changes</div>
    </div>
    <div class="cp-item" onclick="selectCP(this,'light')">
      <div class="cp-icon">🟡</div>
      <div class="cp-name">Light</div>
      <div class="cp-desc">Speed + color tweak</div>
    </div>
    <div class="cp-item" onclick="selectCP(this,'medium')">
      <div class="cp-icon">🟠</div>
      <div class="cp-name">Medium</div>
      <div class="cp-desc">Flip + pitch + speed</div>
    </div>
    <div class="cp-item" onclick="selectCP(this,'strong')">
      <div class="cp-icon">🔴</div>
      <div class="cp-name">Strong</div>
      <div class="cp-desc">All changes applied</div>
    </div>
  </div>

  <button class="btn" id="btn" onclick="start()" disabled>✨ Generate Clips</button>
  <div class="err" id="err"></div>
</div>

<div class="progress" id="prog">
  <div class="pcard">
    <h3 style="margin-bottom:14px">⚙️ Processing...</h3>
    <div id="steps"></div>
    <div class="bar"><div class="fill" id="fill"></div></div>
  </div>
</div>

<div class="results" id="results">
  <div class="rhead"><h2>🎉 Clips Ready!</h2><button class="nbtn" onclick="resetApp()">+ New</button></div>
  <div id="cliplist"></div>
</div>

<script>
let selectedTopic='general', selectedCP='none';
const STEPS=[
  {key:'upload',label:'Uploading video',icon:'📤'},
  {key:'audio',label:'Extracting audio',icon:'🎵'},
  {key:'transcribe',label:'Analyzing video',icon:'🧠'},
  {key:'analyze',label:'Finding best moments',icon:'🎯'},
  {key:'clips',label:'Cutting & processing',icon:'✂️'},
  {key:'captions',label:'Applying protection & captions',icon:'🛡️'},
  {key:'done',label:'Done!',icon:'🎉'},
];
let jobId=null,timer=null;
let useUrlMode = false;
let selectedCapStyle = 'classic';
function selectCapStyle(el, style) {
  document.querySelectorAll('.cap-style').forEach(x => {
    x.style.background = '#0f0f1a';
    x.style.borderColor = '#2d2d4e';
  });
  el.style.background = '#13132a';
  el.style.borderColor = '#a78bfa';
  selectedCapStyle = style;
}
function useUrl(){
  const url = document.getElementById('urlInput').value.trim();
  if(!url){alert('Please paste a video link first');return;}
  useUrlMode = true;
  document.getElementById('chosen').textContent = '🔗 ' + url.substring(0,50) + '...';
  document.getElementById('btn').disabled = false;
  document.getElementById('drop').style.opacity = '0.4';
}
document.getElementById('captions').addEventListener('change', function(){
  document.getElementById('captionStyleSection').style.display = this.checked ? 'flex' : 'none';
});
function selectTopic(el,t){document.querySelectorAll('.topic').forEach(x=>x.classList.remove('active'));el.classList.add('active');selectedTopic=t;}
function selectCP(el,t){document.querySelectorAll('.cp-item').forEach(x=>x.classList.remove('active'));el.classList.add('active');selectedCP=t;
  // Auto-set toggles based on level
  const mirror=document.getElementById('mirror');
  const speed=document.getElementById('speed');
  const pitch=document.getElementById('pitch');
  const colorgrade=document.getElementById('colorgrade');
  if(t==='none'){mirror.checked=false;speed.checked=false;pitch.checked=false;colorgrade.checked=false;}
  else if(t==='light'){mirror.checked=false;speed.checked=true;pitch.checked=false;colorgrade.checked=true;}
  else if(t==='medium'){mirror.checked=true;speed.checked=true;pitch.checked=true;colorgrade.checked=true;}
  else if(t==='strong'){mirror.checked=true;speed.checked=true;pitch.checked=true;colorgrade.checked=true;}
}
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
  const f=document.getElementById('file').files[0];
  if(!f && !useUrlMode)return;
  document.getElementById('btn').disabled=true;
  document.getElementById('err').style.display='none';
  document.getElementById('prog').style.display='block';
  document.getElementById('results').style.display='none';
  renderSteps('upload',null);
  document.getElementById('prog').scrollIntoView({behavior:'smooth'});
  const fd=new FormData();
  if(useUrlMode){
    fd.append('video_url', document.getElementById('urlInput').value.trim());
  } else {
    fd.append('video',f);
  }
  fd.append('num_clips',document.getElementById('num').value);
  fd.append('clip_length',document.getElementById('len').value);
  fd.append('topic',selectedTopic);
  fd.append('cp_level',selectedCP);
  fd.append('captions',document.getElementById('captions').checked?'1':'0');
  fd.append('caption_style', selectedCapStyle);
  fd.append('reframe',document.getElementById('reframe').checked?'1':'0');
  fd.append('mirror',document.getElementById('mirror').checked?'1':'0');
  fd.append('colorgrade',document.getElementById('colorgrade').checked?'1':'0');
  fd.append('speed',document.getElementById('speed').checked?'1':'0');
  fd.append('pitch',document.getElementById('pitch').checked?'1':'0');
  fd.append('music',document.getElementById('music').checked?'1':'0');
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
    const protections = c.protections||[];
    const ptags = protections.length ? protections.map(p=>`<span class="cp-tag">${p}</span>`).join('') : '';
    return `<div class="clip-item"><div class="clip-top">
      <div class="clip-title">${i+1}. ${c.title}</div>
      <div class="clip-meta"><span class="badge ${bc}">${em} ${s}/100</span><span class="tag2">⏱ ${c.duration}s</span>${c.has_captions?'<span class="tag2">💬</span>':''}</div>
    </div>${ptags?`<div class="cp-tags">${ptags}</div>`:''}<div class="clip-reason">${c.reason}</div>
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
    return jsonify({"status": "ok"})

@app.route("/upload", methods=["POST"])
def upload():
    try:
        video_url = request.form.get("video_url", "")
        file = request.files.get("video")
        if not file and not video_url:
            return jsonify({"error": "No video file or URL provided"}), 400
        num_clips = int(request.form.get("num_clips", 5))
        clip_length = int(request.form.get("clip_length", 60))
        topic = request.form.get("topic", "general")
        cp_level = request.form.get("cp_level", "none")
        add_captions = request.form.get("captions", "1") == "1"
        caption_style = request.form.get("caption_style", "classic")
        do_reframe = request.form.get("reframe", "1") == "1"
        do_mirror = request.form.get("mirror", "0") == "1"
        do_colorgrade = request.form.get("colorgrade", "0") == "1"
        do_speed = request.form.get("speed", "0") == "1"
        do_pitch = request.form.get("pitch", "0") == "1"
        add_music = request.form.get("music", "0") == "1"

        job_id = str(uuid.uuid4())[:8]
        job_dir = os.path.join(OUTPUT_FOLDER, job_id)
        os.makedirs(job_dir, exist_ok=True)
        if video_url:
            # Download from URL using yt-dlp
            video_path = os.path.join(UPLOAD_FOLDER, f"{job_id}.mp4")
            jobs[job_id] = {"status": "running", "step": "audio", "clips": []}
            result = subprocess.run([
                "yt-dlp", "-f", "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
                "--merge-output-format", "mp4",
                "-o", video_path, video_url,
                "--no-playlist", "--max-filesize", "500m"
            ], capture_output=True, text=True, timeout=300)
            if result.returncode != 0:
                return jsonify({"error": "Could not download video. Check the link and try again."}), 400
        else:
            ext = os.path.splitext(file.filename)[1] or ".mp4"
            video_path = os.path.join(UPLOAD_FOLDER, f"{job_id}{ext}")
            file.save(video_path)
        jobs[job_id] = {"status": "running", "step": "audio", "clips": []}
        t = threading.Thread(target=process_video,
                             args=(job_id, video_path, job_dir, num_clips, clip_length,
                                   topic, cp_level, add_captions, caption_style, do_reframe,
                                   do_mirror, do_colorgrade, do_speed, do_pitch, add_music))
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
        try:
            r = subprocess.run([ffprobe_exe,"-v","error","-show_entries","format=duration",
                                "-of","default=noprint_wrappers=1:nokey=1",path],
                               capture_output=True, text=True, timeout=15)
            val = r.stdout.strip()
            if val:
                return float(val)
        except Exception:
            pass
    # Reliable fallback: parse FFmpeg stderr output
    try:
        r = subprocess.run([ffmpeg_exe,"-i",path,"-f","null","-"],
                           capture_output=True, text=True, timeout=30)
        combined = r.stdout + r.stderr
        match = re.search(r"Duration:\s*(\d+):(\d+):(\d+\.?\d*)", combined)
        if match:
            h,m,s = float(match.group(1)),float(match.group(2)),float(match.group(3))
            return h*3600+m*60+s
    except Exception:
        pass
    # Last resort: ffmpeg -i only (no decode)
    try:
        r = subprocess.run([ffmpeg_exe,"-i",path],
                           capture_output=True, text=True, timeout=15)
        combined = r.stdout + r.stderr
        match = re.search(r"Duration:\s*(\d+):(\d+):(\d+\.?\d*)", combined)
        if match:
            h,m,s = float(match.group(1)),float(match.group(2)),float(match.group(3))
            return h*3600+m*60+s
    except Exception:
        pass
    raise Exception("Could not get video duration — ensure the file is a valid MP4/MOV/MKV")

def get_dimensions(path):
    ffmpeg_exe = get_ffmpeg_exe()
    ffprobe_exe = get_ffprobe_exe()
    if ffprobe_exe:
        r = subprocess.run([ffprobe_exe,"-v","error","-select_streams","v:0",
                            "-show_entries","stream=width,height","-of","csv=p=0",path],
                           capture_output=True, text=True)
        dims = r.stdout.strip().split(",")
        return int(dims[0]), int(dims[1])
    r = subprocess.run([ffmpeg_exe,"-i",path], capture_output=True, text=True)
    match = re.search(r"(\d{2,4})x(\d{2,4})", r.stderr)
    if match:
        return int(match.group(1)), int(match.group(2))
    return 1920, 1080

def extract_audio(video, audio):
    ffmpeg_exe = get_ffmpeg_exe()
    subprocess.run([ffmpeg_exe,"-i",video,"-vn","-acodec","pcm_s16le",
                    "-ar","16000","-ac","1",audio,"-y","-loglevel","error"], check=True)

def transcribe_audio(audio_path, job_id):
    """Real Whisper transcription — returns list of {start, end, text} segments"""
    jobs[job_id]["step"] = "transcribe"
    try:
        import whisper
        model = whisper.load_model("tiny")  # tiny = fast, low RAM, good enough
        result = model.transcribe(audio_path, word_timestamps=True, fp16=False)
        segments = []
        for seg in result.get("segments", []):
            segments.append({
                "start": seg["start"],
                "end": seg["end"],
                "text": seg["text"].strip()
            })
        return segments
    except Exception:
        return []  # Whisper not installed or failed — fallback to duration-only mode

def segments_to_srt(segments, clip_start):
    """Convert Whisper segments (absolute timestamps) to SRT for a clip window"""
    def fmt(t):
        t = max(0, t)
        h = int(t // 3600); m = int((t % 3600) // 60); s = int(t % 60); ms = int((t % 1) * 1000)
        return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"
    lines = []
    idx = 1
    for seg in segments:
        rel_start = seg["start"] - clip_start
        rel_end = seg["end"] - clip_start
        if rel_end <= 0 or rel_start < 0:
            continue
        lines.append(f"{idx}\n{fmt(rel_start)} --> {fmt(rel_end)}\n{seg['text']}\n")
        idx += 1
    return "\n".join(lines) if lines else None

def generate_captions_srt(start, end, job_id, api_key, transcript_segments=None):
    """Use real Whisper segments if available, else ask AI for fake ones"""
    import urllib.request as ur

    # Use real transcript segments for this clip window if we have them
    if transcript_segments:
        clip_segs = [s for s in transcript_segments if s["end"] > start and s["start"] < end]
        if clip_segs:
            return segments_to_srt(clip_segs, start)

    # Fallback: AI-generated fake captions
    clip_duration = end - start
    prompt = f"""Generate realistic subtitle/caption entries for a {clip_duration:.0f} second video clip.
Create 6-10 short caption lines that would appear during the clip.
Return ONLY a valid SRT format, nothing else. Example:
1
00:00:00,000 --> 00:00:03,000
This is the first caption line

2
00:00:03,500 --> 00:00:06,000
This is the second line"""

    try:
        data = json.dumps({"model":"meta-llama/llama-3.1-8b-instruct","max_tokens":500,
                           "messages":[{"role":"user","content":prompt}]}).encode()
        req = ur.Request("https://openrouter.ai/api/v1/chat/completions", data=data,
                         headers={"Content-Type":"application/json",
                                   "Authorization":f"Bearer {api_key}",
                                   "HTTP-Referer":"https://clipai.app","X-Title":"ClipAI"})
        with ur.urlopen(req, timeout=15) as resp:
            result = json.loads(resp.read())
        return result["choices"][0]["message"]["content"].strip()
    except:
        return None

def analyze_with_ai(duration, num_clips, clip_length, topic, job_id, transcript_segments=None):
    jobs[job_id]["step"] = "analyze"
    api_key = os.environ.get("OPENROUTER_API_KEY","")
    if not api_key:
        raise Exception("OPENROUTER_API_KEY not set in Railway Variables")
    import urllib.request as ur
    topic_prompts = {
        "general":"the most engaging and interesting moments",
        "funny":"the funniest and most humorous moments",
        "emotional":"the most emotional and touching moments",
        "educational":"the most informative and educational moments",
        "motivational":"the most inspiring and motivational moments",
        "shocking":"the most surprising and shocking moments"
    }
    focus = topic_prompts.get(topic, topic_prompts["general"])

    if transcript_segments and len(transcript_segments) > 0:
        # Rich prompt using real transcript content — truncate to ~3000 chars
        full_text = ""
        for seg in transcript_segments:
            full_text += f"[{seg['start']:.1f}s] {seg['text']}\n"
        full_text = full_text[:3000]
        prompt = f"""Here is a real transcript of a video ({duration:.0f} seconds long) with timestamps:

{full_text}

Find {num_clips} clips focusing on {focus}, each ~{clip_length} seconds long.
Use the actual transcript to identify the best moments based on real content and what was said.

Return ONLY a valid JSON array:
[{{"title":"Catchy title","start":0,"end":{clip_length},"virality_score":85,"reason":"Why this specific moment is viral based on what was said"}}]

Rules: use real timestamps from the transcript, never exceed {duration:.0f}s, no overlaps, each clip ~{clip_length}s."""
    else:
        # Fallback: no transcript, guess by duration only
        prompt = f"""A video is {duration:.0f} seconds long. Find {num_clips} clips focusing on {focus}, each ~{clip_length} seconds.

Return ONLY a valid JSON array:
[{{"title":"Catchy title","start":0,"end":{clip_length},"virality_score":80,"reason":"Why this clip is viral"}}]

Rules: never exceed {duration:.0f}s, no overlaps, each clip ~{clip_length}s."""

    data = json.dumps({"model":"meta-llama/llama-3.1-8b-instruct","max_tokens":1000,
                       "messages":[{"role":"user","content":prompt}]}).encode()
    req = ur.Request("https://openrouter.ai/api/v1/chat/completions", data=data,
                     headers={"Content-Type":"application/json",
                               "Authorization":f"Bearer {api_key}",
                               "HTTP-Referer":"https://clipai.app","X-Title":"ClipAI"})
    try:
        with ur.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read())
    except ur.HTTPError as e:
        body = e.read().decode()
        raise Exception(f"OpenRouter API error {e.code}: {body[:300]}")
    text = result["choices"][0]["message"]["content"].strip()
    text = re.sub(r"```json\s*|\s*```","",text).strip()
    match = re.search(r"\[.*\]", text, re.DOTALL)
    if match:
        text = match.group(0)
    return json.loads(text)

def generate_bg_music(duration, output_path):
    """Generate a real looping lo-fi beat using FFmpeg sine waves — no external files needed"""
    ffmpeg_exe = get_ffmpeg_exe()
    # Kick: low sine pulse every 0.5s | Hi-hat: high sine pulse every 0.25s | Bass: sub sine
    beat = (
        "sine=frequency=60:sample_rate=44100,"
        "volume=0.18[kick];"
        "sine=frequency=8000:sample_rate=44100,"
        "volume=0.04[hat];"
        "sine=frequency=80:sample_rate=44100,"
        "volume=0.12[bass];"
        "[kick][hat][bass]amix=inputs=3:duration=longest,"
        f"atrim=0:{duration:.2f},"
        "aecho=0.8:0.88:60:0.4,"   # subtle echo for depth
        "volume=0.55"               # final mix volume
    )
    cmd = [ffmpeg_exe, "-f", "lavfi", "-i", beat,
           "-c:a", "aac", "-b:a", "96k", "-ac", "1",
           output_path, "-y", "-loglevel", "error"]
    result = subprocess.run(cmd)
    return result.returncode == 0

def cut_clip(video, start, end, output, add_captions, caption_style, do_reframe,
             do_mirror, do_colorgrade, do_speed, do_pitch, add_music=False,
             transcript_segments=None):
    ffmpeg_exe = get_ffmpeg_exe()
    duration = end - start
    w, h = get_dimensions(video)

    # Build video filter chain
    filters = []
    if do_reframe:
        if w/h > 9/16:
            nw = int(h*9/16); x = (w-nw)//2
            filters.append(f"crop={nw}:{h}:{x}:0")
        else:
            nh = int(w*16/9); y = max(0,(h-nh)//2)
            filters.append(f"crop={w}:{nh}:0:{y}")
        filters.append("scale=720:1280")
    else:
        filters.append("scale=720:1280")
    if do_mirror:
        filters.append("hflip")
    if do_colorgrade:
        filters.append("eq=brightness=0.03:contrast=1.05:saturation=1.1")
    if do_speed:
        filters.append("setpts=0.99*PTS")

    vf = ",".join(filters)

    # Audio filters
    audio_filters = []
    if do_pitch:
        audio_filters.append("asetrate=44100*1.02,aresample=44100")
    if do_speed:
        audio_filters.append("atempo=1.01")
    # Note: add_music is handled as a separate mix pass after cutting, not here

    # Step 1: Cut and process video (no logo yet)
    tmp_output = output.replace(".mp4", "_tmp.mp4")
    cmd = [ffmpeg_exe, "-ss", str(start), "-i", video, "-t", str(duration)]
    if vf:
        cmd += ["-vf", vf]
    if audio_filters:
        cmd += ["-af", ",".join(audio_filters)]
    cmd += ["-c:v","libx264","-preset","ultrafast","-crf","28",
            "-vb","1000k","-c:a","aac","-b:a","96k","-ac","1",
            "-movflags","+faststart","-threads","1",
            tmp_output,"-y","-loglevel","error"]
    subprocess.run(cmd, check=True)

    # Step 1b: Mix in real background music if requested
    if add_music:
        music_path = output.replace(".mp4", "_music.aac")
        music_ok = generate_bg_music(duration, music_path)
        if music_ok and os.path.exists(music_path):
            try:
                music_mixed = output.replace(".mp4", "_musicmix.mp4")
                mix_cmd = [ffmpeg_exe, "-i", tmp_output, "-i", music_path,
                           "-filter_complex",
                           "[0:a]volume=1.0[orig];[1:a]volume=0.30[bg];[orig][bg]amix=inputs=2:duration=first[aout]",
                           "-map", "0:v", "-map", "[aout]",
                           "-c:v", "copy", "-c:a", "aac", "-b:a", "96k",
                           music_mixed, "-y", "-loglevel", "error"]
                result = subprocess.run(mix_cmd)
                if result.returncode == 0:
                    os.replace(music_mixed, tmp_output)
            except Exception:
                pass
            finally:
                try: os.remove(music_path)
                except: pass

    # Step 2: Burn captions if requested
    if add_captions:
        try:
            srt_path = output.replace(".mp4", ".srt")
            api_key = os.environ.get("OPENROUTER_API_KEY","")
            srt_content = generate_captions_srt(start, end, None, api_key, transcript_segments)
            if srt_content:
                with open(srt_path, 'w') as f:
                    f.write(srt_content)
                captioned = output.replace(".mp4", "_cap.mp4")
                # Caption styles
                style_map = {
                    'classic':    'FontSize=22,PrimaryColour=&Hffffff,OutlineColour=&H000000,Outline=2,Bold=0,Alignment=2',
                    'bold':       'FontSize=28,PrimaryColour=&H00ffff00,OutlineColour=&H000000,Outline=3,Bold=1,Alignment=2',
                    'tiktok':     'FontSize=26,PrimaryColour=&Hffffff,BackColour=&H800000ff,BorderStyle=4,Outline=0,Bold=1,Alignment=2',
                    'minimal':    'FontSize=16,PrimaryColour=&Hccffffff,OutlineColour=&H000000,Outline=1,Bold=0,Alignment=2',
                    'fire':       'FontSize=26,PrimaryColour=&H0045a5f9,OutlineColour=&H00000000,Outline=3,Bold=1,Alignment=2',
                    'neon':       'FontSize=26,PrimaryColour=&H00fa8bdb,OutlineColour=&H00000000,Outline=3,Bold=1,Alignment=2',
                }
                style_str = style_map.get(caption_style, style_map['classic'])
                cap_cmd = [ffmpeg_exe, "-i", tmp_output,
                           "-vf", f"subtitles={srt_path}:force_style='{style_str}'",
                           "-c:v","libx264","-preset","ultrafast","-crf","28",
                           "-c:a","copy","-threads","1",
                           captioned,"-y","-loglevel","error"]
                result = subprocess.run(cap_cmd)
                if result.returncode == 0:
                    os.replace(captioned, tmp_output)
                try: os.remove(srt_path)
                except: pass
        except Exception as e:
            pass  # captions failed silently, continue without

    # Step 2: Add logo watermark as separate pass
    logo_path = ensure_logo()
    if os.path.exists(logo_path):
        try:
            logo_filter = "[1:v]scale=140:-1,format=rgba,colorchannelmixer=aa=0.7[wm];[0:v][wm]overlay=W-w-15:H-h-15[out]"
            cmd2 = [ffmpeg_exe, "-i", tmp_output, "-i", logo_path,
                    "-filter_complex", logo_filter, "-map", "[out]", "-map", "0:a?",
                    "-c:v","libx264","-preset","ultrafast","-crf","28",
                    "-c:a","aac","-b:a","96k",
                    "-movflags","+faststart","-threads","1",
                    output,"-y","-loglevel","error"]
            subprocess.run(cmd2, check=True)
            os.remove(tmp_output)
        except:
            # If logo fails, just use the clip without logo
            os.rename(tmp_output, output)
    else:
        os.rename(tmp_output, output)

def process_video(job_id, video_path, job_dir, num_clips, clip_length,
                  topic, cp_level, add_captions, caption_style, do_reframe,
                  do_mirror, do_colorgrade, do_speed, do_pitch, add_music=False):
    try:
        duration = get_duration(video_path)
        jobs[job_id]["step"] = "audio"
        audio_path = os.path.join(job_dir, "audio.wav")
        extract_audio(video_path, audio_path)

        # Real Whisper transcription
        jobs[job_id]["step"] = "transcribe"
        transcript_segments = transcribe_audio(audio_path, job_id)

        # AI clip analysis — now powered by real transcript if available
        clips_data = analyze_with_ai(duration, num_clips, clip_length, topic, job_id, transcript_segments)
        jobs[job_id]["step"] = "clips"
        final = []
        for i, c in enumerate(clips_data[:num_clips]):
            start = max(0, float(c["start"]))
            end = min(duration, float(c["end"]))
            if end-start < 5:
                end = min(duration, start+clip_length)
            fn = f"clip_{i+1:02d}_score{c.get('virality_score',70)}.mp4"
            jobs[job_id]["step"] = "clips"
            cut_clip(video_path, start, end, os.path.join(job_dir, fn),
                     add_captions, caption_style, do_reframe, do_mirror, do_colorgrade,
                     do_speed, do_pitch, add_music, transcript_segments=transcript_segments)
            jobs[job_id]["step"] = "captions"

            protections = []
            if do_mirror: protections.append("🔄 Mirrored")
            if do_colorgrade: protections.append("🎨 Color graded")
            if do_speed: protections.append("⚡ Speed adjusted")
            if do_pitch: protections.append("🎵 Pitch shifted")
            if add_music: protections.append("🎶 Music added")

            final.append({
                "filename": fn,
                "title": c.get("title", f"Clip {i+1}"),
                "virality_score": c.get("virality_score", 70),
                "reason": c.get("reason",""),
                "duration": round(end-start),
                "has_captions": add_captions,
                "protections": protections
            })
        final.sort(key=lambda x: x["virality_score"], reverse=True)
        jobs[job_id].update({"status":"done","step":"done","clips":final})
        try:
            os.remove(audio_path)
            os.remove(video_path)
        except:
            pass
    except Exception as e:
        jobs[job_id].update({"status":"error","step":"done",
                              "error_step":jobs[job_id].get("step","clips"),"message":str(e)})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    print(f"Starting ClipAI on port {port}")
    app.run(debug=False, host="0.0.0.0", port=port)
