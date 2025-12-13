"""
Quick Verification Script for Assignment 3
Run this to verify all grading requirements are met before submission.

Usage: python verify_requirements.py
"""

import os
import sys
import json
import glob
from pathlib import Path


def print_header(title):
    """Print section header."""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)


def check_file_exists(filepath, description):
    """Check if a file exists."""
    exists = Path(filepath).exists()
    status = "✅" if exists else "❌"
    print(f"{status} {description}: {filepath}")
    return exists


def check_import(module_path, description):
    """Check if a module can be imported."""
    try:
        parts = module_path.split(".")
        module = __import__(module_path, fromlist=[parts[-1]])
        print(f"✅ {description}: {module_path}")
        return True
    except Exception as e:
        print(f"❌ {description}: {module_path} - Error: {str(e)}")
        return False


def check_json_structure(filepath, expected_keys, description):
    """Check JSON file structure."""
    try:
        with open(filepath, 'r') as f:
            data = json.load(f)
            
        if isinstance(data, list):
            print(f"✅ {description}: Array with {len(data)} items")
            if data and expected_keys:
                first_item = data[0]
                missing = [k for k in expected_keys if k not in first_item]
                if missing:
                    print(f"   ⚠️  Missing keys in first item: {missing}")
            return True
        elif isinstance(data, dict):
            missing = [k for k in expected_keys if k not in data]
            if missing:
                print(f"⚠️  {description}: Missing keys: {missing}")
            else:
                print(f"✅ {description}: All required keys present")
            return len(missing) == 0
    except Exception as e:
        print(f"❌ {description}: Error reading {filepath} - {str(e)}")
        return False


def count_lines(filepath):
    """Count lines in a file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return len(f.readlines())
    except:
        return 0


def main():
    """Run all verification checks."""
    print_header("🔍 Assignment 3 Requirements Verification")
    
    all_passed = True
    
    # 1. System Architecture (20 pts)
    print_header("1. System Architecture & Orchestration (20 pts)")
    
    # Check agents
    all_passed &= check_import("src.agents.autogen_agents", "Planner Agent")
    all_passed &= check_import("src.agents.autogen_agents", "Researcher Agent")
    all_passed &= check_import("src.agents.autogen_agents", "Writer Agent")
    all_passed &= check_import("src.agents.autogen_agents", "Critic Agent")
    
    # Check orchestrator
    all_passed &= check_import("src.autogen_orchestrator", "AutoGen Orchestrator")
    
    # Check tools
    all_passed &= check_import("src.tools.web_search", "Web Search Tool")
    all_passed &= check_import("src.tools.paper_search", "Paper Search Tool")
    all_passed &= check_import("src.tools.citation_tool", "Citation Tool")
    
    # 2. User Interface (15 pts)
    print_header("2. User Interface & UX (15 pts)")
    
    all_passed &= check_file_exists("src/ui/streamlit_app.py", "Streamlit Web UI")
    all_passed &= check_file_exists("src/ui/cli.py", "CLI Interface")
    all_passed &= check_file_exists("main.py", "Main Entry Point")
    
    # 3. Safety & Guardrails (15 pts)
    print_header("3. Safety & Guardrails (15 pts)")
    
    all_passed &= check_import("src.guardrails.safety_manager", "Safety Manager")
    all_passed &= check_import("src.guardrails.input_guardrail", "Input Guardrail")
    all_passed &= check_import("src.guardrails.output_guardrail", "Output Guardrail")
    
    # Check safety policies count
    try:
        from src.guardrails.safety_manager import SafetyManager
        manager = SafetyManager({})
        policy_count = len(manager.input_filters) + len(manager.output_filters)
        if policy_count >= 3:
            print(f"✅ Safety Policies: {policy_count} categories (≥3 required)")
        else:
            print(f"❌ Safety Policies: Only {policy_count} categories (need ≥3)")
            all_passed = False
    except Exception as e:
        print(f"❌ Could not verify safety policies: {e}")
        all_passed = False
    
    # 4. Evaluation (20 pts)
    print_header("4. Evaluation (LLM-as-a-Judge) (20 pts)")
    
    all_passed &= check_import("src.evaluation.judge", "LLM Judge")
    all_passed &= check_import("src.evaluation.evaluator", "System Evaluator")
    
    # Check test queries
    if check_file_exists("data/example_queries.json", "Test Queries File"):
        try:
            with open("data/example_queries.json", 'r') as f:
                queries = json.load(f)
                query_count = len(queries) if isinstance(queries, list) else len(queries.get("queries", []))
                if query_count >= 5:
                    print(f"✅ Test Queries Count: {query_count} (≥5 required)")
                else:
                    print(f"❌ Test Queries Count: Only {query_count} (need ≥5)")
                    all_passed = False
        except Exception as e:
            print(f"❌ Error reading test queries: {e}")
            all_passed = False
    else:
        all_passed = False
    
    # 5. Required Deliverables
    print_header("5. Required Deliverables")
    
    # Check demo script
    all_passed &= check_file_exists("demo.py", "Demo Script")
    
    # Check for exported artifacts
    print("\nChecking exported artifacts in outputs/:")
    
    session_files = glob.glob("outputs/*session*.json")
    response_files = glob.glob("outputs/*response*.md")
    judge_files = glob.glob("outputs/*judge*.json")
    eval_files = glob.glob("outputs/evaluation*.json")
    
    if session_files:
        print(f"✅ Session exports: {len(session_files)} found")
        # Check structure of most recent
        latest = max(session_files, key=os.path.getctime)
        check_json_structure(latest, ["query", "response", "conversation_history"], 
                           "Latest session export")
    else:
        print("⚠️  No session exports found. Run: python demo.py")
    
    if response_files:
        print(f"✅ Response exports (MD): {len(response_files)} found")
    else:
        print("⚠️  No markdown response exports found. Run: python demo.py")
    
    if judge_files:
        print(f"✅ Judge results: {len(judge_files)} found")
    else:
        print("⚠️  No judge results found. Run: python demo.py")
    
    if eval_files:
        print(f"✅ Evaluation results: {len(eval_files)} found")
    else:
        print("⚠️  No batch evaluation results found. Run: python main.py --mode evaluate")
    
    # 6. Report Quality (20 pts)
    print_header("6. Report Quality (20 pts)")
    
    if check_file_exists("TECHNICAL_REPORT.md", "Technical Report"):
        lines = count_lines("TECHNICAL_REPORT.md")
        words = lines * 10  # Rough estimate
        if 800 <= words <= 1500:
            print(f"✅ Report length: ~{words} words ({lines} lines) - Good!")
        elif words < 800:
            print(f"⚠️  Report length: ~{words} words - May be too short (aim for 800-1200)")
        else:
            print(f"✅ Report length: ~{words} words ({lines} lines)")
    else:
        all_passed = False
    
    # Check for APA references
    if Path("TECHNICAL_REPORT.md").exists():
        with open("TECHNICAL_REPORT.md", 'r', encoding='utf-8') as f:
            content = f.read().lower()
            has_references = "references" in content or "bibliography" in content
            has_abstract = "abstract" in content
            
            if has_abstract:
                print("✅ Abstract section found")
            else:
                print("⚠️  No abstract section found")
            
            if has_references:
                print("✅ References section found")
            else:
                print("⚠️  No references section found")
    
    # 7. Reproducibility (10 pts)
    print_header("7. Reproducibility & Documentation (10 pts)")
    
    all_passed &= check_file_exists("README.md", "README file")
    all_passed &= check_file_exists("requirements.txt", "Requirements file")
    all_passed &= check_file_exists(".env.example", "Environment variables template")
    all_passed &= check_file_exists("config.yaml", "Configuration file")
    
    # Check README content
    if Path("README.md").exists():
        with open("README.md", 'r', encoding='utf-8') as f:
            readme = f.read().lower()
            
            checks = [
                ("installation", "Installation instructions"),
                ("api", "API key configuration"),
                ("demo.py" or "python demo.py", "Demo command"),
                ("troubleshooting", "Troubleshooting section"),
            ]
            
            for keyword, description in checks:
                if keyword in readme:
                    print(f"✅ {description} found in README")
                else:
                    print(f"⚠️  {description} not found in README")
    
    # Final Summary
    print_header("📊 Verification Summary")
    
    if all_passed:
        print("\n✅ All core requirements verified!")
        print("\n📋 Next steps before submission:")
        print("1. Run: python demo.py (to generate all exports)")
        print("2. Run: python main.py --mode evaluate (for batch evaluation)")
        print("3. Record demo video (30-60 seconds)")
        print("4. Take 5 screenshots of UI")
        print("5. Update README with video link and screenshots")
        print("6. Final proofread of TECHNICAL_REPORT.md")
        print("7. Commit and push all changes")
    else:
        print("\n⚠️  Some requirements need attention (see above)")
        print("\n🔧 Recommended fixes:")
        print("- Ensure all imports work: pip install -r requirements.txt")
        print("- Generate exports: python demo.py")
        print("- Run evaluation: python main.py --mode evaluate")
        print("- Complete TECHNICAL_REPORT.md sections")
    
    print("\n" + "=" * 80)
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
