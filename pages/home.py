import requests
import streamlit as st
import pandas as pd
import plotly.express as px
import uuid
API_URL = "http://127.0.0.1:8000"

# 1. Page Configuration
st.set_page_config(
    page_title="Project Walkthrough",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize Session States
if "show_chat" not in st.session_state:
    st.session_state.show_chat = True
if "demo_active" not in st.session_state:
    st.session_state.demo_active = False

# Custom Styling (Merged metric card styles, iframe, features, and technology badges)
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

    /* Key Feature Cards styling */
    .feature-card {
        background: #1e293b;
        padding: 20px;
        border-radius: 10px;
        border: 1px solid #334155;
        height: 100%;
        min-height: 180px;
        box-shadow: 0px 4px 6px rgba(0, 0, 0, 0.1);
    }
    .feature-title {
        font-weight: bold;
        font-size: 1.1rem;
        color: #38bdf8;
        margin-bottom: 10px;
    }
    .feature-text {
        font-size: 0.9rem;
        color: #cbd5e1;
    }

    /* Tech Cards styling */
    .tech-card {
        background: #020024;
        background: linear-gradient(90deg, rgba(2, 0, 36, 1) 0%, rgba(9, 9, 121, 1) 35%, rgba(0, 212, 255, 1) 100%);
        padding: 15px;
        border-radius: 8px;
        border: 1px solid #1e293b;
        display: flex;
        align-items: center;
        gap: 15px;
        font-weight: 500;
        color: #f8fafc;
    }
    .tech-card img {
        object-fit: contain;
    }
</style>
""", unsafe_allow_html=True)


# =====================================================
# HOME PAGE SECTION (WALKTHROUGH & ARCHITECTURE)
# =====================================================
if not st.session_state.demo_active:
    st.title("🚀Multi-Tool Expense Tracker AI Agent")
    st.markdown("---")
    
    # Showcase technical highlights
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("""
        ### 🛠️ System Architecture
        * **Frontend:** Built with Streamlit for highly interactive data representation.
        * **AI Agent Orchestration:** Powered by a Python AI Agent equipped with specialized tool-calling capabilities to append, edit, and delete ledger entries dynamically.
        * **Real-time Database:** Direct integration with the **Google Sheets API** for live CRUD operations and persistent spreadsheet synchronization.
        """)
    with col_b:
        st.markdown("""
        ### 💡 Key Features Highlight
        * **Conversational Control:** Modify your budget ledger seamlessly in natural language through Python agent tools.
        * **Bi-directional Sync:** Live data editor automatically syncs structural changes directly to your Google Sheet.
        * **Telemetry Matrix:** Built-in calculation engine tracking cumulative spend and category weighting.
        """)
        
    st.markdown("<br>", unsafe_allow_html=True)

    # --- KEY CAPABILITIES SECTION ---
    st.subheader("💡 Key Capabilities")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(
            "<div class='feature-card'><div class='feature-title'>➕ Smart Appending</div><div class='feature-text'>Log new expenses instantly just by chatting. The agent parses descriptions, amounts, and categories automatically.</div></div>",
            unsafe_allow_html=True)
    with col2:
        st.markdown(
            "<div class='feature-card'><div class='feature-title'>✏️ Conversational Editing</div><div class='feature-text'>Need to fix an entry? Ask the agent to adjust amounts, dates, or details in place using dynamic modification tools.</div></div>",
            unsafe_allow_html=True)
    with col3:
        st.markdown(
            "<div class='feature-card'><div class='feature-title'>❌ Quick Deletion</div><div class='feature-text'>Remove incorrect or duplicate transactions easily by asking the agent to delete them from your spreadsheet records.</div></div>",
            unsafe_allow_html=True)
    with col4:
        st.markdown(
            "<div class='feature-card'><div class='feature-title'>🧠 LLM Recommendations</div><div class='feature-text'>Get tailored, real-time financial optimizations and budget recommendations generated through Groq.</div></div>",
            unsafe_allow_html=True)

    # --- TECHNOLOGIES USED SECTION ---
    st.divider()
    st.subheader("🛠️ Technologies Used")
    tech_col1, tech_col2, tech_col3, tech_col4,tech_col5 = st.columns(5)

    with tech_col1:
        st.markdown(
            "<div class='tech-card'><img src='https://images.seeklogo.com/logo-png/60/2/groq-icon-logo-png_seeklogo-605779.png' width='30'/>Groq API</div>",
            unsafe_allow_html=True
        )
    with tech_col2:
        st.markdown(
            "<div class='tech-card'><img src='https://cdn-icons-png.flaticon.com/128/281/281761.png' width='30'/>Google Sheets API</div>",
            unsafe_allow_html=True
        )
    with tech_col3:
        st.markdown(
            "<div class='tech-card'><img src='https://cdn-icons-png.flaticon.com/128/14657/14657058.png' width='30'/>Python Agents</div>",
            unsafe_allow_html=True
        )
    with tech_col4:
        st.markdown(
            "<div class='tech-card'><img src='https://images.seeklogo.com/logo-png/44/2/streamlit-logo-png_seeklogo-441815.png' width='30'/>Streamlit</div>",
            unsafe_allow_html=True
        )
    with tech_col5:
        st.markdown(
            "<div class='tech-card'><img src='https://cdn-icons-png.flaticon.com/128/1822/1822899.png' width='30'/>Python</div>",
            unsafe_allow_html=True
        )

    # --- CONNECT WITH ME SECTION ---
    st.divider()
    st.markdown(
        """
        <div style="text-align: center; width: 100%; margin-top: 20px; margin-bottom: 20px;">
            <div style="display: flex; justify-content: center; gap: 35px; flex-wrap: wrap; align-items: center;">
                <a href="https://www.youtube.com/@avenkatesh0610" target="_blank" style="text-decoration: none;">
                    <img src="https://cdn-icons-png.flaticon.com/512/1384/1384060.png" width="35" height="35" title="YouTube"/>
                </a>
                <a href="https://medium.com/@avenkatesh0610" target="_blank" style="text-decoration: none;">
                    <img src="https://cdn-icons-png.flaticon.com/512/2111/2111505.png" width="35" height="35" title="Medium"/>
                </a>
                <a href="https://github.com/Venkatesh0610" target="_blank" style="text-decoration: none;">
                    <img src="https://cdn-icons-png.flaticon.com/512/2111/2111432.png" width="35" height="35" title="GitHub"/>
                </a>
                <a href="https://www.linkedin.com/in/venkatesh-a-400459191/" target="_blank" style="text-decoration: none;">
                    <img src="https://cdn-icons-png.flaticon.com/128/3536/3536505.png" width="35" height="35" title="LinkedIn"/>
                </a>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    
    # Single CTA button to launch the original interface
    # if st.button("✨ Launch Live Application Demo", use_container_width=True, type="primary"):
    #     st.session_state.demo_active = True
    #     st.rerun()

# =====================================================
# ORIGINAL APPLICATION INTERFACE (RUNS WHEN DEMO IS ACTIVE)
# =====================================================
else:
    # 3. App Header Row
    header_col1, header_col2, header_col3 = st.columns([6, 2, 2])
    with header_col1:
        st.title("Expense Tracker AI Agent")
        st.markdown("Track your spending, edit transactions live, and chat with an intelligent assistant to instantly log your data.")
    with header_col2:
        st.markdown("<br>", unsafe_allow_html=True)
        chat_btn_label = "❌ Close Assistant" if st.session_state.show_chat else "🤖 AI Assistant"
        if st.button(chat_btn_label, use_container_width=True, type="secondary"):
            st.session_state.show_chat = not st.session_state.show_chat
            st.rerun()
    with header_col3:
        st.markdown("<br>", unsafe_allow_html=True)
        # Return back to the landing page
        if st.button("🏠 Back to Overview", use_container_width=True, type="primary"):
            st.session_state.demo_active = False
            st.rerun()

    st.divider()

    # =====================================================
    # LIVE DATA EXTRACTION
    # =====================================================
    try:
        response = requests.get(f"{API_URL}/expenses", timeout=3)
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
    st.sidebar.header("🔍 Filter Engine")

    date_range = st.sidebar.date_input(
        "Select Date Range",
        value=[]
    )

    category_filter = st.sidebar.multiselect(
        "Category",
        options=sorted(df["category"].unique()) if not df.empty else []
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
        
        # KPI Descriptions Block
        st.markdown("""
        <div style="background-color: #0F172A; padding: 10px 14px; border-radius: 8px; font-size: 0.8rem; color: #94A3B8; border: 1px solid #1E293B; margin-top: 10px; margin-bottom: 15px;">
        <strong>💡 Quick Stats Explained:</strong> 
        
        <b> Total Spending</b> is cumulative cost; 
        <b>Total Expenses</b> tracks count; 
        <b>Average</b> is transaction weight; 
        <b>Top Category</b> flags maximum budget consumption.
        </div>
        """, unsafe_allow_html=True)
        
        # --- 1. SIMPLE TRANSACTION TABLE ---
        st.subheader("📋 Transaction History")
        
        if not filtered_df.empty:
            filtered_df["id"] = filtered_df["id"].fillna("").apply(lambda x: x if x != "" else str(uuid.uuid4())[:8])

        edited_df = st.data_editor(
            filtered_df,
            key="ledger_editor",
            use_container_width=True,
            hide_index=True,
            num_rows="dynamic",
            height=200,  # Locked height to preserve viewport consistency
            column_order=["date", "category", "amount", "description"],  # Hides database ID from users
            column_config={
                "date": st.column_config.DateColumn("Date", required=True),
                "category": st.column_config.SelectboxColumn("Category", options=["Food", "Shopping", "Utilities", "Travel", "Entertainment", "Healthcare", "Education", "Others"], required=True),
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
                        requests.delete(f"{API_URL}/expenses/{d_id}", timeout=2)
                    
                    for _, row in edited_df.iterrows():
                        row_id = str(row.get("id", ""))
                        payload = {
                            "date": str(row["date"]),
                            "category": row["category"],
                            "amount": float(row["amount"]),
                            "description": row["description"]
                        }
                        
                        if not row_id or row_id not in orig_ids:
                            requests.post(f"{API_URL}/expenses", json=payload, timeout=2)
                        else:
                            orig_match = filtered_df[filtered_df["id"].astype(str) == row_id]
                            if not orig_match.empty:
                                if (str(orig_match.iloc[0]["date"]) != str(row["date"])) or \
                                   (orig_match.iloc[0]["category"] != row["category"]) or \
                                   (float(orig_match.iloc[0]["amount"]) != float(row["amount"])) or \
                                   (orig_match.iloc[0]["description"] != row["description"]):
                                    requests.put(f"{API_URL}/expenses/{row_id}", json=payload, timeout=2)
                    
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
            
            # =====================================================
            # 🧠 ON-CLICK AUTOMATED AI INSIGHTS ENGINE
            # =====================================================
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
                            insight_response = requests.post(f"{API_URL}/chat", json=insight_payload, timeout=12)
                            
                            if insight_response.status_code == 200:
                                ai_recommendation = insight_response.json().get("response", "Could not generate strategy parameters.")
                                
                                # Standardize layout extraction display
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
                    {"role": "assistant", "content": "Hello! I am your multi-tool Python budget agent. I can append, edit, or delete items from your Google Sheet, and offer budget recommendations. How can I help you manage your funds today?"}
                ]

            # Fluid container dynamically scaled to align beautifully with the left panel components
            with st.container(height=545, border=True):
                for message in st.session_state.messages:
                    with st.chat_message(message["role"]):
                        content = message["content"]
                        
                        # A. Parse the structured structured compound dictionary response
                        if isinstance(content, dict) and "text" in content:
                            st.markdown(content["text"])
                            
                            if "data" in content and content["data"]:
                                data_obj = content["data"]
                                
                                # If response payload represents an array collection (like multiple search items)
                                if isinstance(data_obj, list):
                                    st.dataframe(pd.DataFrame(data_obj), use_container_width=True, hide_index=True)
                                
                                # If payload is a single model detail record (like an added/retrieved item)
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
                                    
                        # B. Legacy handling matrix for continuous straight arrays
                        elif isinstance(content, list):
                            if len(content):
                                st.dataframe(pd.DataFrame(content), use_container_width=True, hide_index=True)
                        
                        # C. Baseline plain text fallback
                        else:
                            st.markdown(str(content))

            user_input = st.chat_input("E.g., 'Append 450 for Food', 'Delete my coffee expense', or 'Suggest budget tips'...")

            if user_input:
                st.session_state.messages.append({"role": "user", "content": user_input})
                
                try:
                    chat_payload = {"message": user_input}
                    response = requests.post(f"{API_URL}/chat", json=chat_payload, timeout=10)
                    
                    if response.status_code == 200:
                        assistant_reply = response.json().get("response", "Transaction modification complete.")
                    else:
                        assistant_reply = f"⚠️ Server exception verified with status code: {response.status_code}"
                except Exception as e:
                    assistant_reply = f"❌ Error communicating with backend server agent context: `{str(e)}`"

                st.session_state.messages.append({"role": "assistant", "content": assistant_reply})
                st.rerun()