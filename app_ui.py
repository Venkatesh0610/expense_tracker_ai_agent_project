# app_ui.py
import uuid
import requests
import pandas as pd
import streamlit as st
import plotly.express as px

API_URL = "http://127.0.0.1:8000"

def render_ui(default_spreadsheet_id):
    # Initialize workspace state
    if "show_chat" not in st.session_state:
        st.session_state.show_chat = True
    if "active_user_sheet_id" not in st.session_state:
        st.session_state.active_user_sheet_id = ""

    # Styling Matrix
    st.markdown("""
    <style>
        [data-testid="stMetric"] {
            background: #f587a1;
            padding: 16px 20px;
            border-radius: 12px;
            box-shadow: 0px 4px 10px rgba(0, 0, 0, 0.2);
            border: 1px solid #334155;
        }
        .block-container {
            padding-top: 1.5rem;
            padding-bottom: 1rem;
        }
        iframe {
            border-radius: 8px;
        }
    </style>
    """, unsafe_allow_html=True)

    # Header Row
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

    # Sidebar: Data Configuration
    st.sidebar.markdown("### ⚙️ Data Configuration")
    user_sheet_id = st.sidebar.text_input(
        label="Google Sheet ID",
        value=st.session_state.active_user_sheet_id,
        placeholder="Paste your custom sheet ID here...",
        key="config_sheet_input_widget",
        help="Leave blank to experiment using the built-in global demo workspace."
    )
    st.session_state.active_user_sheet_id = user_sheet_id

    active_sheet_id = user_sheet_id.strip() if user_sheet_id.strip() else default_spreadsheet_id

    if user_sheet_id.strip():
        st.sidebar.success("🔗 Connected to Custom Workspace Matrix")
    else:
        st.sidebar.info("💡 Running on Default Demo Environment")

    request_headers = {
        "X-Sheet-ID": str(active_sheet_id),
        "Content-Type": "application/json"
    }

    # Fetch Data
    try:
        response = requests.get(f"{API_URL}/expenses", headers=request_headers, timeout=5)
        if response.status_code == 200:
            raw_data = response.json()
            # Safely handle both dicts containing 'expenses' and raw lists
            if isinstance(raw_data, dict):
                expenses = raw_data.get("expenses", [])
            elif isinstance(raw_data, list):
                expenses = raw_data
            else:
                expenses = []
        else:
            st.sidebar.warning(f"⚠️ Backend API returned status code: {response.status_code}")
            expenses = []
    except Exception as e:
        st.sidebar.error(f"⚠️ Connection to API engine delayed or failed. Error: {e}")
        expenses = []

    if expenses:
        df = pd.DataFrame(expenses)
        if "id" not in df.columns:
            df["id"] = [str(uuid.uuid4())[:8] for _ in range(len(df))]
        df["date"] = pd.to_datetime(df["date"]).dt.date
        df["amount"] = df["amount"].astype(float)
    else:
        df = pd.DataFrame(columns=["id", "date", "category", "amount", "description"])

    # Sidebar: Filters
    st.sidebar.divider()
    st.sidebar.markdown("### 🔍 Filter Engine")
    date_range = st.sidebar.date_input("Select Date Range", value=[])
    category_filter = st.sidebar.multiselect("Category", options=sorted(df["category"].dropna().unique()) if not df.empty else [])
    description_filter = st.sidebar.text_input("Search Description")

    filtered_df = df.copy()
    if not filtered_df.empty:
        if category_filter:
            filtered_df = filtered_df[filtered_df["category"].isin(category_filter)]
        if description_filter:
            filtered_df = filtered_df[filtered_df["description"].str.contains(description_filter, case=False, na=False)]
        if len(date_range) == 2:
            filtered_df = filtered_df[(filtered_df["date"] >= date_range[0]) & (filtered_df["date"] <= date_range[1])]

    # Main Panels Layout
    if st.session_state.show_chat:
        dash_col, chat_col = st.columns([6.2, 3.8], gap="medium")
    else:
        dash_col = st.container()
        chat_col = None

    # Left View Panel: Analytics & Editor
    with dash_col:
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
        <strong>💡 Quick Stats Explained:</strong> Total Spending is cumulative cost; Total Expenses tracks count; Average is transaction weight; Top Category flags maximum budget consumption.
        </div>
        """, unsafe_allow_html=True)

        st.subheader("📋 Transaction History")
        if not filtered_df.empty:
            filtered_df["id"] = filtered_df["id"].fillna("").apply(lambda x: x if x != "" else str(uuid.uuid4())[:8])

        existing_categories = sorted(list(df["category"].dropna().unique())) if not df.empty else []
        fallback_categories = ["Food", "Shopping", "Utilities", "Travel", "Entertainment", "Healthcare", "Education", "Others"]
        dynamic_categories = sorted(list(set(existing_categories + fallback_categories)))

        # MODIFIED: Changed deprecated `use_container_width` to `width='stretch'`
        edited_df = st.data_editor(
            filtered_df,
            key="ledger_editor",
            width="stretch",
            hide_index=True,
            num_rows="dynamic",
            height=250,
            column_order=["date", "category", "amount", "description"],
            column_config={
                "date": st.column_config.DateColumn("Date", required=True),
                "category": st.column_config.SelectboxColumn("Category", options=dynamic_categories, required=True),
                "amount": st.column_config.NumberColumn("Amount (₹)", min_value=0, required=True, format="₹%.2f"),
                "description": st.column_config.TextColumn("Description", required=True)
            }
        )

        # Database syncing
        crud_save_col1, crud_save_col2, _ = st.columns([3.5, 3.5, 3])
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
                except Exception:
                    st.error("Sync Pipeline Interrupted: Backend offline or structural mutation error.")

        with crud_save_col2:
            st.download_button(
                label="📄 Export to CSV",
                data=filtered_df.to_csv(index=False),
                file_name="expenses_export.csv",
                mime="text/csv",
                use_container_width=True
            )

        st.markdown("<br>", unsafe_allow_html=True)

        # Data Visualization
        if not filtered_df.empty:
            # 1. Group by category and sum the amounts to find total spend per category
            cat_totals = filtered_df.groupby("category")["amount"].sum().reset_index()
            
            # 2. Sort descending and slice the top 5
            top_5_categories_df = cat_totals.sort_values(by="amount", ascending=False).head(5)
            
            # 3. Create a filtered version of our transaction dataframe that only contains these top 5 categories
            top_5_filtered_df = filtered_df[filtered_df["category"].isin(top_5_categories_df["category"])]

            unique_categories = sorted(top_5_filtered_df["category"].unique())
            color_palette = px.colors.qualitative.G10
            color_map = {cat: color_palette[i % len(color_palette)] for i, cat in enumerate(unique_categories)}

            g_col1, g_col2 = st.columns(2)
            with g_col1:
                st.markdown("#### 🟢 Top 5 Category Allocation")
                # Using the top 5 transactions subset for the pie chart
                fig_pie = px.pie(top_5_filtered_df, names="category", values="amount", hole=0.4, color="category", color_discrete_map=color_map)
                fig_pie.update_layout(margin=dict(t=5, b=5, l=5, r=5), height=200, showlegend=True)
                st.plotly_chart(fig_pie, use_container_width=True, config={'displayModeBar': False})

            with g_col2:
                st.markdown("#### 📊 Top 5 Category Volumes")
                # Using the pre-grouped top 5 dataframe for the bar chart
                fig_bar = px.bar(top_5_categories_df, x="category", y="amount", text_auto='.2s', color="category", color_discrete_map=color_map)
                fig_bar.update_layout(margin=dict(t=5, b=5, l=5, r=5), height=200, showlegend=False, xaxis_title=None, yaxis_title=None)
                st.plotly_chart(fig_bar, use_container_width=True, config={'displayModeBar': False})

            st.markdown("<br>", unsafe_allow_html=True)

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
                                st.error(f"Failed to extract strategic data. Backend server status: {insight_response.status_code}")
                        except Exception as e:
                            st.error(f"Insight Generation Interrupted. Details: `{str(e)}`")

    # Right View Panel: Interactive Co-Pilot
    if chat_col and st.session_state.show_chat:
        with chat_col:
            st.markdown("### 🤖 AI Agent Chat")
            st.markdown("<div style='margin-bottom:8px;'></div>", unsafe_allow_html=True)

            if "messages" not in st.session_state:
                st.session_state.messages = [
                    {"role": "assistant", "content": "👋 Hi! I'm your AI Expense Tracker. Tell me what you spent or ask about your expenses."}
                ]

            with st.container(height=545, border=True):
                for message in st.session_state.messages:
                    with st.chat_message(message["role"]):
                        content = message["content"]
                        if isinstance(content, dict) and "text" in content:
                            st.markdown(content["text"])
                            if "data" in content and content["data"]:
                                data_obj = content["data"]
                                if isinstance(data_obj, list):
                                    st.dataframe(pd.DataFrame(data_obj), width="stretch", hide_index=True)
                                elif isinstance(data_obj, dict):
                                    formatted_data = {
                                        "Metrics Properties": [k.replace("_", " ").title() for k in data_obj.keys() if k != "expense_id"],
                                        "Telemetry Values": [str(v) for k in data_obj.keys() for v in [data_obj[k]] if k != "expense_id"]
                                    }
                                    st.table(pd.DataFrame(formatted_data))
                        elif isinstance(content, list):
                            if len(content):
                                st.dataframe(pd.DataFrame(content), width="stretch", hide_index=True)
                        else:
                            st.markdown(str(content))

            user_input = st.chat_input("Ask your AI Agent or enter a new expense...")
            if user_input:
                st.session_state.messages.append({"role": "user", "content": user_input})
                st.rerun()

    # Handle asynchronous state loop logic
    if "messages" in st.session_state and st.session_state.messages[-1]["role"] == "user":
        latest_user_query = st.session_state.messages[-1]["content"]
        with chat_col:
            with st.spinner("AI Agent thinking..."):
                try:
                    chat_payload = {"message": latest_user_query}
                    response = requests.post(f"{API_URL}/chat", json=chat_payload, headers=request_headers, timeout=10)
                    assistant_reply = response.json().get("response", "Processing done.") if response.status_code == 200 else f"⚠️ Server exception: {response.status_code}"
                except Exception as e:
                    assistant_reply = f"❌ Error communicating with agent: `{str(e)}`"

                st.session_state.messages.append({"role": "assistant", "content": assistant_reply})
                st.rerun()