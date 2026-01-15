import streamlit as st
import os
import subprocess
import signal
import time
import re
from yt_dlp import YoutubeDL

# Configuration
OUTPUT_DIR = "./bilibili_videos"
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

# Page Config
st.set_page_config(page_title="Bilibili Pro Downloader", page_icon="📺", layout="wide")

# Custom CSS for Modern Business Look
st.markdown("""
    <style>
    .main {
        background-color: #f4f7f9;
    }
    .stButton>button {
        width: 100%;
        border-radius: 4px;
        height: 2.5em;
        background-color: #1a73e8;
        color: white;
        font-weight: 600;
        border: none;
        font-size: 14px;
    }
    .stButton>button:hover {
        background-color: #1557b0;
        color: white;
    }
    .download-card {
        background-color: white;
        padding: 10px 15px;
        border-radius: 6px;
        border: 1px solid #e0e0e0;
        margin-bottom: 8px;
    }
    .bold-header {
        font-weight: 800 !important;
        font-size: 24px !important;
        color: #202124;
        margin-bottom: 15px;
    }
    .status-text {
        font-size: 13px;
        font-weight: 500;
    }
    .status-finished {
        color: #28a745 !important;
        font-weight: bold;
    }
    .completed-list {
        background-color: white;
        padding: 12px;
        border-radius: 6px;
        border: 1px solid #e0e0e0;
    }
    /* Compact inputs */
    .stTextInput>div>div>input {
        padding: 5px 10px;
        font-size: 14px;
    }
    </style>
    """, unsafe_allow_html=True)

# Session State Initialization
if 'processes' not in st.session_state:
    st.session_state.processes = {} # {index: subprocess.Popen}
if 'progress' not in st.session_state:
    st.session_state.progress = {i: 0.0 for i in range(10)}
if 'status' not in st.session_state:
    st.session_state.status = {i: "Idle" for i in range(10)}
if 'completed' not in st.session_state:
    st.session_state.completed = []
if 'auto_next' not in st.session_state:
    st.session_state.auto_next = False
if 'cookie_file' not in st.session_state:
    st.session_state.cookie_file = ""

def get_completed_files():
    if os.path.exists(OUTPUT_DIR):
        return [f for f in os.listdir(OUTPUT_DIR) if f.endswith('.mp4')]
    return []

def start_download(i, link):
    st.session_state.status[i] = "Downloading..."
    st.session_state.progress[i] = 0.0
    
    cmd = [
        "yt-dlp", 
        "--newline",
        "--progress",
        "-f", "bestvideo+bestaudio/best", # Force maximum resolution
        "-o", f"{OUTPUT_DIR}/%(title)s.%(ext)s",
    ]
    
    # Add cookies if provided
    if st.session_state.cookie_file and os.path.exists(st.session_state.cookie_file):
        cmd.extend(["--cookies", st.session_state.cookie_file])
    
    cmd.append(link)
    
    process = subprocess.Popen(
        cmd, 
        stdout=subprocess.PIPE, 
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        universal_newlines=True
    )
    st.session_state.processes[i] = process

st.session_state.completed = get_completed_files()

# Sidebar for Global Settings
with st.sidebar:
    st.markdown('<p class="bold-header" style="font-size:20px !important;">⚙️ Global Settings</p>', unsafe_allow_html=True)
    st.session_state.cookie_file = st.text_input("Cookie File Path (Optional)", value=st.session_state.cookie_file, placeholder="e.g. bilibili_cookies.txt")
    st.info("💡 Pro Tip: Use a cookie file to unlock 1080p, 4K, and high bitrate videos.")
    
    st.markdown("---")
    st.session_state.auto_next = st.checkbox("Sequential Download Mode", value=st.session_state.auto_next)
    st.write("Automatically start the next link in the queue.")

# Header
st.markdown('<p class="bold-header">📺 Bilibili Pro Downloader</p>', unsafe_allow_html=True)

# Main Layout
col1, col2 = st.columns([3, 1])

with col1:
    st.markdown('<p style="font-weight:700; font-size:18px;">📥 Download Queue (Max Resolution Enabled)</p>', unsafe_allow_html=True)
    
    # 10 Input Slots
    links = {}
    for i in range(10):
        with st.container():
            st.markdown(f'<div class="download-card">', unsafe_allow_html=True)
            c1, c2, c3 = st.columns([5, 1, 1])
            
            link = c1.text_input(f"Link #{i+1}", key=f"link_{i}", placeholder="Paste Bilibili URL here...", label_visibility="collapsed")
            links[i] = link
            
            # Status and Progress
            status = st.session_state.status[i]
            status_class = "status-finished" if status == "Finished" else ""
            
            c2.markdown(f'<p class="status-text {status_class}">{status}</p>', unsafe_allow_html=True)
            
            # Buttons
            if status == "Downloading...":
                if c3.button("Stop", key=f"stop_{i}"):
                    if i in st.session_state.processes:
                        st.session_state.processes[i].terminate()
                        del st.session_state.processes[i]
                        st.session_state.status[i] = "Stopped"
                        st.rerun()
            else:
                if c3.button("Start", key=f"start_{i}", disabled=not link):
                    start_download(i, link)
                    st.rerun()
            
            st.progress(st.session_state.progress[i])
            st.markdown('</div>', unsafe_allow_html=True)

with col2:
    st.markdown('<p style="font-weight:700; font-size:18px;">✅ Completed</p>', unsafe_allow_html=True)
    if st.session_state.completed:
        st.markdown('<div class="completed-list">', unsafe_allow_html=True)
        # Using a list box as requested
        selected_file = st.selectbox("History", st.session_state.completed, label_visibility="collapsed")
        
        for file in st.session_state.completed[-10:]: # Show last 10
            file_path = os.path.join(OUTPUT_DIR, file)
            if os.path.exists(file_path):
                c1, c2, c3 = st.columns([3, 1, 1])
                c1.markdown(f'<p style="font-size:12px; margin:0; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;">• {file}</p>', unsafe_allow_html=True)
                
                # Save to Device Button
                with open(file_path, "rb") as f:
                    c2.download_button(
                        label="💾",
                        data=f,
                        file_name=file,
                        mime="video/mp4",
                        key=f"dl_{file}"
                    )
                
                # Delete Button
                if c3.button("🗑️", key=f"del_{file}"):
                    os.remove(file_path)
                    st.session_state.completed = get_completed_files()
                    st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.info("No downloads yet.")

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("Refresh List"):
        st.session_state.completed = get_completed_files()
        st.rerun()

# Background Progress Monitor
any_running = False
for i, proc in list(st.session_state.processes.items()):
    any_running = True
    if proc.poll() is None: # Still running
        # Read output without blocking
        try:
            line = proc.stdout.readline()
            if line:
                match = re.search(r'(\d+\.\d+)%', line)
                if match:
                    st.session_state.progress[i] = float(match.group(1)) / 100.0
                    st.session_state.status[i] = f"{match.group(1)}%"
        except:
            pass
    else:
        # Process finished
        st.session_state.status[i] = "Finished"
        st.session_state.progress[i] = 1.0
        st.session_state.completed = get_completed_files()
        del st.session_state.processes[i]
        
        # Auto-next logic
        if st.session_state.auto_next:
            next_idx = i + 1
            if next_idx < 10 and links[next_idx] and st.session_state.status[next_idx] in ["Idle", "Stopped"]:
                start_download(next_idx, links[next_idx])
        
        st.rerun()

# Auto-refresh if any process is running
if any_running:
    time.sleep(0.1)
    st.rerun()
