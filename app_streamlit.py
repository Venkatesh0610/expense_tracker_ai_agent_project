import os
import subprocess
import time
import requests
import streamlit as st
import pandas as pd
import plotly.express as px
import uuid
import socket
import sys
import json
from dotenv import load_dotenv
load_dotenv()

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
        # Test if python can parse the string as valid JSON metadata
        parsed_json = json.loads(raw_env)
        print(f"✅ [Env Check] JSON parsing successful!")
        print(f"📋 [Env Check] Target Project ID: {parsed_json.get('project_id')}")
        print(f"📋 [Env Check] Target Client Email: {parsed_json.get('client_email')}")
        
        # Check if the private key structure is intact
        pk = parsed_json.get("private_key", "")
        if "-----BEGIN PRIVATE KEY-----" in pk and "-----END PRIVATE KEY-----" in pk:
            print("✅ [Env Check] Cryptographic private key boundaries are valid.")
        else:
            print("❌ [Env Check] Missing header/footer boundaries inside 'private_key'.")
            
    except json.JSONDecodeError as e:
        print(f"❌ [Env Check] String found, but it is NOT valid JSON. Parse Error: {e}")
        # Print a snippet of the beginning to see what python-dotenv actually grabbed
        print(f"📌 [Env Check] Snippet captured: {raw_env[:60]}...")
print("----------------------------------------")
# --- DIAGNOSTIC LOG MATRIX END ---

# =====================================================
# 🚀 DIAGNOSTIC & AUTOMATED BACKEND INITIALIZATION BLOCK
# =====================================================
print("🔍 Streamlit Lifecycle: Initializing script execution path...", flush=True)

def is_port_in_use(port: int) -> bool:
    """Checks if a local port is already bound by a running process."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        in_use = s.connect_ex(('127.0.0.1', port)) == 0
        print(f"📡 [Port Scanner] Checking local port {port} -> In Use: {in_use}", flush=True)
        return in_use

@st.cache_resource
def start_fastapi_server():
    """
    Spins up the FastAPI server as a background process within the 
    Streamlit Community Cloud container env matrix, only if not already active.
    Flushes traceback errors directly to the cloud terminal for fast debugging.
    """
    port = 8000
    print(f"🚀 [Backend Engine] start_fastapi_server() triggered. Scanning port {port}...", flush=True)
    
    if is_port_in_use(port):
        print(f"ℹ️ [Backend Engine] Port {port} already bound. Reusing existing active background worker process context.", flush=True)
        return None

    print(f"⚡ [Backend Engine] Port {port} is free! Attempting to launch Uvicorn background process...", flush=True)
    
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        
        # 🎯 FIX: Passing sys.stdout and sys.stderr directly bypasses internal pipes 
        # and flushes FastAPI runtime 500 exceptions instantly onto your dashboard console.
        process = subprocess.Popen(
            ["uvicorn", "app:app", "--host", "127.0.0.1", "--port", str(port)],
            cwd=current_dir,
            stdout=sys.stdout,
            stderr=sys.stderr,
            text=True
        )
        
        print("⏳ [Backend Engine] Waiting 2.0 seconds for port binding warm-up context...", flush=True)
        time.sleep(2.0)
        
        poll_status = process.poll()
        if poll_status is not None:
            print(f"❌ [Backend Engine] Critical failure! Process exited immediately on boot with status code {poll_status}.", flush=True)
            return None
            
        print(f"🔥 [Backend Engine] Uvicorn worker process successfully detached into background! PID: {process.pid}", flush=True)
        return process
        
    except Exception as launch_err:
        print(f"❌ [Backend Engine] Exception caught while executing subprocess Popen: {str(launch_err)}", flush=True)
        return None

# Trigger background execution pipeline safely
fastapi_process = start_fastapi_server()

# Target endpoint mapping: fallback dynamically based on environment conditions
if os.getenv("STREAMLIT_RUNTIME_ENV") or "STREAMLIT_SERVER_PORT" in os.environ:
    API_URL = "http://localhost:8000"
    print(f"🌐 [Network Route] Production Cloud Context detected. Targeting URL: {API_URL}", flush=True)
else:
    API_URL = "http://127.0.0.1:8000"
    print(f"🏠 [Network Route] Local Environment context detected. Targeting URL: {API_URL}", flush=True)

# Verify health status of the endpoint immediately during page load
try:
    print(f"📡 [Health Check] Pinging backend at {API_URL}/expenses ...", flush=True)
    
    # Emulate the baseline header matrix so the backend route doesn't crash on missing headers
    DEMO_SHEET_ID = os.getenv("SPREADSHEET_ID")
    test_headers = {"X-Sheet-ID": str(DEMO_SHEET_ID), "Content-Type": "application/json"}
    
    health_check = requests.get(f"{API_URL}/expenses", headers=test_headers, timeout=3)
    print(f"📡 [Health Check] Response status code received: {health_check.status_code}", flush=True)
    
    if health_check.status_code == 500:
        print("🚨 [Health Check] Detected an HTTP 500 error! Check lines directly below in the terminal logs for the python traceback.", flush=True)
except Exception as check_err:
    print(f"⚠️ [Health Check] Warning: Pre-flight connection check failed. Reason: {str(check_err)}", flush=True)

# =====================================================
# 1. Page Configuration Matrix
# =====================================================
st.set_page_config(
    page_title="Expense Tracker AI Agent",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize Workspace State Layout Controls & Persistent Sheet Keys
if "show_chat" not in st.session_state:
    st.session_state.show_chat = True
if "active_user_sheet_id" not in st.session_state:
    st.session_state.active_user_sheet_id = ""

# 2. Premium Custom Styling & Layout Locking Matrix
st.markdown("""
<style>
    /* Metric Cards Custom Styling */
    [data-testid="stMetric"] {
        background: #f587a1;
        padding: 16px 20px;
        border-radius: 12px;
        box-shadow: 0px 4px 10px rgba(0, 0, 0, 0.2);
        border: 1px solid #334155;
    }
    
    /* Compact top padding */
    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 1rem;
    }
    
    /* Pinned layout rules for fluid full-screen sizing */
    iframe {
        border-radius: 8px;
    }
</style>
""", unsafe_allow_html=True)

# 3. App Header Row Matrix
header_col1, header_col2 = st.columns([8, 2])
with header_col1:
    st.title("Expense Tracker AI Agent")
    st.markdown("Track your spending, edit transactions live, and chat with an intelligent assistant to instantly log your data.")
with header_col2:
    st.markdown("<br>", unsafe_allow_html=True)
    chat_btn_label = "❌ Close Assistant" if st.session_state.show_chat else "🤖 AI Assistant"
    if st.button(chat_btn_label, use_container_width=True, type="secondary"):
        st.session_state.show_chat = not st.session_state.show_chat
        st.rerun()

st.divider()

# =====================================================
# SIDEBAR: DATA TARGET CONFIGURATION
# =====================================================
st.sidebar.markdown("### ⚙️ Data Configuration")

# Fallback Demo Google Sheet ID context 
DEMO_SHEET_ID = os.getenv("SPREADSHEET_ID")

# Capture sheet ID text input cleanly without tearing out multi-page cache matrices
user_sheet_id = st.sidebar.text_input(
    label="Google Sheet ID",
    value=st.session_state.active_user_sheet_id,
    placeholder="Paste your custom sheet ID here...",
    key="config_sheet_input_widget",
    help="Leave blank to experiment using the built-in global demo workspace."
)

# Sync visual widget modification explicitly to the background storage profile matrix
st.session_state.active_user_sheet_id = user_sheet_id

# Parse active operational database destination identity
active_sheet_id = user_sheet_id.strip() if user_sheet_id.strip() else DEMO_SHEET_ID

# Direct interface connection confirmation banner
if user_sheet_id.strip():
    st.sidebar.success("🔗 Connected to Custom Workspace Matrix")
else:
    st.sidebar.info("💡 Running on Default Demo Environment")

# Universal transactional routing context matrix (Passes UI Sheet ID to API)
request_headers = {
    "X-Sheet-ID": str(active_sheet_id),
    "Content-Type": "application/json"
}

# =====================================================
# LIVE DATA EXTRACTION 
# =====================================================
try:
    response = requests.get(f"{API_URL}/expenses", headers=request_headers, timeout=3)
    if response.status_code == 200:
        expenses = response.json().get("expenses", [])
    else:
        expenses = []
except Exception:
    expenses = []

# Build core DataFrame
if expenses:
    df = pd.DataFrame(expenses)
    if "id" not in df.columns:
        df["id"] = [str(uuid.uuid4())[:8] for _ in range(len(df))]
    df["date"] = pd.to_datetime(df["date"]).dt.date
    df["amount"] = df["amount"].astype(float)
else:
    df = pd.DataFrame(columns=["id", "date", "category", "amount", "description"])

# =====================================================
# SIDEBAR FILTERS
# =====================================================
st.sidebar.divider()
st.sidebar.markdown("### 🔍 Filter Engine")

date_range = st.sidebar.date_input(
    "Select Date Range",
    value=[]
)

category_filter = st.sidebar.multiselect(
    "Category",
    options=sorted(df["category"].dropna().unique()) if not df.empty else []
)

description_filter = st.sidebar.text_input(
    "Search Description"
)

# --- Apply Filters Dynamically ---
filtered_df = df.copy()

if not filtered_df.empty:
    if category_filter:
        filtered_df = filtered_df[filtered_df["category"].isin(category_filter)]

    if description_filter:
        filtered_df = filtered_df[filtered_df["description"].str.contains(description_filter, case=False, na=False)]

    if len(date_range) == 2:
        filtered_df = filtered_df[
            (filtered_df["date"] >= date_range[0]) & 
            (filtered_df["date"] <= date_range[1])
        ]

# =====================================================
# DUAL PANEL LAYOUT DESIGN
# =====================================================
if st.session_state.show_chat:
    dash_col, chat_col = st.columns([6.2, 3.8], gap="medium")
else:
    dash_col = st.container()
    chat_col = None

# -----------------------------------------------------
# LEFT VIEW PANEL: 📊 ANALYTICS & INTERACTIVE LEDGER
# -----------------------------------------------------
with dash_col:
    # --- KPI Cards Row ---
    c1, c2, c3, c4 = st.columns(4)
    
    total_spend = filtered_df['amount'].sum() if not filtered_df.empty else 0.0
    total_count = len(filtered_df)
    avg_spend = filtered_df['amount'].mean() if not filtered_df.empty else 0.0
    
    try:
        top_category = filtered_df.groupby("category")["amount"].sum().idxmax() if not filtered_df.empty else "N/A"
    except Exception:
        top_category = "N/A"
        
    c1.metric("💵 Total Spending", f"₹{total_spend:,.2f}")
    c2.metric("🧾 Total Expenses", f"{total_count}")
    c3.metric("📊 Average", f"₹{avg_spend:,.2f}")
    c4.metric("🏆 Top Category", str(top_category))
    
    st.markdown("""
    <div style="background-color: #0F172A; padding: 10px 14px; border-radius: 8px; font-size: 0.8rem; color: #94A3B8; border: 1px solid #1E293B; margin-top: 10px; margin-bottom: 15px;">
    <strong>💡 Quick Stats Explained:</strong> 
    
    <b> Total Spending</b> is cumulative cost; 
    <b>Total Expenses</b> tracks count; 
    <b>Average</b> is transaction weight; 
    <b>Top Category</b> flags maximum budget consumption.
    </div>
    """, unsafe_allow_html=True)
    
    # --- 1. DYNAMIC TRANSACTION TABLE ---
    st.subheader("📋 Transaction History")
    
    if not filtered_df.empty:
        filtered_df["id"] = filtered_df["id"].fillna("").apply(lambda x: x if x != "" else str(uuid.uuid4())[:8])

    # 💡 Extract dynamic categories directly from active spreadsheet dataset
    existing_categories = sorted(list(df["category"].dropna().unique())) if not df.empty else []
    fallback_categories = ["Food", "Shopping", "Utilities", "Travel", "Entertainment", "Healthcare", "Education", "Others"]
    dynamic_categories = sorted(list(set(existing_categories + fallback_categories)))

    edited_df = st.data_editor(
        filtered_df,
        key="ledger_editor",
        use_container_width=True,
        hide_index=True,
        num_rows="dynamic",
        height=200,  
        column_order=["date", "category", "amount", "description"],  
        column_config={
            "date": st.column_config.DateColumn("Date", required=True),
            "category": st.column_config.SelectboxColumn("Category", options=dynamic_categories, required=True),
            "amount": st.column_config.NumberColumn("Amount (₹)", min_value=0, required=True, format="₹%.2f"),
            "description": st.column_config.TextColumn("Description", required=True)
        }
    )
    
    # Process Save Action
    crud_save_col1, crud_save_col2, crud_save_col3 = st.columns([3.5, 3.5, 3])
    with crud_save_col1:
        if st.button("💾 Save Database Changes", use_container_width=True, type="primary"):
            try:
                orig_ids = set(filtered_df["id"].dropna().astype(str).tolist())
                new_ids = set(edited_df["id"].dropna().astype(str).tolist())
                deleted_ids = orig_ids - new_ids
                
                for d_id in deleted_ids:
                    requests.delete(f"{API_URL}/expenses/{d_id}", headers=request_headers, timeout=2)
                
                for _, row in edited_df.iterrows():
                    row_id = str(row.get("id", ""))
                    payload = {
                        "date": str(row["date"]),
                        "category": row["category"],
                        "amount": float(row["amount"]),
                        "description": row["description"]
                    }
                    
                    if not row_id or row_id not in orig_ids:
                        requests.post(f"{API_URL}/expenses", json=payload, headers=request_headers, timeout=2)
                    else:
                        orig_match = filtered_df[filtered_df["id"].astype(str) == row_id]
                        if not orig_match.empty:
                            if (str(orig_match.iloc[0]["date"]) != str(row["date"])) or \
                               (orig_match.iloc[0]["category"] != row["category"]) or \
                               (float(orig_match.iloc[0]["amount"]) != float(row["amount"])) or \
                               (orig_match.iloc[0]["description"] != row["description"]):
                                requests.put(f"{API_URL}/expenses/{row_id}", json=payload, headers=request_headers, timeout=2)
                
                st.toast("✅ Database synchronized seamlessly!", icon="🔥")
                st.rerun()
            except Exception as ex:
                st.error(f"Sync Pipeline Interrupted: Backend offline or structural mutation error.")
                
    with crud_save_col2:
        st.download_button(
            label="📄 Export to CSV",
            data=filtered_df.to_csv(index=False),
            file_name="expenses_export.csv",
            mime="text/csv",
            use_container_width=True
        )
                
    st.markdown("<br>", unsafe_allow_html=True)

    # --- 2. INTEGRATED GRAPH ARCHITECTURE ---
    if not filtered_df.empty:
        unique_categories = sorted(filtered_df["category"].unique())
        color_palette = px.colors.qualitative.G10
        color_map = {cat: color_palette[i % len(color_palette)] for i, cat in enumerate(unique_categories)}

        g_col1, g_col2 = st.columns(2)
        with g_col1:
            st.markdown("#### 🟢 Category Allocation")
            fig_pie = px.pie(filtered_df, names="category", values="amount", hole=0.4, color="category", color_discrete_map=color_map)
            fig_pie.update_layout(margin=dict(t=5, b=5, l=5, r=5), height=200, showlegend=True)
            st.plotly_chart(fig_pie, use_container_width=True, config={'displayModeBar': False})
            
        with g_col2:
            st.markdown("#### 📊 Category Volumes")
            cat_totals = filtered_df.groupby("category")["amount"].sum().reset_index()
            fig_bar = px.bar(cat_totals, x="category", y="amount", text_auto='.2s', color="category", color_discrete_map=color_map)
            fig_bar.update_layout(margin=dict(t=5, b=5, l=5, r=5), height=200, showlegend=False, xaxis_title=None, yaxis_title=None)
            st.plotly_chart(fig_bar, use_container_width=True, config={'displayModeBar': False})
            
        st.markdown("<br>", unsafe_allow_html=True)
        
        # --- Deep AI Financial Recommendations ---
        with st.expander("🧠 Deep AI Financial Recommendations", expanded=False):
            st.markdown("<p style='font-size:0.9rem; color:#94A3B8; margin-bottom:12px;'>Click the generation action engine below to let your AI Agent parse the telemetry matrix and yield optimization vectors.</p>", unsafe_allow_html=True)
            
            if st.button("✨ Generate Custom Recommendation Report", use_container_width=True, type="secondary"):
                with st.spinner("Analyzing active data engine parameters..."):
                    telemetry_context = (
                        f"Give me actionable financial optimization recommendations based on my real-time expense data. "
                        f"Here is the budget context summary: Total spending is ₹{total_spend:,.2f} spread across {total_count} transactions. "
                        f"The statistical mathematical average per item is ₹{avg_spend:,.2f}. The highest budget pressure sector is my '{top_category}' category. "
                        f"Provide 3 hyper-targeted bullet points outlining savings tips, vector patterns, and optimization strategies."
                    )
                    
                    try:
                        insight_payload = {"message": telemetry_context}
                        insight_response = requests.post(f"{API_URL}/chat", json=insight_payload, headers=request_headers, timeout=12)
                        
                        if insight_response.status_code == 200:
                            ai_recommendation = insight_response.json().get("response", "Could not generate strategy parameters.")
                            if isinstance(ai_recommendation, dict) and "text" in ai_recommendation:
                                st.info(ai_recommendation["text"])
                            else:
                                st.info(str(ai_recommendation))
                        else:
                            st.error(f"Failed to extract strategic data. Backend server returned status code: {insight_response.status_code}")
                    except Exception as target_err:
                        st.error(f"Insight Generation Interrupted: Pipeline offline. Details: `{str(target_err)}`")

# -----------------------------------------------------
# RIGHT VIEW PANEL: 🤖 COMPACT SCALED CO-PILOT ASSISTANT
# -----------------------------------------------------
if chat_col and st.session_state.show_chat:
    with chat_col:
        st.markdown("### 🤖 AI Agent Chat")
        st.markdown("<div style='margin-bottom:8px;'></div>", unsafe_allow_html=True)

        if "messages" not in st.session_state:
            st.session_state.messages = [
                {"role": "assistant", "content": "Hello! I am your automated budget agent. Tell me what you spent (e.g., *'I spent ₹450 on Coffee today'*) or ask questions about your history."}
            ]

        # 1. Render all history inside the message container first
        with st.container(height=545, border=True):
            for message in st.session_state.messages:
                with st.chat_message(message["role"]):
                    content = message["content"]
                    
                    if isinstance(content, dict) and "text" in content:
                        st.markdown(content["text"])
                        if "data" in content and content["data"]:
                            data_obj = content["data"]
                            if isinstance(data_obj, list):
                                st.dataframe(pd.DataFrame(data_obj), use_container_width=True, hide_index=True)
                            elif isinstance(data_obj, dict):
                                formatted_data = {
                                    "Metrics Properties": [k.replace("_", " ").title() for k in data_obj.keys() if k != "expense_id"],
                                    "Telemetry Values": [str(v) for k in data_obj.keys() for v in [data_obj[k]] if k != "expense_id"]
                                }
                                if "amount" in data_obj:
                                    try:
                                        keys_list = [k for k in data_obj.keys() if k != "expense_id"]
                                        amt_idx = keys_list.index("amount")
                                        formatted_data["Telemetry Values"][amt_idx] = f"₹{float(data_obj['amount']):,.2f}"
                                    except Exception:
                                        pass
                                st.table(pd.DataFrame(formatted_data))
                    elif isinstance(content, list):
                        if len(content):
                            st.dataframe(pd.DataFrame(content), use_container_width=True, hide_index=True)
                    else:
                        st.markdown(str(content))

        # 2. Capture text user input outside the chat container block
        user_input = st.chat_input("Ask your AI Agent or enter a new expense...")

        if user_input:
            # Append user entry to history immediately and trigger a rapid UI redraw
            st.session_state.messages.append({"role": "user", "content": user_input})
            st.rerun()

# 3. Handle asynchronous backend processing during page refresh lifecycle
if "messages" in st.session_state and st.session_state.messages[-1]["role"] == "user":
    latest_user_query = st.session_state.messages[-1]["content"]
    
    with chat_col:
        with st.spinner("AI Agent thinking..."):
            try:
                chat_payload = {"message": latest_user_query}
                response = requests.post(f"{API_URL}/chat", json=chat_payload, headers=request_headers, timeout=10)
                
                if response.status_code == 200:
                    assistant_reply = response.json().get("response", "Transaction modification complete.")
                else:
                    assistant_reply = f"⚠️ Server exception verified with status code: {response.status_code}"
            except Exception as e:
                assistant_reply = f"❌ Error communicating with backend server agent context: `{str(e)}`"

            # Append assistant reply and reload to finalize the cycle cleanly
            st.session_state.messages.append({"role": "assistant", "content": assistant_reply})
            st.rerun()