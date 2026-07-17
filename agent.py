import os
import json
import logging

from dotenv import load_dotenv
from groq import Groq
from database import ExpenseDatabase

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)
logger = logging.getLogger(__name__)

client = Groq()
MODEL = "llama-3.3-70b-versatile"
SYSTEM_PROMPT = """
You are an AI Expense Tracking Assistant.
Your responsibility is expense management, complex data analysis, and budget telemetry computations.

You must help with the following tasks:
1. Add a new expense.
2. Show all expenses / show the latest expense.
3. Update or delete an existing expense.
4. Calculate total spending or category breakdowns.
5. Perform deep mathematical calculations on historical data.

CRITICAL TOOL RULES:
• NEVER nest or chain tool calls inside one another's parameters. (e.g., Do NOT pass a function tag as a parameter value).
• If a user asks to delete or update "the last expense" or an expense without providing an explicit ID, you MUST call `get_last_expense` or `get_expenses` FIRST in this turn. Do not try to call `delete_expense` or `update_expense` until you have received the real ID back from the tool output in the next turn.
• Perform exact mathematical deductions based on the data provided before answering. Show your percentage calculations cleanly.
• Never answer general knowledge, coding, or unrelated queries outside finance.
"""

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
            "description": "Retrieves the complete list of all transaction records to calculate percentages, trends, top spend items, and monthly anomalies.",
            "parameters": {"type": "object", "properties": {}, "required": []}
        }
    }
]

class ExpenseAgent:
    def __init__(self, spreadsheet_id=None):
        # 💡 Dynamically spin up a database binding for this instance context
        self.db = ExpenseDatabase(spreadsheet_id=spreadsheet_id)
        
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
        arguments = tool_call.function.arguments

        if arguments in [None, "", "null"]:
            arguments = {}
        else:
            arguments = json.loads(arguments)

        tool = self.tool_registry.get(function_name)
        if tool is None:
            return {"error": f"Unknown Tool : {function_name}"}

        try:
            result = tool(**arguments)
            return result
        except Exception as e:
            logger.exception("Tool Execution Failed")
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
            response = client.chat.completions.create(
                model=MODEL,
                messages=self.messages,
                tools=TOOLS,
                tool_choice="auto"
            )

            assistant_message = response.choices[0].message

            if not assistant_message.tool_calls:
                final_answer = assistant_message.content or "Analysis completed successfully."
                self.messages.append({"role": "assistant", "content": final_answer})

                # --- DATA-PAYLOAD FILTERING BLOCK ---
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

                if self.active_data_payload is not None:
                    return {
                        "text": final_answer,
                        "data": self.active_data_payload
                    }
                return {"text": final_answer, "data": None}

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