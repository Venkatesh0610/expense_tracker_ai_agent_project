# backend_agent.py
import os
import json
import logging
from fastapi import FastAPI, HTTPException, Body, Header
from fastapi.middleware.cors import CORSMiddleware
from groq import Groq
import streamlit as st
from prompts import SYSTEM_PROMPT

# Import your database module
from database import ExpenseDatabase

# Fetch keys safely
GROQ_API_KEY = st.secrets.get("GROQ_API_KEY") or os.getenv("GROQ_API_KEY")
DEFAULT_SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")

app = FastAPI(title="Unified Expense Tracker API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

MODEL = "llama-3.3-70b-versatile"

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "add_expense",
            "description": "Add a new expense.",
            "parameters": {
                "type": "object",
                "properties": {
                    "amount": {"type": "number", "description": "Expense amount in INR."},
                    "category": {"type": "string", "description": "Expense category."},
                    "description": {"type": "string", "description": "Expense description."}
                },
                "required": ["amount", "category", "description"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_expenses",
            "description": "Retrieve all expenses.",
            "parameters": {"type": "object", "properties": {}, "required": []}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_last_expense",
            "description": "Retrieve the latest expense record.",
            "parameters": {"type": "object", "properties": {}, "required": []}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "update_expense",
            "description": "Update an existing transaction record.",
            "parameters": {
                "type": "object",
                "properties": {
                    "expense_id": {"type": "string", "description": "Expense ID."},
                    "amount": {"type": "number", "description": "Updated amount."},
                    "category": {"type": "string", "description": "Updated category."},
                    "description": {"type": "string", "description": "Updated description."}
                },
                "required": ["expense_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "delete_expense",
            "description": "Delete an expense using its unique ID.",
            "parameters": {
                "type": "object",
                "properties": {
                    "expense_id": {"type": "string", "description": "Expense ID."}
                },
                "required": ["expense_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "total_spending",
            "description": "Calculate global summary total spending.",
            "parameters": {"type": "object", "properties": {}, "required": []}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "category_summary",
            "description": "Return spending grouped by category.",
            "parameters": {"type": "object", "properties": {}, "required": []}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_analytics_summary",
            "description": "Retrieves the complete list of all transaction records to calculate percentages, trends, and anomalies.",
            "parameters": {"type": "object", "properties": {}, "required": []}
        }
    }
]

class ExpenseAgent:
    def __init__(self, spreadsheet_id=None):
        self.db = ExpenseDatabase(spreadsheet_id=spreadsheet_id)
        self.messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        self.client = Groq(api_key=GROQ_API_KEY)
        self.tool_registry = {
            "add_expense": self.db.add_expense,
            "get_expenses": self.db.get_expenses,
            "get_last_expense": self.db.get_last_expense,
            "update_expense": self.db.update_expense,
            "delete_expense": self.db.delete_expense,
            "total_spending": self.db.total_spending,
            "category_summary": self.db.category_summary,
            "get_analytics_summary": self.db.get_expenses 
        }
        self.active_data_payload = None

    def execute_tool(self, tool_call):
        function_name = tool_call.function.name
        arguments = tool_call.function.arguments
        
        if arguments in [None, "", "null"]:
            arguments = {}
        else:
            arguments = json.loads(arguments)

        tool = self.tool_registry.get(function_name)
        if tool is None:
            return {"error": f"Unknown Tool: {function_name}"}

        try:
            return tool(**arguments)
        except Exception as e:
            return {"error": str(e)}

    def chat(self, user_message):
        self.messages.append({"role": "user", "content": user_message})
        self.active_data_payload = None 

        months_map = {
            "january": "-01-", "february": "-02-", "march": "-03-", "april": "-04-",
            "may": "-05-", "june": "-06-", "july": "-07-", "august": "-08-",
            "september": "-09-", "october": "-10-", "november": "-11-", "december": "-12-",
            "jan": "-01-", "feb": "-02-", "mar": "-03-", "apr": "-04-", "jun": "-06-", "jul": "-07-"
        }

        while True:
            response = self.client.chat.completions.create(
                model=MODEL,
                messages=self.messages,
                tools=TOOLS,
                tool_choice="auto"
            )

            assistant_message = response.choices[0].message

            if not assistant_message.tool_calls:
                final_answer = assistant_message.content or "Analysis completed."
                self.messages.append({"role": "assistant", "content": final_answer})

                if self.active_data_payload is not None and isinstance(self.active_data_payload, list):
                    normalized_text = final_answer.lower()
                    detected_month_token = None
                    for m_name, m_code in months_map.items():
                        if m_name in normalized_text:
                            detected_month_token = m_code
                            break
                    
                    if detected_month_token:
                        self.active_data_payload = [
                            row for row in self.active_data_payload 
                            if "date" in row and detected_month_token in str(row["date"])
                        ]
                    elif "category" in normalized_text or any(cat.lower() in normalized_text for cat in ["food", "travel", "shopping", "bills", "entertainment"]):
                        for cat in ["food", "travel", "shopping", "bills", "entertainment", "healthcare", "education", "others"]:
                            if cat in normalized_text:
                                self.active_data_payload = [
                                    row for row in self.active_data_payload
                                    if "category" in row and row["category"].lower() == cat
                                ]
                                break

                return {
                    "text": final_answer,
                    "data": self.active_data_payload
                }

            self.messages.append(assistant_message)

            for tool_call in assistant_message.tool_calls:
                tool_name = tool_call.function.name
                tool_result = self.execute_tool(tool_call)

                if tool_name in ["get_expenses", "get_last_expense", "category_summary", "total_spending", "get_analytics_summary"]:
                    if isinstance(tool_result, dict) and "expenses" in tool_result:
                        self.active_data_payload = tool_result["expenses"]
                    else:
                        self.active_data_payload = tool_result

                self.messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(tool_result)
                })

# --- FASTAPI ENDPOINTS ---
@app.get("/health")
def health():
    return {"status": "online"}

@app.get("/expenses")
def get_expenses_route(x_sheet_id: str = Header(None, alias="X-Sheet-ID")):
    sheet_id = x_sheet_id or DEFAULT_SPREADSHEET_ID
    try:
        db = ExpenseDatabase(spreadsheet_id=sheet_id)
        return db.get_expenses()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/expenses")
def add_expense_route(payload: dict = Body(...), x_sheet_id: str = Header(None, alias="X-Sheet-ID")):
    sheet_id = x_sheet_id or DEFAULT_SPREADSHEET_ID
    try:
        db = ExpenseDatabase(spreadsheet_id=sheet_id)
        return db.add_expense(**payload)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/expenses/{expense_id}")
def update_expense_route(expense_id: str, payload: dict = Body(...), x_sheet_id: str = Header(None, alias="X-Sheet-ID")):
    print("---------------------------",expense_id,payload)
    sheet_id = x_sheet_id or DEFAULT_SPREADSHEET_ID
    try:
        db = ExpenseDatabase(spreadsheet_id=sheet_id)
        
        # 🚨 THE FIX: Remove 'date' from the payload copy so it doesn't break the method signature
        db_payload = payload.copy()
        db_payload.pop("date", None) 
        
        # Now it safely unpacks only amount, category, and description
        return db.update_expense(expense_id=expense_id, **db_payload)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/expenses/{expense_id}")
def delete_expense_route(expense_id: str, x_sheet_id: str = Header(None, alias="X-Sheet-ID")):
    sheet_id = x_sheet_id or DEFAULT_SPREADSHEET_ID
    try:
        db = ExpenseDatabase(spreadsheet_id=sheet_id)
        return db.delete_expense(expense_id=expense_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat")
def chat_route(payload: dict = Body(...), x_sheet_id: str = Header(None, alias="X-Sheet-ID")):
    user_msg = payload.get("message")
    sheet_id = x_sheet_id or DEFAULT_SPREADSHEET_ID
    if not user_msg:
        raise HTTPException(status_code=400, detail="Missing parameter: 'message'")
    try:
        agent = ExpenseAgent(spreadsheet_id=sheet_id)
        response = agent.chat(user_msg)
        return {"response": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))