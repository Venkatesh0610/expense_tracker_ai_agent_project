# app.py
import os
import json
import time
import threading
import uvicorn
import streamlit as st
from dotenv import load_dotenv

# --- 1. FORCE FULL PAGE WIDTH (Must be the absolute first Streamlit command) ---
st.set_page_config(
    page_title="AI Expense Tracker",
    layout="wide",  # This makes the UI render in full page width
    initial_sidebar_state="expanded"
)

# Load local environment variables if present (.env)
load_dotenv()

# Import our backend & frontend modules
from backend_agent import app as fastapi_app
from app_ui import render_ui

# --- DIAGNOSTIC LOG MATRIX START ---
print("🔍 [Env Check] Fetching GOOGLE_CREDENTIALS_JSON...")
raw_env = os.getenv("GOOGLE_CREDENTIALS_JSON")
DEFAULT_SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")
print(f"🔍 [Env Check] Fetching DEFAULT_SPREADSHEET_ID : {DEFAULT_SPREADSHEET_ID}")

if raw_env is None:
    print("❌ [Env Check] GOOGLE_CREDENTIALS_JSON is completely missing (Returned None).")
elif raw_env.strip() == "":
    print("⚠️ [Env Check] GOOGLE_CREDENTIALS_JSON exists but is completely blank.")
else:
    print(f"✅ [Env Check] Raw string found! Length: {len(raw_env)} characters.")
    try:
        parsed_json = json.loads(raw_env)
        print("✅ [Env Check] JSON parsing successful!")
        print(f"📋 [Env Check] Target Project ID: {parsed_json.get('project_id')}")
        print(f"📋 [Env Check] Target Client Email: {parsed_json.get('client_email')}")
        pk = parsed_json.get("private_key", "")
        if "-----BEGIN PRIVATE KEY-----" in pk and "-----END PRIVATE KEY-----" in pk:
            print("✅ [Env Check] Cryptographic private key boundaries are valid.")
        else:
            print("❌ [Env Check] Missing header/footer boundaries inside 'private_key'.")
    except json.JSONDecodeError as e:
        print(f"❌ [Env Check] String found, but it is NOT valid JSON. Parse Error: {e}")
print("----------------------------------------")
# --- DIAGNOSTIC LOG MATRIX END ---


# --- BACKGROUND FASTAPI BOOTSTRAPPER ---
def run_fastapi_in_background():
    uvicorn.run(fastapi_app, host="127.0.0.1", port=8000, log_level="warning")

@st.cache_resource
def init_backend_runtime():
    print("⚡ [Thread Manager] Spinning up background Uvicorn API runtime...", flush=True)
    server_thread = threading.Thread(target=run_fastapi_in_background, daemon=True)
    server_thread.start()
    time.sleep(2.0)  # Increased slightly to ensure FastAPI is fully healthy before front-end queries it
    return True

# Initialize Thread Pool Execution
init_backend_runtime()

# Render User Interface Page Frame
render_ui(default_spreadsheet_id=DEFAULT_SPREADSHEET_ID)