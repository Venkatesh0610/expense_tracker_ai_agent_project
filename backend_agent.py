import os
import json
import time
import logging
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, HTTPException, Body, Header, Request
from fastapi.middleware.cors import CORSMiddleware
from groq import Groq

# Import system prompt and database module
from prompts import SYSTEM_PROMPT
from database import ExpenseDatabase

# Configure detailed logging format
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
)
logger = logging.getLogger("ExpenseTrackerAPI")

# Fetch environment variables safely
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
DEFAULT_SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")

logger.info("Initializing API application...")
if not GROQ_API_KEY:
    logger.warning("GROQ_API_KEY is not set in environment variables!")
if not DEFAULT_SPREADSHEET_ID:
    logger.warning("SPREADSHEET_ID is not set in environment variables!")

app = FastAPI(title="Unified Expense Tracker API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

MODEL = "llama-3.1-8b-instant"

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
                    "category": {"type": "string", "description": "Expense category (e.g. Food, Travel, Shopping, Bills)."},
                    "description": {"type": "string", "description": "Short details of the purchase."}
                },
                "required": ["amount", "category"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_expenses",
            "description": "Retrieve all recorded expense transactions.",
            "parameters": {"type": "object", "properties": {}, "required": []}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_last_expense",
            "description": "Retrieve the most recently added expense record.",
            "parameters": {"type": "object", "properties": {}, "required": []}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "update_expense",
            "description": "Update an existing transaction record. If expense_id is omitted or set to 'latest', it updates the last added expense.",
            "parameters": {
                "type": "object",
                "properties": {
                    "expense_id": {"type": "string", "description": "Optional unique Expense ID. Omit to target the most recent expense."},
                    "amount": {"type": "number", "description": "Updated amount in INR."},
                    "category": {"type": "string", "description": "Updated category."},
                    "description": {"type": "string", "description": "Updated description."}
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "delete_expense",
            "description": "Delete an expense record. If expense_id is omitted or set to 'latest', it deletes the last added expense.",
            "parameters": {
                "type": "object",
                "properties": {
                    "expense_id": {"type": "string", "description": "Optional unique Expense ID. Omit to delete the most recent expense."}
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "total_spending",
            "description": "Calculate global summary of total spending across all records.",
            "parameters": {"type": "object", "properties": {}, "required": []}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "category_summary",
            "description": "Return expenditure broken down by category.",
            "parameters": {"type": "object", "properties": {}, "required": []}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_analytics_summary",
            "description": "Retrieve raw expense entries for trend calculations and category ratio analysis.",
            "parameters": {"type": "object", "properties": {}, "required": []}
        }
    }
]


class ExpenseAgent:
    def __init__(self, spreadsheet_id: Optional[str] = None, history: Optional[List[Dict[str, Any]]] = None):
        logger.info(f"[Agent Init] Initializing ExpenseAgent with spreadsheet_id: {spreadsheet_id or 'DEFAULT'}")
        
        self.db = ExpenseDatabase(spreadsheet_id=spreadsheet_id)
        if not GROQ_API_KEY:
            logger.error("[Agent Init] GROQ_API_KEY is missing!")
            raise ValueError("GROQ_API_KEY is missing. Please set it in your environment variables or .env file.")
            
        self.client = Groq(api_key=GROQ_API_KEY)

        if history:
            logger.info(f"[Agent Init] Loaded existing conversation history ({len(history)} messages)")
            self.messages = history
        else:
            logger.info("[Agent Init] Initializing new conversation with SYSTEM_PROMPT")
            self.messages = [{"role": "system", "content": SYSTEM_PROMPT}]

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
        raw_arguments = tool_call.function.arguments
        
        logger.info(f"[Tool Execution] Attempting to execute: '{function_name}' with raw args: {raw_arguments}")

        if raw_arguments in [None, "", "null"]:
            arguments = {}
        else:
            try:
                arguments = json.loads(raw_arguments)
            except Exception as parse_err:
                logger.error(f"[Tool Execution] Failed to parse function arguments for '{function_name}': {parse_err}")
                arguments = {}

        tool = self.tool_registry.get(function_name)
        if tool is None:
            logger.error(f"[Tool Execution] Requested unknown tool: '{function_name}'")
            return {"error": f"Unknown Tool: {function_name}"}

        start_time = time.time()
        try:
            result = tool(**arguments)
            duration = round((time.time() - start_time) * 1000, 2)
            logger.info(f"[Tool Execution] Successfully executed '{function_name}' in {duration}ms")
            logger.debug(f"[Tool Execution Result] '{function_name}': {result}")
            return result
        except Exception as e:
            duration = round((time.time() - start_time) * 1000, 2)
            logger.exception(f"[Tool Execution Error] Exception in '{function_name}' after {duration}ms: {e}")
            return {"error": str(e)}

    def chat(self, user_message: str):
        logger.info(f"[Agent Chat] New user message received: '{user_message}'")
        self.messages.append({"role": "user", "content": user_message})
        self.active_data_payload = None

        months_map = {
            "january": "-01-", "february": "-02-", "march": "-03-", "april": "-04-",
            "may": "-05-", "june": "-06-", "july": "-07-", "august": "-08-",
            "september": "-09-", "october": "-10-", "november": "-11-", "december": "-12-",
            "jan": "-01-", "feb": "-02-", "mar": "-03-", "apr": "-04-", "jun": "-06-", "jul": "-07-"
        }

        loop_count = 0
        while True:
            loop_count += 1
            logger.info(f"[Agent Loop Iteration {loop_count}] Sending request to Groq model '{MODEL}'...")
            
            start_time = time.time()
            response = self.client.chat.completions.create(
                model=MODEL,
                messages=self.messages,
                tools=TOOLS,
                tool_choice="auto"
            )
            duration = round((time.time() - start_time) * 1000, 2)
            logger.info(f"[Groq Response] Received completion in {duration}ms")

            assistant_message = response.choices[0].message

            if not assistant_message.tool_calls:
                final_answer = assistant_message.content or "Analysis completed."
                logger.info(f"[Agent Finished] Final response generated without further tool calls.")
                logger.debug(f"[Agent Final Answer Text]: {final_answer}")
                
                self.messages.append({"role": "assistant", "content": final_answer})

                # Post-process payload for downstream UI cards / tables
                if self.active_data_payload is not None and isinstance(self.active_data_payload, list):
                    logger.info(f"[Payload Post-Processing] Filtering active data payload ({len(self.active_data_payload)} records)...")
                    normalized_text = final_answer.lower()
                    detected_month_token = None
                    
                    for m_name, m_code in months_map.items():
                        if m_name in normalized_text:
                            detected_month_token = m_code
                            logger.info(f"[Payload Post-Processing] Detected month filter token: '{m_name}' ({m_code})")
                            break

                    if detected_month_token:
                        self.active_data_payload = [
                            row for row in self.active_data_payload
                            if isinstance(row, dict) and "date" in row and detected_month_token in str(row["date"])
                        ]
                        logger.info(f"[Payload Post-Processing] Filtered by month token. Remaining rows: {len(self.active_data_payload)}")
                    else:
                        categories = ["food", "travel", "shopping", "bills", "entertainment", "healthcare", "education", "others"]
                        for cat in categories:
                            if cat in normalized_text:
                                logger.info(f"[Payload Post-Processing] Detected category filter token: '{cat}'")
                                self.active_data_payload = [
                                    row for row in self.active_data_payload
                                    if isinstance(row, dict) and "category" in row and str(row["category"]).lower() == cat
                                ]
                                logger.info(f"[Payload Post-Processing] Filtered by category token. Remaining rows: {len(self.active_data_payload)}")
                                break

                return {
                    "text": final_answer,
                    "data": self.active_data_payload,
                    "history": self.messages
                }

            # Handle Tool Calls
            tool_call_names = [tc.function.name for tc in assistant_message.tool_calls]
            logger.info(f"[Agent Loop Iteration {loop_count}] Model requested tool calls: {tool_call_names}")

            tool_calls_dict = [
                {
                    "id": tc.id,
                    "type": tc.type,
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments
                    }
                } for tc in assistant_message.tool_calls
            ]

            self.messages.append({
                "role": "assistant",
                "content": assistant_message.content,
                "tool_calls": tool_calls_dict
            })

            for tool_call in assistant_message.tool_calls:
                tool_name = tool_call.function.name
                tool_result = self.execute_tool(tool_call)

                if tool_name in ["get_expenses", "get_last_expense", "category_summary", "total_spending", "get_analytics_summary"]:
                    if isinstance(tool_result, dict) and "expenses" in tool_result:
                        self.active_data_payload = tool_result["expenses"]
                    else:
                        self.active_data_payload = tool_result
                    
                    payload_count = len(self.active_data_payload) if isinstance(self.active_data_payload, list) else 1
                    logger.info(f"[Payload Update] Updated active_data_payload from '{tool_name}' ({payload_count} items)")

                serialized_content = (
                    json.dumps(tool_result) if not isinstance(tool_result, str) else tool_result
                )

                self.messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": serialized_content
                })


# --- FASTAPI ENDPOINTS ---
@app.get("/health")
def health():
    logger.info("GET /health pinged")
    return {"status": "online"}


@app.get("/expenses")
def get_expenses_route(x_sheet_id: Optional[str] = Header(None, alias="X-Sheet-ID")):
    sheet_id = x_sheet_id or DEFAULT_SPREADSHEET_ID
    logger.info(f"GET /expenses | Target Sheet ID: '{sheet_id or 'DEFAULT'}'")
    try:
        db = ExpenseDatabase(spreadsheet_id=sheet_id)
        result = db.get_expenses()
        record_count = len(result) if isinstance(result, list) else (len(result.get("expenses", [])) if isinstance(result, dict) else "unknown")
        logger.info(f"GET /expenses | Success — retrieved {record_count} records")
        return result
    except Exception as e:
        logger.exception(f"GET /expenses | Error fetching expenses for sheet_id: {sheet_id}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/expenses")
def add_expense_route(payload: dict = Body(...), x_sheet_id: Optional[str] = Header(None, alias="X-Sheet-ID")):
    sheet_id = x_sheet_id or DEFAULT_SPREADSHEET_ID
    logger.info(f"POST /expenses | Target Sheet ID: '{sheet_id or 'DEFAULT'}' | Payload: {payload}")
    try:
        db = ExpenseDatabase(spreadsheet_id=sheet_id)
        result = db.add_expense(**payload)
        logger.info(f"POST /expenses | Success — added expense")
        return result
    except Exception as e:
        logger.exception(f"POST /expenses | Error adding expense")
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/expenses/{expense_id}")
def update_expense_route(expense_id: str, payload: dict = Body(...), x_sheet_id: Optional[str] = Header(None, alias="X-Sheet-ID")):
    sheet_id = x_sheet_id or DEFAULT_SPREADSHEET_ID
    logger.info(f"PUT /expenses/{expense_id} | Target Sheet ID: '{sheet_id or 'DEFAULT'}' | Payload: {payload}")
    try:
        db = ExpenseDatabase(spreadsheet_id=sheet_id)
        db_payload = payload.copy()
        db_payload.pop("date", None)
        result = db.update_expense(expense_id=expense_id, **db_payload)
        logger.info(f"PUT /expenses/{expense_id} | Success — updated expense")
        return result
    except Exception as e:
        logger.exception(f"PUT /expenses/{expense_id} | Error updating expense")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/expenses/{expense_id}")
def delete_expense_route(expense_id: str, x_sheet_id: Optional[str] = Header(None, alias="X-Sheet-ID")):
    sheet_id = x_sheet_id or DEFAULT_SPREADSHEET_ID
    logger.info(f"DELETE /expenses/{expense_id} | Target Sheet ID: '{sheet_id or 'DEFAULT'}'")
    try:
        db = ExpenseDatabase(spreadsheet_id=sheet_id)
        result = db.delete_expense(expense_id=expense_id)
        logger.info(f"DELETE /expenses/{expense_id} | Success — deleted expense")
        return result
    except Exception as e:
        logger.exception(f"DELETE /expenses/{expense_id} | Error deleting expense")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/chat")
def chat_route(payload: dict = Body(...), x_sheet_id: Optional[str] = Header(None, alias="X-Sheet-ID")):
    user_msg = payload.get("message")
    history = payload.get("history")
    sheet_id = x_sheet_id or DEFAULT_SPREADSHEET_ID

    logger.info(f"POST /chat | Target Sheet ID: '{sheet_id or 'DEFAULT'}' | Message length: {len(user_msg) if user_msg else 0} chars")

    if not user_msg:
        logger.warning("POST /chat | Request rejected — missing 'message' parameter")
        raise HTTPException(status_code=400, detail="Missing required request parameter: 'message'")
    try:
        agent = ExpenseAgent(spreadsheet_id=sheet_id, history=history)
        response = agent.chat(user_msg)
        logger.info("POST /chat | Success — returning response payload")
        return {"response": response}
    except Exception as e:
        logger.exception("POST /chat | Error executing chat flow")
        raise HTTPException(status_code=500, detail=str(e))