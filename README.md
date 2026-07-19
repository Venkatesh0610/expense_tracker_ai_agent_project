# 🤖 AI Agent: Personal Expense Tracker

An intelligent, AI-powered personal finance assistant that helps users **track, manage, and analyze expenses using natural language**. The application combines a **Streamlit** frontend, a **FastAPI** backend, an **LLM-powered AI Agent**, and **Google Sheets** as the database to provide a conversational expense management experience.

**Try It:** 👉[ Personal Expense Tracker](https://expensetrackeraiagentproject-2ybcvburgqgey2zqbgs4q2.streamlit.app/)

---
# Demonstration

<img width="854" height="480" alt="demonstration_final" src="https://github.com/user-attachments/assets/9d4da3b1-df55-4f6a-863c-a6cf65175be6" />

---
# 🚀 Features

* 🤖 AI-powered expense tracking using natural language
* 💬 Conversational AI assistant with tool/function calling
* ➕ Add, ✏️ Update, 🗑️ Delete, and 📋 View expenses
* 📊 Interactive analytics dashboard with Plotly
* 📈 Spending trends and category insights
* 🧠 AI-generated financial recommendations
* 📂 Google Sheets as a real-time database
* 🔄 Live synchronization between UI and database
* 📥 CSV export
* 📱 Modern and responsive Streamlit interface

---

# 🏗️ Architecture

<img width="1180" height="1333" alt="image" src="https://github.com/user-attachments/assets/41e32a38-b4ac-43cf-9afb-bb81688cdf48" />
---

# 🧠 AI Agent Workflow

<img width="1024" height="1536" alt="image" src="https://github.com/user-attachments/assets/dd94f78d-0f86-4889-b772-ab5b7c087171" />

---

# 🛠️ Available AI Tools

The AI Agent uses function calling to execute backend operations.

| Tool             | Description                  |
| ---------------- | ---------------------------- |
| add_expense      | Add a new expense            |
| get_expenses     | Retrieve all expenses        |
| get_last_expense | Fetch the latest expense     |
| update_expense   | Update an existing expense   |
| delete_expense   | Delete an expense            |
| total_spending   | Calculate total spending     |
| category_summary | Spending grouped by category |

---

# 📊 Dashboard

The Streamlit dashboard includes:

### KPI Cards

* Total Spending
* Total Expenses
* Average Expense
* Highest Spending Category

### Analytics

* Pie Chart
* Category Bar Chart
* Daily Spending Trend
* Monthly Spending Trend
* Expense Distribution Histogram

### Transaction Manager

* Editable Data Table
* Add/Delete Rows
* Save Changes
* CSV Export

### Filters

* Date Range
* Category
* Description Search

---

# 📂 Project Structure

```text
expense-tracker-ai-agent/
│
├── app.py
├── app_ui.py
├── backend_agent.py
├── database.py
├── prompts.py
├── requirements.txt
├── README.md
├── .gitignore
│
└── pages/
    └── home.py
```

---

# 🛠️ Technologies Used

### Frontend

* Streamlit

### Backend

* FastAPI

### AI

* Groq Llama 3.3
* Function Calling

### Database

* Google Sheets API

### Data Processing

* Pandas

### Visualization

* Plotly

### Environment

* Python
* dotenv

---

# ⚙️ Installation

## 1. Clone Repository

```bash
git clone https://github.com/Venkatesh0610/expense_tracker_ai_agent_project.git
cd expense-tracker-ai-agent
```

---

## 2. Create Virtual Environment

```bash
python -m venv venv
```

Activate

Windows

```bash
venv\Scripts\activate
```

Linux/macOS

```bash
source venv/bin/activate
```

---

## 3. Install Dependencies

```bash
pip install -r requirements.txt
```

---

# 🔑 Configure Google Sheets

## Create Google Cloud Project

1. Open Google Cloud Console.
2. Create a project.
3. Enable:

   * Google Sheets API
4. Create a Service Account.
5. Download the JSON credentials.

---

## Create Google Sheet

Create a sheet with the following columns:

```text
id | date | category | amount | description
```

Share the sheet with your Service Account email and grant **Editor** access.

---

# 🌱 Environment Variables

Create a `.env` file.

```env
SPREADSHEET_ID=your_google_sheet_id

GROQ_API_KEY=your_llm_api_key

GOOGLE_CREDENTIALS_JSON='{
  ...
}'
```

---

# ▶️ Run the Application

Start the application using:

```bash
streamlit run app.py
```

The application will:

* Launch the Streamlit UI
* Start the FastAPI backend
* Connect to Google Sheets
* Initialize the AI Agent

Open:

```
http://localhost:8501
```

---

# 💬 Example Queries

```
I spent ₹450 on coffee
```

```
Paid ₹1,200 for groceries
```

```
Show all expenses
```

```
Show today's expenses
```

```
How much did I spend this month?
```

```
Show category summary
```

```
Delete my last expense
```

```
Update my last expense to ₹800
```

```
Generate financial insights
```

---

# 📌 Key Features

* ✅ Natural language expense tracking
* ✅ AI function calling
* ✅ Multi-step tool execution
* ✅ Google Sheets integration
* ✅ Real-time CRUD operations
* ✅ Interactive analytics dashboard
* ✅ Live data synchronization
* ✅ AI-generated financial insights
* ✅ Responsive Streamlit interface
* ✅ CSV export

## 🌐 Connect with Me

<p align="left">
  <a href="https://www.youtube.com/@avenkatesh0610" target="_blank">
    <img src="https://cdn-icons-png.flaticon.com/512/1384/1384060.png" alt="YouTube" width="40" height="40"/>
  </a>
  &nbsp;
  <a href="https://medium.com/@avenkatesh0610" target="_blank">
    <img src="https://cdn-icons-png.flaticon.com/512/2111/2111505.png" alt="Medium" width="40" height="40"/>
  </a>
  &nbsp;
  <a href="https://github.com/Venkatesh0610" target="_blank">
    <img src="https://cdn-icons-png.flaticon.com/512/2111/2111432.png" alt="GitHub" width="40" height="40"/>
  </a>
  &nbsp;
  <a href="https://www.linkedin.com/in/venkatesh-a-400459191/" target="_blank">
    <img src="https://cdn-icons-png.flaticon.com/128/3536/3536505.png" alt="LinkedIn" width="40" height="40"/>
  </a>
</p>

---

# 📄 License

This project is intended for educational and learning purposes. Feel free to fork, extend, and customize it for your own AI applications.

---

⭐ If you found this project useful, consider giving it a star on GitHub!
