"""
Main Entry Point
Can be used to run the system or evaluation.

Usage:
  python main.py --mode cli           # Run CLI interface
  python main.py --mode web           # Run web interface
  python main.py --mode evaluate      # Run evaluation
"""

import argparse
import asyncio
import sys
from pathlib import Path


def run_cli():
    """Run CLI interface."""
    from src.ui.cli import main as cli_main
    cli_main()


def run_web():
    """Run web interface."""
    import subprocess
    print("Starting Streamlit web interface...")
    subprocess.run(["streamlit", "run", "src/ui/streamlit_app.py"])


async def run_evaluation():
    """Run system evaluation using SystemEvaluator."""
    import yaml
    import json
    from dotenv import load_dotenv
    from src.evaluation.evaluator import SystemEvaluator
    
    # Load environment variables
    load_dotenv()

    # Load config
    with open("config.yaml", 'r') as f:
        config = yaml.safe_load(f)

    # Load test queries
    with open("data/example_queries.json", 'r') as f:
        queries_data = json.load(f)
        test_queries = queries_data.get("queries", [])

    print("\n" + "=" * 80)
    print("MULTI-AGENT SYSTEM EVALUATION")
    print("=" * 80)
    print(f"\nResearch Topic: {config.get('system', {}).get('topic', 'HCI Research')}")
    print(f"Model: {config.get('models', {}).get('default', {}).get('name', 'gpt-4o-mini')}")
    print(f"Test Queries: {len(test_queries)}")
    print(f"Evaluation Criteria: {', '.join(config.get('evaluation', {}).get('criteria', []))}")
    
    # Initialize evaluator
    print("\n" + "-" * 80)
    print("Initializing SystemEvaluator...")
    evaluator = SystemEvaluator(config)
    
    # Run evaluation
    print("\n" + "-" * 80)
    print("Running evaluation on test queries...")
    print("This may take several minutes depending on the number of queries...")
    print("-" * 80 + "\n")
    
    results = await evaluator.evaluate_system(test_queries)
    
    # Display results
    print("\n" + "=" * 80)
    print("EVALUATION RESULTS")
    print("=" * 80)
    
    print(f"\nOverall Score: {results['overall_score']:.3f}")
    print(f"Total Queries Evaluated: {results['total_queries']}")
    print(f"Successful: {results['successful_queries']}")
    print(f"Failed: {results['failed_queries']}")
    
    print("\n" + "-" * 80)
    print("CRITERION SCORES:")
    for criterion, score in results['criterion_averages'].items():
        print(f"  {criterion}: {score:.3f}")
    
    if results.get('best_query'):
        print("\n" + "-" * 80)
        print("BEST PERFORMING QUERY:")
        print(f"  Query: {results['best_query']['query'][:80]}...")
        print(f"  Score: {results['best_query']['score']:.3f}")
    
    if results.get('worst_query'):
        print("\n" + "-" * 80)
        print("LOWEST PERFORMING QUERY:")
        print(f"  Query: {results['worst_query']['query'][:80]}...")
        print(f"  Score: {results['worst_query']['score']:.3f}")
    
    print("\n" + "=" * 80)
    print("EVALUATION COMPLETE")
    print("=" * 80)
    print(f"\nDetailed results saved to: {results.get('report_path', 'outputs/evaluation_report.json')}")
    print(f"Timestamp: {results.get('timestamp', '')}")
    print("\nReview the JSON report for detailed per-query evaluations.")
    print("=" * 80 + "\n")


def run_autogen():
    """Run AutoGen example."""
    import subprocess
    print("Running AutoGen example...")
    subprocess.run([sys.executable, "example_autogen.py"])


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Multi-Agent Research Assistant"
    )
    parser.add_argument(
        "--mode",
        choices=["cli", "web", "evaluate", "autogen"],
        default="autogen",
        help="Mode to run: cli, web, evaluate, or autogen (default)"
    )
    parser.add_argument(
        "--config",
        default="config.yaml",
        help="Path to configuration file"
    )

    args = parser.parse_args()

    if args.mode == "cli":
        run_cli()
    elif args.mode == "web":
        run_web()
    elif args.mode == "evaluate":
        asyncio.run(run_evaluation())
    elif args.mode == "autogen":
        run_autogen()


if __name__ == "__main__":
    main()
