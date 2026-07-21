import os
import uuid
import json
import logging
from datetime import datetime
from dotenv import load_dotenv
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)
logger = logging.getLogger(__name__)

DEFAULT_SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")
SERVICE_ACCOUNT_ENV = os.getenv("GOOGLE_CREDENTIALS_JSON")
SHEET_NAME = "Sheet1"


class ExpenseDatabase:
    def __init__(self, spreadsheet_id=None):
        if not SERVICE_ACCOUNT_ENV:
            raise ValueError("❌ Error: GOOGLE_CREDENTIALS_JSON environment variable is completely empty or missing.")

        try:
            if os.path.exists(SERVICE_ACCOUNT_ENV):
                creds = Credentials.from_service_account_file(
                    SERVICE_ACCOUNT_ENV,
                    scopes=["https://www.googleapis.com/auth/spreadsheets"]
                )
                logger.info(f"📡 Authenticated via local keyfile path: {SERVICE_ACCOUNT_ENV}")
            else:
                creds_info = json.loads(SERVICE_ACCOUNT_ENV)
                creds = Credentials.from_service_account_info(
                    creds_info,
                    scopes=["https://www.googleapis.com/auth/spreadsheets"]
                )
                logger.info("📡 Authenticated via raw GOOGLE_CREDENTIALS_JSON configuration string.")
        except json.JSONDecodeError:
            raise ValueError(
                f"❌ Authentication Failed: GOOGLE_CREDENTIALS_JSON does not target a valid file path, "
                f"nor could it be parsed as a raw JSON dictionary matrix."
            )
        except Exception as auth_err:
            raise RuntimeError(f"❌ Structural authentication error: {auth_err}")

        service = build("sheets", "v4", credentials=creds)
        self.sheet = service.spreadsheets()
        self.spreadsheet_id = spreadsheet_id or DEFAULT_SPREADSHEET_ID
        
        if not self.spreadsheet_id:
            logger.warning("Warning: No Spreadsheet ID provided or found in environment variables.")
        else:
            logger.info(f"Connected to Google Sheets ID: {self.spreadsheet_id}")
            self.create_header_if_not_exists()

    def create_header_if_not_exists(self):
        try:
            result = self.sheet.values().get(
                spreadsheetId=self.spreadsheet_id,
                range=f"{SHEET_NAME}!A1:E1"
            ).execute()

            values = result.get("values", [])
            if not values:
                logger.info("Creating sheet headers.")
                self.sheet.values().update(
                    spreadsheetId=self.spreadsheet_id,
                    range=f"{SHEET_NAME}!A1:E1",
                    valueInputOption="RAW",
                    body={
                        "values": [[
                            "Expense ID",
                            "Date",
                            "Category",
                            "Amount",
                            "Description"
                        ]]
                    }
                ).execute()
        except Exception as e:
            logger.error(f"Failed to verify/create headers: {e}")

    def add_expense(self, amount, category, description=""):
        expense_id = str(uuid.uuid4())[:8]
        today_date = datetime.now().strftime("%Y-%m-%d")
        
        expense = [
            expense_id,
            today_date,
            str(category).capitalize(),
            float(amount),
            str(description)
        ]
        logger.info(f"Adding Expense: {expense}")
        
        self.sheet.values().append(
            spreadsheetId=self.spreadsheet_id,
            range=f"{SHEET_NAME}!A:E",
            valueInputOption="RAW",
            insertDataOption="INSERT_ROWS",
            body={"values": [expense]}
        ).execute()

        desc_part = f" for {description}" if description else ""
        return f"SUCCESS: Added ₹{amount} in {category}{desc_part}."

    def get_expenses(self):
        logger.info("Fetching expenses.")
        try:
            result = self.sheet.values().get(
                spreadsheetId=self.spreadsheet_id,
                range=f"{SHEET_NAME}!A:E"
            ).execute()
            values = result.get("values", [])
            
            if len(values) <= 1:
                return []

            expenses = []
            for row in values[1:]:
                expenses.append({
                    "expense_id": row[0] if len(row) > 0 else "",
                    "date": row[1] if len(row) > 1 else "",
                    "category": row[2] if len(row) > 2 else "",
                    "amount": float(row[3]) if len(row) > 3 and row[3] else 0.0,
                    "description": row[4] if len(row) > 4 else ""
                })
            logger.info(f"{len(expenses)} expenses found.")
            return expenses
        except Exception as e:
            logger.error(f"Error fetching expenses: {e}")
            return []
    
    def get_last_expense(self):
        """Returns the last expense object for internal agent tool calls."""
        logger.info("Fetching last expense.")
        expenses = self.get_expenses()
        if not expenses:
            return None
        return expenses[-1]

    def resolve_expense_id(self, target_id=None):
        """
        Helper method to grab either a specific expense_id or default to the most recent one.
        Prevents tools from failing when the LLM passes 'latest' or leaves ID empty.
        """
        if target_id and target_id.lower() not in ["latest", "last", "recent", "none", ""]:
            return target_id
        
        last = self.get_last_expense()
        return last["expense_id"] if last else None

    def update_expense(self, expense_id=None, amount=None, category=None, description=None):
        resolved_id = self.resolve_expense_id(expense_id)
        if not resolved_id:
            return "ERROR: No expense available to update."

        logger.info(f"Updating Expense ID: {resolved_id}")
        result = self.sheet.values().get(
            spreadsheetId=self.spreadsheet_id,
            range=f"{SHEET_NAME}!A:E"
        ).execute()
        values = result.get("values", [])

        if len(values) <= 1:
            return "ERROR: No expenses available in records."

        for row_number, row in enumerate(values[1:], start=2):
            if len(row) > 0 and row[0] == resolved_id:
                if category is not None:
                    row[2] = str(category).capitalize()
                if amount is not None:
                    row[3] = str(amount)
                if description is not None:
                    if len(row) < 5:
                        row.append(str(description))
                    else:
                        row[4] = str(description)

                self.sheet.values().update(
                    spreadsheetId=self.spreadsheet_id,
                    range=f"{SHEET_NAME}!A{row_number}:E{row_number}",
                    valueInputOption="RAW",
                    body={"values": [row]}
                ).execute()
                logger.info("Expense updated successfully.")
                return "SUCCESS: Updated the expense record."

        logger.warning(f"Expense ID {resolved_id} not found.")
        return "ERROR: Targeted expense record could not be found."

    def delete_expense(self, expense_id=None):
        resolved_id = self.resolve_expense_id(expense_id)
        if not resolved_id:
            return "ERROR: No expense available to delete."

        logger.info(f"Deleting Expense ID: {resolved_id}")
        result = self.sheet.values().get(
            spreadsheetId=self.spreadsheet_id,
            range=f"{SHEET_NAME}!A:E"
        ).execute()
        values = result.get("values", [])

        if len(values) <= 1:
            return "ERROR: No expenses available to delete."

        target_row_index = None
        for idx, row in enumerate(values[1:], start=1):
            if len(row) > 0 and row[0] == resolved_id:
                target_row_index = idx
                break

        if target_row_index is not None:
            body = {
                "requests": [
                    {
                        "deleteDimension": {
                            "range": {
                                "sheetId": 0,
                                "dimension": "ROWS",
                                "startIndex": target_row_index,
                                "endIndex": target_row_index + 1
                            }
                        }
                    }
                ]
            }
            self.sheet.batchUpdate(
                spreadsheetId=self.spreadsheet_id,
                body=body
            ).execute()
            logger.info("Expense row deleted via batchUpdate successfully.")
            return "SUCCESS: Deleted the expense record."

        return "ERROR: Targeted expense record could not be found."

    def total_spending(self):
        logger.info("Calculating Total Spending.")
        expenses = self.get_expenses()
        total = sum(expense["amount"] for expense in expenses)
        return f"Total spending across all recorded expenses is ₹{total:,.2f}."
    
    def category_summary(self):
        logger.info("Generating Category Summary.")
        expenses = self.get_expenses()
        summary = {}
        for expense in expenses:
            cat = expense["category"] or "Uncategorized"
            summary[cat] = summary.get(cat, 0.0) + expense["amount"]
        return summary