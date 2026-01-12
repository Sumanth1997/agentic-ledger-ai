#!/usr/bin/env python3
"""
Analyze Spending - Run CrewAI agents to analyze transactions.

Usage:
    python analyze_spending.py

This script runs a crew of AI agents that:
1. Analyze spending patterns and trends
2. Provide budget recommendations
3. Detect unusual transactions or duplicates

Results are saved to a JSON file for dashboard display.
"""

import os
import json
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from agents.crew import run_analysis


def main():
    """Main entry point."""
    print("=" * 60)
    print("🤖 CrewAI Spending Analysis")
    print("=" * 60)
    print()
    print("Starting analysis crew with 3 agents:")
    print("  • Spending Analyst - Pattern analysis")
    print("  • Budget Advisor - Recommendations")
    print("  • Anomaly Detector - Issue detection")
    print()
    print("This may take a few minutes with local LLM...")
    print("-" * 60)
    print()
    
    try:
        # Run the analysis crew
        result = run_analysis()
        
        print()
        print("=" * 60)
        print("📊 ANALYSIS COMPLETE")
        print("=" * 60)
        print()
        print(result)
        
        # Save results for dashboard
        output_file = Path(__file__).parent / "analysis_results.json"
        results_data = {
            "timestamp": datetime.now().isoformat(),
            "analysis": str(result),
            "status": "completed",
        }
        
        with open(output_file, "w") as f:
            json.dump(results_data, f, indent=2)
        
        print()
        print(f"✓ Results saved to: {output_file}")
        
        return 0
        
    except Exception as e:
        print(f"✗ Error running analysis: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
