"""
CrewAI Crew definition for transaction analysis.
"""

import os
from crewai import Agent, Task, Crew, Process, LLM

from .tools import get_analysis_tools


def create_analysis_crew():
    """Create and return the transaction analysis crew."""
    
    # Configure Ollama LLM
    llm = LLM(
        model="ollama/llama3.2",
        base_url="http://localhost:11434",
    )
    
    # Get all tools
    tools = get_analysis_tools()
    
    # Define Agents
    spending_analyst = Agent(
        role="Spending Analyst",
        goal="Analyze spending patterns and identify key insights from transaction data",
        backstory=(
            "You are an expert financial analyst specializing in personal spending patterns. "
            "You excel at finding trends and summarizing where money goes."
        ),
        tools=tools,
        llm=llm,
        verbose=True,
    )
    
    budget_advisor = Agent(
        role="Budget Advisor",
        goal="Provide actionable budget recommendations based on spending analysis",
        backstory=(
            "You are a certified financial planner who helps people optimize their budgets. "
            "You find opportunities to save money and give practical advice."
        ),
        tools=tools,
        llm=llm,
        verbose=True,
    )
    
    anomaly_detector = Agent(
        role="Anomaly Detector",
        goal="Identify unusual transactions, duplicates, and potential issues",
        backstory=(
            "You are a fraud detection specialist with a keen eye for unusual patterns. "
            "You spot duplicate charges and unusually large transactions."
        ),
        tools=tools,
        llm=llm,
        verbose=True,
    )
    
    # Define Tasks
    spending_analysis_task = Task(
        description=(
            "Analyze the user's spending patterns:\n"
            "1. Use 'Get Category Stats' to get spending breakdown\n"
            "2. Use 'Get Monthly Trends' to identify trends over time\n"
            "3. Identify the top 3 spending categories\n"
            "4. Note any significant changes in spending patterns\n\n"
            "Provide a clear, concise summary."
        ),
        expected_output=(
            "A spending analysis summary with:\n"
            "- Total spending amount\n"
            "- Top 3 categories with amounts\n"
            "- Monthly trend (increasing/decreasing)\n"
            "- Key insight"
        ),
        agent=spending_analyst,
    )
    
    budget_advice_task = Task(
        description=(
            "Based on the spending analysis, provide budget recommendations:\n"
            "1. Identify categories where spending could be reduced\n"
            "2. Suggest specific ways to save money\n"
            "3. Recommend one actionable next step\n\n"
            "Be practical and specific."
        ),
        expected_output=(
            "Budget recommendations with:\n"
            "- 2-3 areas for spending reduction\n"
            "- Practical tips\n"
            "- Estimated monthly savings\n"
            "- One actionable next step"
        ),
        agent=budget_advisor,
    )
    
    anomaly_detection_task = Task(
        description=(
            "Use 'Detect Anomalies' tool to find unusual transactions. "
            "The tool returns a markdown table with flagged transactions. "
            "Copy that table exactly to your final answer and add recommendations."
        ),
        expected_output=(
            "A markdown table like this:\n\n"
            "| Date | Description | Amount | Type | Reason |\n"
            "| --- | --- | --- | --- | --- |\n"
            "| 2024-05-16 | Gift Card Purchase | $500.00 | Unusually Large | 14.3x average |\n"
            "| 2024-12-30 | DELTA DELTA.COM | $312.56 | Unusually Large | 8.9x average |\n\n"
            "Then add: Recommended Actions: (list 2-3 actions)"
        ),
        agent=anomaly_detector,
    )
    
    # Create the Crew
    crew = Crew(
        agents=[spending_analyst, budget_advisor, anomaly_detector],
        tasks=[spending_analysis_task, budget_advice_task, anomaly_detection_task],
        process=Process.sequential,
        verbose=True,
    )
    
    return crew


def run_analysis():
    """Run the analysis crew and return results."""
    crew = create_analysis_crew()
    result = crew.kickoff()
    return result
