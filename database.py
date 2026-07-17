import os
import uuid
import json  # Added for parsing raw JSON strings
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
print("========",SERVICE_ACCOUNT_ENV,DEFAULT_SPREADSHEET_ID)
class ExpenseDatabase:
    def __init__(self, spreadsheet_id=None):
        # Authenticate using either a file path or a raw JSON string
        if not SERVICE_ACCOUNT_ENV:
            raise ValueError("❌ Error: GOOGLE_CREDENTIALS_JSON environment variable is completely empty or missing.")

        try:
            # Scenario A: Check if the string points to a physical file path layout
            if os.path.exists(SERVICE_ACCOUNT_ENV):
                creds = Credentials.from_service_account_file(
                    SERVICE_ACCOUNT_ENV,
                    scopes=["https://www.googleapis.com/auth/spreadsheets"]
                )
                logger.info(f"📡 Authenticated via local keyfile path: {SERVICE_ACCOUNT_ENV}")
            
            # Scenario B: Assume it is a raw credentials JSON string matrix
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
                f"nor could it be parsed as a raw JSON dictionary matrix. Value trace snippet: {SERVICE_ACCOUNT_ENV[:30]}..."
            )
        except Exception as auth_err:
            raise RuntimeError(f"❌ Structural authentication error: {auth_err}")

        # Build service setup downstream
        service = build(
            "sheets",
            "v4",
            credentials=creds
        )

        self.sheet = service.spreadsheets()
        
        # Prioritizes the passed runtime ID. Falls back to .env if empty/None.
        self.spreadsheet_id = spreadsheet_id or DEFAULT_SPREADSHEET_ID
        
        if not self.spreadsheet_id:
            logger.warning("Warning: No Spreadsheet ID provided or found in environment variables.")

        logger.info(f"Connected to Google Sheets ID: {self.spreadsheet_id}")
        
        if self.spreadsheet_id:
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
        expense = [
            expense_id,
            datetime.now().strftime("%Y-%m-%d"),
            category,
            amount,
            description
        ]
        logger.info(f"Adding Expense : {expense}")
        
        self.sheet.values().append(
            spreadsheetId=self.spreadsheet_id,
            range=f"{SHEET_NAME}!A:E",
            valueInputOption="RAW",
            insertDataOption="INSERT_ROWS",
            body={"values": [expense]}
        ).execute()

        return {"status": "success", "expense_id": expense_id}
        
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
                    "expense_id": row[0],
                    "date": row[1],
                    "category": row[2],
                    "amount": float(row[3]) if len(row) > 3 else 0.0,
                    "description": row[4] if len(row) > 4 else ""
                })
            logger.info(f"{len(expenses)} expenses found.")
            return expenses
        except Exception as e:
            logger.error(f"Error fetching expenses: {e}")
            return []
    
    def get_last_expense(self):
        logger.info("Fetching last expense.")
        expenses = self.get_expenses()
        if not expenses:
            return {"message": "No expenses found."}
        return expenses[-1]
    
    def update_expense(self, expense_id, amount=None, category=None, description=None):
        logger.info(f"Updating Expense : {expense_id}")
        result = self.sheet.values().get(
            spreadsheetId=self.spreadsheet_id,
            range=f"{SHEET_NAME}!A:E"
        ).execute()
        values = result.get("values", [])

        if len(values) <= 1:
            return None

        for row_number, row in enumerate(values[1:], start=2):
            if row[0] == expense_id:
                if category is not None:
                    row[2] = category
                if amount is not None:
                    row[3] = str(amount)
                if description is not None:
                    if len(row) < 5:
                        row.append(description)
                    else:
                        row[4] = description

                self.sheet.values().update(
                    spreadsheetId=self.spreadsheet_id,
                    range=f"{SHEET_NAME}!A{row_number}:E{row_number}",
                    valueInputOption="RAW",
                    body={"values": [row]}
                ).execute()
                logger.info("Expense Updated Successfully.")
                return {"status": "success", "expense_id": expense_id}

        logger.warning("Expense ID not found.")
        return None 
    
    def delete_expense(self, expense_id):
        logger.info(f"Deleting Expense : {expense_id}")
        result = self.sheet.values().get(
            spreadsheetId=self.spreadsheet_id,
            range=f"{SHEET_NAME}!A:E"
        ).execute()
        values = result.get("values", [])

        if len(values) <= 1:
            return False

        updated_rows = [values[0]]
        deleted = False

        for row in values[1:]:
            if row[0] == expense_id:
                deleted = True
                continue
            updated_rows.append(row)

        if deleted:
            self.sheet.values().clear(
                spreadsheetId=self.spreadsheet_id,
                range=f"{SHEET_NAME}!A:E"
            ).execute()

            self.sheet.values().update(
                spreadsheetId=self.spreadsheet_id,
                range=f"{SHEET_NAME}!A:E",
                valueInputOption="RAW",
                body={"values": updated_rows}
            ).execute()
            logger.info("Expense Deleted Successfully.")

        return deleted
    
    def total_spending(self):
        logger.info("Calculating Total Spending.")
        expenses = self.get_expenses()
        return sum(expense["amount"] for expense in expenses)
    
    def category_summary(self):
        logger.info("Generating Category Summary.")
        expenses = self.get_expenses()
        summary = {}
        for expense in expenses:
            category = expense["category"]
            summary[category] = summary.get(category, 0) + expense["amount"]
        return summary