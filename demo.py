"""
Single-Command Demo Script
Demonstrates all system capabilities in one execution.

Usage: python demo.py
"""

import sys
from pathlib import Path
import json
from datetime import datetime
import asyncio

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.autogen_orchestrator import AutoGenOrchestrator
from src.guardrails.safety_manager import SafetyManager
from src.evaluation.judge import LLMJudge
import yaml
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def load_config():
    """Load configuration file."""
    config_path = Path("config.yaml")
    if config_path.exists():
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    return {}


def print_section(title: str):
    """Print a formatted section header."""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")


def print_agent_status(agent_name: str, action: str):
    """Print agent status with emoji."""
    emoji_map = {
        "Planner": "📋",
        "Researcher": "🔍",
        "Writer": "✍️",
        "Critic": "⚖️"
    }
    emoji = emoji_map.get(agent_name, "🤖")
    print(f"{emoji} {agent_name}: {action}")


def truncate_content(content: str, max_length: int = 2000) -> str:
    """Truncate content for display."""
    if len(content) <= max_length:
        return content
    return content[:max_length] + f"\n... [truncated, {len(content) - max_length} more characters]"


def save_session_export(query: str, result: dict, filename_prefix: str = "demo_session"):
    """Save complete session data to JSON."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = Path("outputs")
    output_dir.mkdir(exist_ok=True)
    
    # Prepare session data
    session_data = {
        "timestamp": datetime.now().isoformat(),
        "query": query,
        "response": result.get("response", ""),
        "conversation_history": [],
        "metadata": {
            "source_count": result.get("metadata", {}).get("source_count", 0),
            "research_plan": result.get("metadata", {}).get("research_plan", ""),
            "processing_time": result.get("metadata", {}).get("processing_time", 0)
        },
        "citations": result.get("citations", []),
        "safety_events": result.get("safety_events", [])
    }
    
    # Extract conversation history from agent_traces
    if "agent_traces" in result:
        for trace in result["agent_traces"]:
            # Handle both dict and object types
            if isinstance(trace, dict):
                role = trace.get("role", "assistant")
                name = trace.get("name", "unknown")
                content = trace.get("content", "")
            else:
                # Handle object with attributes
                role = getattr(trace, "role", "assistant")
                name = getattr(trace, "name", "unknown")
                content = getattr(trace, "content", "")
            
            session_data["conversation_history"].append({
                "index": len(session_data["conversation_history"]) + 1,
                "role": role,
                "name": name,
                "content": content
            })
    
    # Save to file
    output_file = output_dir / f"{filename_prefix}_{timestamp}.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(session_data, f, indent=2, ensure_ascii=False)
    
    return output_file


def save_markdown_response(query: str, response: str, citations: list, score: float, filename_prefix: str = "demo_response"):
    """Save response in markdown format."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = Path("outputs")
    output_dir.mkdir(exist_ok=True)
    
    markdown_content = f"""# Research Query Response

**Query:** {query}

**Generated:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

**Overall Quality Score:** {score:.2f}/1.0

---

## Response

{response}

---

## References

"""
    
    # Add citations
    if citations:
        for citation in citations:
            markdown_content += f"{citation}\n\n"
    else:
        markdown_content += "No citations available.\n"
    
    # Save to file
    output_file = output_dir / f"{filename_prefix}_{timestamp}.md"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(markdown_content)
    
    return output_file


def save_judge_results(query: str, judge_result: dict, filename_prefix: str = "demo_judge"):
    """Save judge evaluation results."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = Path("outputs")
    output_dir.mkdir(exist_ok=True)
    
    # Prepare judge data
    judge_data = {
        "timestamp": datetime.now().isoformat(),
        "query": query,
        "overall_score": judge_result.get("overall_score", 0.0),
        "criteria_scores": judge_result.get("criteria_scores", {}),
        "reasoning": judge_result.get("reasoning", {})
    }
    
    # Save to file
    output_file = output_dir / f"{filename_prefix}_{timestamp}.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(judge_data, f, indent=2, ensure_ascii=False)
    
    return output_file


async def run_demo():
    """Run the complete demo."""
    print_section("🚀 Multi-Agent Research System Demo")
    
    print("This demo demonstrates:")
    print("✅ Input Safety Validation")
    print("✅ Multi-Agent Orchestration (4 agents)")
    print("✅ Real-Time Status Display")
    print("✅ Response Synthesis with Citations")
    print("✅ LLM-as-a-Judge Evaluation")
    print("✅ File Exports (JSON + Markdown)")
    
    # Load config
    config = load_config()
    
    # Demo query
    demo_query = "How can procedural generation techniques be combined with machine learning for world building?"
    
    print_section("📝 Test Query")
    print(f"Query: {demo_query}\n")
    
    # Initialize safety manager
    print_section("🛡️ Safety Validation")
    print("Validating query through input guardrails...")
    safety_manager = SafetyManager(config.get("guardrails", {}))
    safety_result = safety_manager.check_input_safety(demo_query)
    
    if not safety_result.get("safe", True):
        violations = safety_result.get("violations", [])
        for v in violations:
            print(f"❌ BLOCKED: {v.get('category')} - {v.get('reason')}")
        return
    
    print("✅ Query passed all safety checks")
    
    # Initialize orchestrator
    print_section("🤖 Multi-Agent Processing")
    print("Initializing 4 specialized agents:")
    print("  📋 Planner - Creates research plan")
    print("  🔍 Researcher - Gathers sources (web + academic papers)")
    print("  ✍️ Writer - Synthesizes findings")
    print("  ⚖️ Critic - Verifies quality\n")
    
    orchestrator = AutoGenOrchestrator(config)
    
    print("Processing query through agent workflow...\n")
    
    # Process query
    result = await orchestrator.process_query(demo_query)
    
    # Display agent conversation
    print_section("💬 Agent Conversation Traces")
    if "agent_traces" in result and result["agent_traces"]:
        for i, trace in enumerate(result["agent_traces"][:10], 1):  # Show first 10 messages
            # Handle both dict and object types
            if isinstance(trace, dict):
                name = trace.get("name", "unknown")
                content = trace.get("content", "")
            else:
                name = getattr(trace, "name", "unknown")
                content = getattr(trace, "content", "")
            
            print(f"\n--- Message {i}: {name} ---")
            print(truncate_content(content, 500))
        
        if len(result["agent_traces"]) > 10:
            print(f"\n... [{len(result['agent_traces']) - 10} more messages in full export]")
    
    # Display response
    print_section("✨ Final Synthesized Response")
    response = result.get("response", "No response generated")
    print(truncate_content(response, 1000))
    
    # Display citations
    print_section("📚 Citations (APA Format)")
    citations = result.get("citations", [])
    if citations:
        for i, citation in enumerate(citations[:5], 1):  # Show first 5
            print(f"{i}. {citation}")
        if len(citations) > 5:
            print(f"\n... [{len(citations) - 5} more citations in full export]")
    else:
        print("No citations found")
    
    # Run LLM-as-a-Judge evaluation
    print_section("⚖️ LLM-as-a-Judge Evaluation")
    print("Evaluating response quality on 5 criteria...")
    
    judge = LLMJudge(config.get("judge", {}))
    judge_result = await judge.evaluate_response(demo_query, response)
    
    print(f"\n{'Criterion':<25} {'Score':<10} {'Reasoning'}")
    print("-" * 80)
    
    # Display scores
    overall_score = judge_result.get("overall_score", 0.0)
    criteria_scores = judge_result.get("criteria_scores", {})
    reasoning = judge_result.get("reasoning", {})
    
    for criterion, score in criteria_scores.items():
        reason_text = reasoning.get(criterion, "No reasoning provided")
        reason_preview = reason_text[:60] + "..." if len(reason_text) > 60 else reason_text
        print(f"{criterion:<25} {score:<10.2f} {reason_preview}")
    
    print("-" * 80)
    print(f"{'Overall Score':<25} {overall_score:<10.2f}")
    
    # Save all outputs
    print_section("💾 Saving Outputs")
    
    # Save session export
    session_file = save_session_export(demo_query, result, "demo_session")
    print(f"✅ Session export: {session_file}")
    print(f"   Size: {session_file.stat().st_size / 1024:.1f} KB")
    
    # Save markdown response
    md_file = save_markdown_response(demo_query, response, citations, overall_score, "demo_response")
    print(f"✅ Markdown response: {md_file}")
    print(f"   Size: {md_file.stat().st_size / 1024:.1f} KB")
    
    # Save judge results
    judge_file = save_judge_results(demo_query, judge_result, "demo_judge")
    print(f"✅ Judge evaluation: {judge_file}")
    print(f"   Size: {judge_file.stat().st_size / 1024:.1f} KB")
    
    print_section("✅ Demo Complete")
    print(f"Overall Quality Score: {overall_score:.2f}/1.0")
    print(f"Citations Generated: {len(citations)}")
    print(f"Agent Messages: {len(result.get('agent_traces', []))}")
    print("\nAll outputs saved to 'outputs/' directory")


def main():
    """Main entry point."""
    try:
        asyncio.run(run_demo())
    except KeyboardInterrupt:
        print("\n\nDemo interrupted by user")
    except Exception as e:
        print(f"\n❌ Error during demo: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
