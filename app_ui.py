# app_ui.py
import uuid
import requests
import pandas as pd
import streamlit as st
import plotly.express as px

API_URL = "http://127.0.0.1:8000"

def render_ui(default_spreadsheet_id):
    # Initialize UI and workflow tracking keys
    if "show_chat" not in st.session_state:
        st.session_state.show_chat = True
    if "active_user_sheet_id" not in st.session_state:
        st.session_state.active_user_sheet_id = ""
    if "processing_chat" not in st.session_state:
        st.session_state.processing_chat = False
        
    # PROTECTED STATE STORAGE
    if "cached_df" not in st.session_state:
        st.session_state.cached_df = None
    if "needs_data_refresh" not in st.session_state:
        st.session_state.needs_data_refresh = True
        
    # DELTA STATE HOLDING CONTAINER: Prevents button clicks from clearing edits
    if "pending_changes" not in st.session_state:
        st.session_state.pending_changes = {"edited_rows": {}, "added_rows": [], "deleted_rows": []}

    # CSS Presentation Override
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

    # Main Context Headers
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

    # Sidebar Panel: Google Sheet Context
    st.sidebar.markdown("### ⚙️ Data Configuration")
    user_sheet_id = st.sidebar.text_input(
        label="Google Sheet ID",
        value=st.session_state.active_user_sheet_id,
        placeholder="Paste your custom sheet ID here...",
        key="config_sheet_input_widget",
        help="Leave blank to use the default demo environment."
    )
    
    if user_sheet_id != st.session_state.active_user_sheet_id:
        st.session_state.active_user_sheet_id = user_sheet_id
        st.session_state.needs_data_refresh = True

    active_sheet_id = user_sheet_id.strip() if user_sheet_id.strip() else default_spreadsheet_id

    if user_sheet_id.strip():
        st.sidebar.success("🔗 Connected to Custom Workspace")
    else:
        st.sidebar.info("💡 Running on Default Demo Environment")

    request_headers = {
        "X-Sheet-ID": str(active_sheet_id),
        "Content-Type": "application/json"
    }

    # Data Synchronization
    if st.session_state.needs_data_refresh or st.session_state.cached_df is None:
        try:
            response = requests.get(f"{API_URL}/expenses", headers=request_headers, timeout=5)
            if response.status_code == 200:
                raw_data = response.json()
                expenses = raw_data.get("expenses", []) if isinstance(raw_data, dict) else raw_data
                
                if expenses:
                    fresh_df = pd.DataFrame(expenses)
                    
                    # Normalization: Ensure structural key variations match 'id' column seamlessly
                    if "expense_id" in fresh_df.columns and "id" not in fresh_df.columns:
                        fresh_df["id"] = fresh_df["expense_id"]
                    elif "id" not in fresh_df.columns:
                        fresh_df["id"] = [str(uuid.uuid4())[:8] for _ in range(len(fresh_df))]
                    
                    fresh_df["id"] = fresh_df["id"].astype(str)
                    fresh_df["date"] = pd.to_datetime(fresh_df["date"]).dt.date
                    fresh_df["amount"] = fresh_df["amount"].astype(float)
                    st.session_state.cached_df = fresh_df
                else:
                    st.session_state.cached_df = pd.DataFrame(columns=["id", "date", "category", "amount", "description"])
            else:
                st.sidebar.warning(f"⚠️ API returned status code: {response.status_code}")
                if st.session_state.cached_df is None:
                    st.session_state.cached_df = pd.DataFrame(columns=["id", "date", "category", "amount", "description"])
        except Exception as e:
            st.sidebar.error(f"⚠️ Connection to API failed: {e}")
            if st.session_state.cached_df is None:
                st.session_state.cached_df = pd.DataFrame(columns=["id", "date", "category", "amount", "description"])
        
        st.session_state.needs_data_refresh = False

    base_df = st.session_state.cached_df

    # Sidebar Panel: Filter Configuration Engine
    st.sidebar.divider()
    st.sidebar.markdown("### 🔍 Filter Engine")
    date_range = st.sidebar.date_input("Select Date Range", value=[])
    category_filter = st.sidebar.multiselect("Category", options=sorted(base_df["category"].dropna().unique()) if not base_df.empty else [])
    description_filter = st.sidebar.text_input("Search Description")

    filtered_df = base_df.copy().reset_index(drop=True)
    if not filtered_df.empty:
        if category_filter:
            filtered_df = filtered_df[filtered_df["category"].isin(category_filter)]
        if description_filter:
            filtered_df = filtered_df[filtered_df["description"].str.contains(description_filter, case=False, na=False)]
        if isinstance(date_range, (list, tuple)) and len(date_range) == 2:
            filtered_df = filtered_df[(filtered_df["date"] >= date_range[0]) & (filtered_df["date"] <= date_range[1])]
        filtered_df = filtered_df.reset_index(drop=True)

    if st.session_state.show_chat:
        dash_col, chat_col = st.columns([6.2, 3.8], gap="medium")
    else:
        dash_col = st.container()
        chat_col = None

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

        st.subheader("📋 Transaction History")
        
        existing_categories = sorted(list(base_df["category"].dropna().unique())) if not base_df.empty else []
        fallback_categories = ["Food", "Shopping", "Utilities", "Travel", "Entertainment", "Healthcare", "Education", "Others"]
        dynamic_categories = sorted(list(set(existing_categories + fallback_categories)))

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

        # STATE SNIPER CACHE: Capture changes before button processing wipes out widget elements
        if "ledger_editor" in st.session_state:
            latest_widget_state = st.session_state["ledger_editor"]
            if latest_widget_state.get("edited_rows") or latest_widget_state.get("added_rows") or latest_widget_state.get("deleted_rows"):
                st.session_state.pending_changes = latest_widget_state

        btn_col1, btn_col2 = st.columns(2)
        with btn_col1:
            save_clicked = st.button("💾 Save Database Changes", use_container_width=True, type="primary")
        with btn_col2:
            st.download_button(
                label="📄 Export Current View to CSV",
                data=filtered_df.to_csv(index=False),
                file_name="expenses_export.csv",
                mime="text/csv",
                use_container_width=True
            )

        # Process mutations from our protected permanent holding space
        if save_clicked:
            try:
                editor_state = st.session_state.pending_changes
                edited_rows = editor_state.get("edited_rows", {})
                added_rows = editor_state.get("added_rows", [])
                deleted_rows = editor_state.get("deleted_rows", [])

                filtered_df["id"] = filtered_df["id"].astype(str)

                # 1. Process Deletions
                if deleted_rows:
                    for row_idx in deleted_rows:
                        if row_idx < len(filtered_df):
                            expense_id = str(filtered_df.iloc[row_idx]["id"])
                            
                            if expense_id and expense_id != "nan":
                                del_resp = requests.delete(f"{API_URL}/expenses/{expense_id}", headers=request_headers, timeout=2)
                                st.write(f"📡 Delete Response Status: {del_resp.status_code}")
                        else:
                            st.error(f"❌ Deletion index out of bounds matching data row index {row_idx}.")

                # 2. Process Modifications (Iterates dynamically through multiple altered rows)
                if edited_rows:
                    for row_idx_str, changes in edited_rows.items():
                        row_idx = int(row_idx_str)
                        
                        if row_idx >= len(filtered_df):
                            st.error(f"❌ Index Mismatch: Row index {row_idx} is out of bounds for current view.")
                            continue
                            
                        orig_row = filtered_df.iloc[row_idx]
                        expense_id = str(orig_row["id"]) # Normalized to read smoothly from data rows without throwing key errors

                        payload = {
                            "date": str(changes.get("date", orig_row["date"])),
                            "category": changes.get("category", orig_row["category"]),
                            "amount": float(changes.get("amount", orig_row["amount"])),
                            "description": changes.get("description", orig_row["description"])
                        }
            
                        
                        put_resp = requests.put(f"{API_URL}/expenses/{expense_id}", json=payload, headers=request_headers, timeout=2)
                        
                        if put_resp.status_code == 200:
                            st.success(f"✅ Expense {expense_id} updated successfully on backend.")
                        else:
                            st.error(f"❌ Backend failed to update row {expense_id}. API Status Code: {put_resp.status_code}, Response: {put_resp.text}")

                # 3. Process Additions
                if added_rows:
                    for i, new_row in enumerate(added_rows):
                        payload = {
                            "date": str(new_row.get("date", pd.Timestamp.now().date())),
                            "category": new_row.get("category", "Others"),
                            "amount": float(new_row.get("amount", 0.0)),
                            "description": new_row.get("description", "")
                        }
                        
                        post_resp = requests.post(f"{API_URL}/expenses", json=payload, headers=request_headers, timeout=2)
                        
                        if post_resp.status_code in [200, 201]:
                            st.success(f"✅ New entry added successfully.")
                        else:
                            st.error(f"❌ Backend rejected addition. Status: {post_resp.status_code}, Response: {post_resp.text}")

                st.toast("✅ Database synchronization processing completed!", icon="🔥")
                
                # Reset container tracking allocations
                st.session_state.pending_changes = {"edited_rows": {}, "added_rows": [], "deleted_rows": []}
                st.session_state.needs_data_refresh = True
                st.rerun()
                    
            except Exception as e:
                st.error(f"💥 Sync Pipeline Interrupted: {e}")

        st.markdown("<br>", unsafe_allow_html=True)

        # Visualizations Panel
        if not filtered_df.empty:
            cat_totals = filtered_df.groupby("category")["amount"].sum().reset_index()
            top_5_categories_df = cat_totals.sort_values(by="amount", ascending=False).head(5)
            top_5_filtered_df = filtered_df[filtered_df["category"].isin(top_5_categories_df["category"])]

            unique_categories = sorted(top_5_filtered_df["category"].unique())
            color_palette = px.colors.qualitative.G10
            color_map = {cat: color_palette[i % len(color_palette)] for i, cat in enumerate(unique_categories)}

            g_col1, g_col2 = st.columns(2)
            with g_col1:
                st.markdown("#### 🟢 Top 5 Category Allocation")
                fig_pie = px.pie(top_5_filtered_df, names="category", values="amount", hole=0.4, color="category", color_discrete_map=color_map)
                fig_pie.update_layout(margin=dict(t=5, b=5, l=5, r=5), height=200, showlegend=True)
                st.plotly_chart(fig_pie, use_container_width=True, config={'displayModeBar': False})

            with g_col2:
                st.markdown("#### 📊 Top 5 Category Volumes")
                fig_bar = px.bar(top_5_categories_df, x="category", y="amount", text_auto='.2s', color="category", color_discrete_map=color_map)
                fig_bar.update_layout(margin=dict(t=5, b=5, l=5, r=5), height=200, showlegend=False, xaxis_title=None, yaxis_title=None)
                st.plotly_chart(fig_bar, use_container_width=True, config={'displayModeBar': False})

            st.markdown("<br>", unsafe_allow_html=True)

            with st.expander("🧠 Deep AI Financial Recommendations", expanded=False):
                if st.button("✨ Generate Custom Recommendation Report", use_container_width=True, type="secondary"):
                    with st.spinner("Analyzing current transactions..."):
                        telemetry_context = (
                            f"Give me actionable financial optimization recommendations based on my real-time expense data. "
                            f"Total spending is ₹{total_spend:,.2f} spread across {total_count} transactions."
                        )
                        try:
                            insight_response = requests.post(f"{API_URL}/chat", json={"message": telemetry_context}, headers=request_headers, timeout=12)
                            if insight_response.status_code == 200:
                                raw_reply = insight_response.json().get("response", "")
                                if isinstance(raw_reply, dict):
                                    recommendation_text = raw_reply.get("text", str(raw_reply))
                                else:
                                    recommendation_text = str(raw_reply)
                                
                        except Exception as e:
                            st.error(f"Insight Generation Failed: {e}")

    # Chat Engine Panel
    if chat_col and st.session_state.show_chat:
        with chat_col:
            st.markdown("### 🤖 AI Agent Chat")
            if "messages" not in st.session_state:
                st.session_state.messages = [{"role": "assistant", "content": "👋 Hi! Tell me what you spent or ask about your expenses."}]

            with st.container(height=545, border=True):
                for message in st.session_state.messages:
                    with st.chat_message(message["role"]):
                        content = message["content"]
                        if isinstance(content, dict) and "text" in content:
                            st.markdown(content["text"])
                            if "data" in content and content["data"]:
                                st.dataframe(pd.DataFrame(content["data"]), width="stretch", hide_index=True)
                        else:
                            st.markdown(str(content))

            user_input = st.chat_input("Ask your AI Agent or enter a new expense...")
            if user_input:
                st.session_state.messages.append({"role": "user", "content": user_input})
                st.session_state.processing_chat = True
                st.rerun()

    # Async Process Thread Control
    if "messages" in st.session_state and len(st.session_state.messages) > 0 and st.session_state.messages[-1]["role"] == "user" and st.session_state.processing_chat:
        latest_user_query = st.session_state.messages[-1]["content"]
        active_chat_context = chat_col if chat_col else st.container()
        with active_chat_context:
            with st.spinner("AI Agent thinking..."):
                try:
                    response = requests.post(f"{API_URL}/chat", json={"message": latest_user_query}, headers=request_headers, timeout=10)
                    assistant_reply = response.json().get("response", "Done.") if response.status_code == 200 else "⚠️ Server error."
                except Exception as e:
                    assistant_reply = f"❌ Connection Error: {e}"

                st.session_state.messages.append({"role": "assistant", "content": assistant_reply})
                st.session_state.processing_chat = False
                st.session_state.needs_data_refresh = True
                st.rerun()