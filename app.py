import logging
import os
from fastapi import FastAPI, HTTPException, Header
from typing import Optional, Any
from pydantic import BaseModel

from agent import ExpenseAgent
from database import ExpenseDatabase

# -----------------------------
# Configure Logger
# -----------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)
logger = logging.getLogger("ExpenseTrackerAPI")

# -----------------------------
# FastAPI App
# -----------------------------
app = FastAPI(
    title="AI Expense Tracker API",
    description="AI Agent powered Expense Tracker using OpenAI/Groq Function Calling",
    version="1.0.0"
)

# 💡 NOTICE: Global 'agent' and 'db' instances have been removed to prevent locking onto the .env sheet.


# -----------------------------
# Request Models
# -----------------------------
class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    response: Any


class UpdateExpenseRequest(BaseModel):
    amount: float
    category: str
    description: str


# -----------------------------
# Helper Function
# -----------------------------
def get_target_sheet_id(x_sheet_id: Optional[str]) -> Optional[str]:
    """Helper to cleanly parse the incoming header string."""
    return x_sheet_id.strip() if (x_sheet_id and x_sheet_id.strip()) else None


# -----------------------------
# Home API
# -----------------------------
@app.get("/")
def home():
    logger.info("Home API called.")
    return {
        "message": "Welcome to AI Expense Tracker API 🚀"
    }


# -----------------------------
# AI Chat API
# -----------------------------
@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest, x_sheet_id: Optional[str] = Header(None)):
    logger.info(f"Incoming User Message: {request.message} | Header Sheet ID: '{x_sheet_id}'")

    try:
        # 💡 Dynamically spin up the agent for this specific sheet target context
        target_id = get_target_sheet_id(x_sheet_id)
        dynamic_agent = ExpenseAgent(spreadsheet_id=target_id)

        response = dynamic_agent.chat(request.message)
        logger.info(f"Agent Response: {response}")

        return ChatResponse(response=response)

    except Exception as e:
        logger.exception("Error occurred while processing chat request")
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


# -----------------------------
# Get All Expenses
# -----------------------------
@app.get("/expenses")
def get_expenses(x_sheet_id: Optional[str] = Header(None)):
    logger.info(f"Incoming Sheet ID Header: '{x_sheet_id}'")

    try:
        target_id = get_target_sheet_id(x_sheet_id)
        dynamic_db = ExpenseDatabase(spreadsheet_id=target_id)
        
        expenses = dynamic_db.get_expenses()
        logger.info(f"Successfully fetched {len(expenses)} rows from: {dynamic_db.spreadsheet_id}")

        return {
            "expenses": expenses
        }

    except Exception as e:
        logger.exception("Failed to fetch expenses")
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


# -----------------------------
# Expense Summary
# -----------------------------
@app.get("/summary")
def summary(x_sheet_id: Optional[str] = Header(None)):
    logger.info(f"Fetching expense summary | Header Sheet ID: '{x_sheet_id}'")

    try:
        target_id = get_target_sheet_id(x_sheet_id)
        dynamic_db = ExpenseDatabase(spreadsheet_id=target_id)

        total = dynamic_db.total_spending()
        categories = dynamic_db.category_summary()

        logger.info(f"Total Spending: {total} on Sheet: {dynamic_db.spreadsheet_id}")

        return {
            "total_spending": total,
            "category_summary": categories
        }

    except Exception as e:
        logger.exception("Failed to generate summary")
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


# -----------------------------
# Delete Expense
# -----------------------------
@app.delete("/expenses/{expense_id}")
def delete_expense(expense_id: str, x_sheet_id: Optional[str] = Header(None)):
    # 💡 Changed expense_id type from int to str because UUID handles it as a string prefix
    logger.info(f"Deleting Expense ID: {expense_id} | Header Sheet ID: '{x_sheet_id}'")

    try:
        target_id = get_target_sheet_id(x_sheet_id)
        dynamic_db = ExpenseDatabase(spreadsheet_id=target_id)

        deleted = dynamic_db.delete_expense(expense_id)
        
        if not deleted:
            logger.warning(f"Expense ID {expense_id} not found on sheet {dynamic_db.spreadsheet_id}.")
            raise HTTPException(
                status_code=404,
                detail="Expense not found or could not be deleted."
            )

        logger.info("Expense deleted successfully.")
        return {
            "message": "Expense deleted successfully."
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to delete expense")
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


# -----------------------------
# Update Expense
# -----------------------------
@app.put("/expenses/{expense_id}")
def update_expense(
    expense_id: str, # 💡 Changed from int to str to accurately parse short UUID values
    request: UpdateExpenseRequest,
    x_sheet_id: Optional[str] = Header(None)
):
    logger.info(f"Updating Expense ID: {expense_id} | Header Sheet ID: '{x_sheet_id}'")

    try:
        target_id = get_target_sheet_id(x_sheet_id)
        dynamic_db = ExpenseDatabase(spreadsheet_id=target_id)

        expense = dynamic_db.update_expense(
            expense_id=expense_id,
            amount=request.amount,
            category=request.category,
            description=request.description
        )

        if expense is None:
            logger.warning(f"Expense ID {expense_id} not found on sheet {dynamic_db.spreadsheet_id}.")
            raise HTTPException(
                status_code=404,
                detail="Expense not found."
            )

        logger.info("Expense updated successfully.")
        return expense

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to update expense")
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)