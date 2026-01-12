"""
Custom tools for CrewAI agents to query transaction data.
"""

import sys
from pathlib import Path
from typing import Type
from crewai.tools import BaseTool
from pydantic import BaseModel, Field

# Add parent to path for gmail_fetcher import
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

from gmail_fetcher import get_supabase_client


class QueryTransactionsInput(BaseModel):
    """Input for QueryTransactionsTool."""
    limit: int = Field(default=100, description="Maximum number of transactions to return")


class QueryTransactionsTool(BaseTool):
    """Tool to query transactions from the database."""
    
    name: str = "Query Transactions"
    description: str = (
        "Query credit card transactions from the database. "
        "Returns transactions with their date, description, amount, category, and type."
    )
    args_schema: Type[BaseModel] = QueryTransactionsInput
    
    def _run(self, limit: int = 100) -> str:
        """Fetch transactions from Supabase."""
        try:
            client = get_supabase_client()
            result = (
                client.table("transactions")
                .select("transaction_date, description, amount, category, transaction_type")
                .order("transaction_date", desc=True)
                .limit(limit)
                .execute()
            )
            
            transactions = result.data
            if not transactions:
                return "No transactions found in the database."
            
            output = f"Found {len(transactions)} transactions:\n\n"
            for tx in transactions:
                tx_type = "+" if tx["transaction_type"] == "credit" else "-"
                output += f"- {tx['transaction_date']}: {tx_type}${tx['amount']:.2f} | {tx['category']} | {tx['description'][:50]}\n"
            
            return output
            
        except Exception as e:
            return f"Error querying transactions: {str(e)}"


class EmptyInput(BaseModel):
    """Empty input schema for tools that don't need input."""
    pass


class GetCategoryStatsTool(BaseTool):
    """Tool to get spending statistics by category."""
    
    name: str = "Get Category Stats"
    description: str = (
        "Get spending breakdown by category. "
        "Returns total amount spent in each category."
    )
    args_schema: Type[BaseModel] = EmptyInput
    
    def _run(self) -> str:
        """Get category statistics from Supabase."""
        try:
            client = get_supabase_client()
            result = (
                client.table("transactions")
                .select("category, amount, transaction_type")
                .eq("transaction_type", "debit")
                .execute()
            )
            
            transactions = result.data
            if not transactions:
                return "No debit transactions found."
            
            category_totals = {}
            for tx in transactions:
                cat = tx["category"] or "Uncategorized"
                category_totals[cat] = category_totals.get(cat, 0) + float(tx["amount"])
            
            sorted_cats = sorted(category_totals.items(), key=lambda x: x[1], reverse=True)
            total = sum(category_totals.values())
            
            output = f"Total spending: ${total:,.2f}\n\nBreakdown by category:\n"
            for cat, amount in sorted_cats:
                pct = (amount / total) * 100 if total > 0 else 0
                output += f"- {cat}: ${amount:,.2f} ({pct:.1f}%)\n"
            
            return output
            
        except Exception as e:
            return f"Error getting category stats: {str(e)}"


class GetMonthlyTrendsTool(BaseTool):
    """Tool to get monthly spending trends."""
    
    name: str = "Get Monthly Trends"
    description: str = (
        "Get monthly spending trends over time. "
        "Returns total spending per month to identify trends."
    )
    args_schema: Type[BaseModel] = EmptyInput
    
    def _run(self) -> str:
        """Get monthly trends from Supabase."""
        try:
            client = get_supabase_client()
            result = (
                client.table("transactions")
                .select("transaction_date, amount, transaction_type")
                .eq("transaction_type", "debit")
                .order("transaction_date")
                .execute()
            )
            
            transactions = result.data
            if not transactions:
                return "No debit transactions found."
            
            monthly_totals = {}
            for tx in transactions:
                month = tx["transaction_date"][:7]
                monthly_totals[month] = monthly_totals.get(month, 0) + float(tx["amount"])
            
            sorted_months = sorted(monthly_totals.items())
            
            output = "Monthly spending trends:\n\n"
            prev_amount = None
            for month, amount in sorted_months:
                if prev_amount is not None:
                    change = amount - prev_amount
                    change_str = f" (↑${change:,.2f})" if change > 0 else f" (↓${abs(change):,.2f})" if change < 0 else " (→)"
                else:
                    change_str = ""
                output += f"- {month}: ${amount:,.2f}{change_str}\n"
                prev_amount = amount
            
            if len(sorted_months) >= 2:
                first = sorted_months[0][1]
                last = sorted_months[-1][1]
                avg = sum(m[1] for m in sorted_months) / len(sorted_months)
                output += f"\nAverage monthly spending: ${avg:,.2f}"
            
            return output
            
        except Exception as e:
            return f"Error getting monthly trends: {str(e)}"


class DetectAnomaliesTool(BaseTool):
    """Tool to detect unusual transactions."""
    
    name: str = "Detect Anomalies"
    description: str = (
        "Detect unusual transactions like duplicates or unusually large amounts."
    )
    args_schema: Type[BaseModel] = EmptyInput
    
    def _run(self) -> str:
        """Detect anomalies in transactions."""
        try:
            client = get_supabase_client()
            result = (
                client.table("transactions")
                .select("id, transaction_date, description, amount, category, transaction_type")
                .eq("transaction_type", "debit")
                .execute()
            )
            
            transactions = result.data
            if not transactions:
                return "No debit transactions found."
            
            anomalies = []
            amounts = [float(tx["amount"]) for tx in transactions]
            avg_amount = sum(amounts) / len(amounts)
            large_threshold = avg_amount * 3
            
            # Check for duplicates
            seen = {}
            for tx in transactions:
                key = f"{tx['transaction_date']}_{tx['description'][:30]}_{tx['amount']}"
                if key in seen:
                    anomalies.append({
                        "type": "Potential Duplicate",
                        "transaction": tx,
                        "reason": f"Same as another transaction"
                    })
                seen[key] = tx
            
            # Check for unusually large
            for tx in transactions:
                if float(tx["amount"]) > large_threshold:
                    anomalies.append({
                        "type": "Unusually Large",
                        "transaction": tx,
                        "reason": f"Amount is {float(tx['amount'])/avg_amount:.1f}x average"
                    })
            
            if not anomalies:
                return "No anomalies detected. All transactions appear normal."
            
            output = f"Found {len(anomalies)} potential anomalies:\n\n"
            output += "| Date | Description | Amount | Type | Reason |\n"
            output += "| --- | --- | --- | --- | --- |\n"
            for a in anomalies:
                tx = a["transaction"]
                output += f"| {tx['transaction_date']} | {tx['description'][:35]} | ${float(tx['amount']):,.2f} | {a['type']} | {a['reason']} |\n"
            
            return output
            
        except Exception as e:
            return f"Error detecting anomalies: {str(e)}"


def get_analysis_tools():
    """Return list of all analysis tools."""
    return [
        QueryTransactionsTool(),
        GetCategoryStatsTool(),
        GetMonthlyTrendsTool(),
        DetectAnomaliesTool(),
    ]
