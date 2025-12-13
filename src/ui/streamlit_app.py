"""
Streamlit Web Interface
Web UI for the multi-agent research system.

Run with: streamlit run src/ui/streamlit_app.py
"""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import streamlit as st
import asyncio
import yaml
import logging
from datetime import datetime
from typing import Dict, Any
from dotenv import load_dotenv

from src.autogen_orchestrator import AutoGenOrchestrator
from src.guardrails.safety_manager import SafetyManager

# Load environment variables
load_dotenv()

# Setup logging to show in terminal
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)  # Output to stdout so it appears in terminal
    ]
)
logger = logging.getLogger("streamlit_app")


def load_config():
    """Load configuration file."""
    config_path = Path("config.yaml")
    if config_path.exists():
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    return {}


def initialize_session_state():
    """Initialize Streamlit session state."""
    if 'history' not in st.session_state:
        st.session_state.history = []

    if 'orchestrator' not in st.session_state:
        config = load_config()
        # Initialize AutoGen orchestrator
        try:
            st.session_state.orchestrator = AutoGenOrchestrator(config)
        except Exception as e:
            st.error(f"Failed to initialize orchestrator: {e}")
            st.session_state.orchestrator = None
    
    if 'safety_manager' not in st.session_state:
        config = load_config()
        st.session_state.safety_manager = SafetyManager(config.get("safety", {}))

    if 'show_traces' not in st.session_state:
        st.session_state.show_traces = False

    if 'show_safety_log' not in st.session_state:
        st.session_state.show_safety_log = False
    
    if 'safety_events' not in st.session_state:
        st.session_state.safety_events = []
    
    if 'current_agent' not in st.session_state:
        st.session_state.current_agent = None
    
    if 'processing' not in st.session_state:
        st.session_state.processing = False


async def process_query(query: str) -> Dict[str, Any]:
    """
    Process a query through the orchestrator with safety checks.
    
    Args:
        query: Research query to process
        
    Returns:
        Result dictionary with response, citations, metadata, and safety info
    """
    orchestrator = st.session_state.orchestrator
    safety_manager = st.session_state.safety_manager
    
    logger.info(f"=" * 80)
    logger.info(f"Processing query: {query[:100]}...")
    logger.info(f"=" * 80)
    
    if orchestrator is None:
        logger.error("Orchestrator not initialized")
        return {
            "query": query,
            "error": "Orchestrator not initialized",
            "response": "Error: System not properly initialized. Please check your configuration.",
            "citations": [],
            "metadata": {},
            "safety": {"safe": True}
        }
    
    try:
        # Check input safety
        logger.info("Checking input safety...")
        input_safety = safety_manager.check_input_safety(query)
        
        if not input_safety["safe"]:
            logger.warning(f"Input safety violation: {input_safety.get('action', 'unknown')}")
            st.session_state.safety_events.append({
                "timestamp": datetime.now(),
                "type": "input_blocked",
                "details": input_safety
            })
            return {
                "query": query,
                "error": "Safety violation",
                "response": input_safety.get("message", "This query violates safety policies."),
                "citations": [],
                "metadata": {},
                "safety": input_safety
            }
        
        logger.info("Input safety check passed. Processing with orchestrator...")
        
        # Set processing flag
        st.session_state.processing = True
        st.session_state.current_agent = "Initializing"
        
        # Process query through AutoGen orchestrator
        result = orchestrator.process_query(query)
        
        # Clear processing flag
        st.session_state.processing = False
        st.session_state.current_agent = None
        
        logger.info("Orchestrator processing complete")
        
        # Check for errors
        if "error" in result:
            logger.error(f"Orchestrator returned error: {result.get('error')}")
            return result
        
        # Check output safety
        logger.info("Checking output safety...")
        response = result.get("response", "")
        output_safety = safety_manager.check_output_safety(response)
        
        if not output_safety["safe"]:
            logger.warning("Output blocked due to safety violation")
            st.session_state.safety_events.append({
                "timestamp": datetime.now(),
                "type": "output_blocked",
                "details": output_safety
            })
        elif output_safety.get("warnings"):
            logger.info("Output contains warnings")
            st.session_state.safety_events.append({
                "timestamp": datetime.now(),
                "type": "output_warning",
                "details": output_safety
            })
        else:
            logger.info("Output safety check passed")
        
        # Extract citations from conversation history
        logger.info("Extracting citations and agent traces...")
        citations = extract_citations(result)
        
        # Extract agent traces for display
        agent_traces = extract_agent_traces(result)
        
        # Format metadata
        metadata = result.get("metadata", {})
        metadata["agent_traces"] = agent_traces
        metadata["citations"] = citations
        metadata["critique_score"] = calculate_quality_score(result)
        
        # Use sanitized response if available
        final_response = output_safety.get("response", response) if output_safety["safe"] else "Response blocked due to safety concerns."
        
        logger.info(f"Query processing complete. Response length: {len(final_response)} chars")
        logger.info(f"Citations found: {len(citations)}")
        logger.info("=" * 80)
        
        # Build result
        full_result = {
            "query": query,
            "response": final_response,
            "citations": citations,
            "metadata": metadata,
            "safety": output_safety,
            "agent_traces": result.get("conversation_history", [])
        }
        
        # Auto-export session
        save_session_export(full_result)
        
        return full_result
        
    except Exception as e:
        logger.error(f"Exception during query processing: {str(e)}", exc_info=True)
        return {
            "query": query,
            "error": str(e),
            "response": f"An error occurred: {str(e)}",
            "citations": [],
            "metadata": {"error": True},
            "safety": {"safe": True}
        }


def extract_citations(result: Dict[str, Any]) -> list:
    """Extract citations from research result."""
    citations = []
    
    # Look through conversation history for citations
    for msg in result.get("conversation_history", []):
        content = msg.get("content", "")
        
        # Handle case where content might be a list
        if isinstance(content, list):
            content = " ".join(str(item) for item in content)
        elif not isinstance(content, str):
            content = str(content)
        
        # Find URLs in content
        import re
        urls = re.findall(r'https?://[^\s<>"{}|\\^`\[\]]+', content)
        
        # Find citation patterns like [Source: Title]
        citation_patterns = re.findall(r'\[Source: ([^\]]+)\]', content)
        
        for url in urls:
            if url not in citations:
                citations.append(url)
        
        for citation in citation_patterns:
            if citation not in citations:
                citations.append(citation)
    
    return citations[:10]  # Limit to top 10


def extract_agent_traces(result: Dict[str, Any]) -> Dict[str, list]:
    """Extract agent execution traces from conversation history."""
    traces = {}
    
    for msg in result.get("conversation_history", []):
        agent = msg.get("source", "Unknown")
        content = msg.get("content", "")
        
        # Handle case where content might be a list or non-string
        if isinstance(content, list):
            content = " ".join(str(item) for item in content)
        elif not isinstance(content, str):
            content = str(content)
        
        content = content[:200]  # First 200 chars
        
        if agent not in traces:
            traces[agent] = []
        
        traces[agent].append({
            "action_type": "message",
            "details": content
        })
    
    return traces


def save_session_export(result: Dict[str, Any]):
    """Auto-export session data to JSON file."""
    try:
        import json
        from pathlib import Path
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = Path("outputs")
        output_dir.mkdir(exist_ok=True)
        
        # Prepare session data
        session_data = {
            "timestamp": datetime.now().isoformat(),
            "query": result.get("query", ""),
            "response": result.get("response", ""),
            "conversation_history": [],
            "metadata": result.get("metadata", {}),
            "citations": result.get("citations", []),
            "safety_events": result.get("safety", {})
        }
        
        # Extract conversation history
        for trace in result.get("agent_traces", []):
            if isinstance(trace, dict):
                session_data["conversation_history"].append({
                    "role": trace.get("role", "assistant"),
                    "name": trace.get("name", "unknown"),
                    "content": trace.get("content", "")
                })
        
        # Save to file
        output_file = output_dir / f"streamlit_session_{timestamp}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(session_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Session exported to: {output_file}")
        
    except Exception as e:
        logger.error(f"Failed to export session: {e}")


def calculate_quality_score(result: Dict[str, Any]) -> float:
    """Calculate a quality score based on various factors."""
    score = 5.0  # Base score
    
    metadata = result.get("metadata", {})
    
    # Add points for sources
    num_sources = metadata.get("num_sources", 0)
    score += min(num_sources * 0.5, 2.0)
    
    # Add points for critique
    if metadata.get("critique"):
        score += 1.0
    
    # Add points for conversation length (indicates thorough discussion)
    num_messages = metadata.get("num_messages", 0)
    score += min(num_messages * 0.1, 2.0)
    
    return min(score, 10.0)  # Cap at 10


def create_markdown_output(result: Dict[str, Any]) -> str:
    """Create markdown formatted output."""
    output = f"""# Research Query Response

## Query
{result.get('query', 'N/A')}

## Response
{result.get('response', 'No response')}

## Citations
"""
    citations = result.get('citations', [])
    if citations:
        for i, cite in enumerate(citations, 1):
            output += f"{i}. {cite}\n"
    else:
        output += "No citations found.\n"
    
    output += f"""
## Metadata
- **Sources Used**: {result.get('metadata', {}).get('num_sources', 0)}
- **Quality Score**: {result.get('metadata', {}).get('critique_score', 0):.2f}
- **Timestamp**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Safety Status
- **Safe**: {result.get('safety', {}).get('safe', True)}
"""
    violations = result.get('safety', {}).get('violations', [])
    if violations:
        output += "\n### Violations Detected:\n"
        for v in violations:
            output += f"- **{v.get('category')}**: {v.get('message')}\n"
    
    return output


def display_response(result: Dict[str, Any]):
    """
    Display query response with safety indicators, citations, and metadata.
    """
    # Display safety status
    safety_info = result.get("safety", {})
    
    if not safety_info.get("safe"):
        st.error("🛡️ Safety Violation Detected")
        violations = safety_info.get("violations", [])
        for v in violations:
            st.warning(f"**{v.get('category', 'Unknown')}**: {v.get('message', 'Policy violation')}")
        if result.get("error") == "Safety violation":
            return
    
    if safety_info.get("action_taken") == "redacted":
        st.warning("⚠️ Some content has been redacted for safety reasons")
    
    if safety_info.get("warnings"):
        with st.expander("ℹ️ Safety Notes", expanded=False):
            for warning in safety_info["warnings"]:
                st.info(f"• {warning.get('message', 'Quality issue detected')}")
    
    # Check for errors
    if "error" in result and result.get("error") != "Safety violation":
        st.error(f"Error: {result['error']}")
        return

    # Display response
    st.markdown("### 📝 Response")
    response = result.get("response", "")
    if response:
        st.markdown(response)
    else:
        st.warning("No response generated")
    
    # Download buttons
    if response:
        col1, col2 = st.columns(2)
        with col1:
            import json
            json_output = json.dumps(result, indent=2, default=str)
            st.download_button(
                label="📥 Download JSON",
                data=json_output,
                file_name=f"response_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )
        with col2:
            markdown_output = create_markdown_output(result)
            st.download_button(
                label="📥 Download Markdown",
                data=markdown_output,
                file_name=f"response_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                mime="text/markdown"
            )

    # Display citations
    citations = result.get("citations", [])
    if citations:
        with st.expander("📚 Citations", expanded=False):
            for i, citation in enumerate(citations, 1):
                st.markdown(f"**[{i}]** {citation}")

    # Display metadata
    metadata = result.get("metadata", {})

    col1, col2 = st.columns(2)
    with col1:
        st.metric("Sources Used", metadata.get("num_sources", 0))
    with col2:
        score = metadata.get("critique_score", 0)
        st.metric("Quality Score", f"{score:.2f}")

    # Safety events
    safety_events = metadata.get("safety_events", [])
    if safety_events:
        with st.expander("⚠️ Safety Events", expanded=True):
            for event in safety_events:
                event_type = event.get("type", "unknown")
                violations = event.get("violations", [])
                st.warning(f"{event_type.upper()}: {len(violations)} violation(s) detected")
                for violation in violations:
                    st.text(f"  • {violation.get('reason', 'Unknown')}")

    # Agent activity summary
    with st.expander("🤖 Agent Activity Summary", expanded=True):
        agent_traces = metadata.get("agent_traces", {})
        if agent_traces:
            st.markdown("**Agents Involved:**")
            cols = st.columns(4)
            agent_icons = {"Planner": "📋", "Researcher": "🔍", "Writer": "✍️", "Critic": "⚖️"}
            for idx, (agent, actions) in enumerate(agent_traces.items()):
                with cols[idx % 4]:
                    icon = agent_icons.get(agent, "🤖")
                    st.metric(f"{icon} {agent}", f"{len(actions)} actions")
        else:
            st.info("No agent activity recorded. Enable 'Show Agent Traces' in sidebar for details.")
    
    # Agent traces (detailed)
    if st.session_state.show_traces:
        agent_traces = metadata.get("agent_traces", {})
        if agent_traces:
            display_agent_traces(agent_traces)


def display_agent_traces(traces: Dict[str, Any]):
    """
    Display detailed agent execution traces with proper formatting.
    Shows agent workflow, messages, and actions taken.
    """
    with st.expander("🔍 Detailed Agent Conversation Traces", expanded=False):
        agent_icons = {"Planner": "📋", "Researcher": "🔍", "Writer": "✍️", "Critic": "⚖️"}
        
        for agent_name, actions in traces.items():
            icon = agent_icons.get(agent_name, "🤖")
            st.markdown(f"### {icon} {agent_name.upper()}")
            
            if not actions:
                st.info(f"No actions recorded for {agent_name}")
                continue
            
            for idx, action in enumerate(actions, 1):
                action_type = action.get("action_type", "message")
                details = action.get("details", "No details available")
                
                # Truncate long details
                if isinstance(details, str) and len(details) > 300:
                    details = details[:300] + "... [truncated]"
                
                with st.container():
                    st.text(f"Action {idx}: {action_type}")
                    st.code(details, language="text")
            
            st.divider()


def display_sidebar():
    """Display sidebar with settings and statistics."""
    with st.sidebar:
        st.title("⚙️ Settings")

        # Show traces toggle
        st.session_state.show_traces = st.checkbox(
            "Show Agent Traces",
            value=st.session_state.show_traces
        )

        # Show safety log toggle
        st.session_state.show_safety_log = st.checkbox(
            "Show Safety Log",
            value=st.session_state.show_safety_log
        )

        st.divider()

        st.title("📊 Statistics")

        # Get actual statistics
        st.metric("Total Queries", len(st.session_state.history))
        st.metric("Safety Events", len(st.session_state.safety_events))
        
        # Safety report
        if st.session_state.safety_manager and st.session_state.safety_events:
            with st.expander("🛡️ Safety Summary"):
                safety_report = st.session_state.safety_manager.get_safety_report()
                st.write(f"**Safe Rate:** {safety_report.get('safe_rate', 1.0):.1%}")
                st.write(f"**Blocked Inputs:** {safety_report.get('unsafe_inputs', 0)}")
                st.write(f"**Flagged Outputs:** {safety_report.get('unsafe_outputs', 0)}")

        st.divider()

        # Clear history button
        if st.button("Clear History"):
            st.session_state.history = []
            st.session_state.safety_events = []
            st.rerun()

        # About section
        st.divider()
        st.markdown("### About")
        config = load_config()
        system_name = config.get("system", {}).get("name", "Research Assistant")
        topic = config.get("system", {}).get("topic", "General")
        st.markdown(f"**System:** {system_name}")
        st.markdown(f"**Topic:** {topic}")


def display_history():
    """Display query history."""
    if not st.session_state.history:
        return

    with st.expander("📜 Query History", expanded=False):
        for i, item in enumerate(reversed(st.session_state.history), 1):
            timestamp = item.get("timestamp", "")
            query = item.get("query", "")
            st.markdown(f"**{i}.** [{timestamp}] {query}")


def main():
    """Main Streamlit app."""
    st.set_page_config(
        page_title="Multi-Agent Research Assistant",
        page_icon="🤖",
        layout="wide"
    )

    initialize_session_state()

    # Header
    st.title("🤖 Multi-Agent Research Assistant")
    st.markdown("Ask me anything about your research topic!")

    # Sidebar
    display_sidebar()

    # Create tabs
    tab1, tab2 = st.tabs(["🔍 Query System", "📊 Evaluation"])
    
    with tab1:
        display_query_tab()
    
    with tab2:
        display_evaluation_tab()


def display_query_tab():
    """Display the main query interface."""
    # Main area
    col1, col2 = st.columns([2, 1])

    with col1:
        # Query input
        query = st.text_area(
            "Enter your research query:",
            height=100,
            placeholder="e.g., What are the latest developments in explainable AI for novice users?"
        )

        # Submit button
        if st.button("🔍 Search", type="primary", use_container_width=True):
            if query.strip():
                # Show real-time status
                status_placeholder = st.empty()
                agent_status_placeholder = st.empty()
                
                with status_placeholder:
                    st.info("🔄 Multi-Agent Processing Active")
                
                try:
                    # Process query - use a new event loop to avoid conflicts
                    import nest_asyncio
                    nest_asyncio.apply()
                    result = asyncio.run(process_query(query))

                    # Clear status
                    status_placeholder.empty()
                    agent_status_placeholder.empty()
                    
                    # Show completion summary
                    st.success("✅ Processing Complete!")
                    
                    # Add to history
                    st.session_state.history.append({
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "query": query,
                        "result": result
                    })

                    # Display result
                    st.divider()
                    display_response(result)
                    
                except Exception as e:
                    status_placeholder.empty()
                    agent_status_placeholder.empty()
                    st.error(f"❌ Error: {str(e)}")
            else:
                st.warning("Please enter a query.")

        # History
        display_history()

    with col2:
        st.markdown("### 💡 Example Queries")
        examples = [
            "What are the key principles of user-centered design?",
            "Explain recent advances in AR usability research",
            "Compare different approaches to AI transparency",
            "What are ethical considerations in AI for education?",
        ]

        for example in examples:
            if st.button(example, use_container_width=True):
                st.session_state.example_query = example
                st.rerun()

        # If example was clicked, populate the text area
        if 'example_query' in st.session_state:
            st.info(f"Example query selected: {st.session_state.example_query}")
            del st.session_state.example_query

        st.divider()

        st.markdown("### ℹ️ How It Works")
        st.markdown("""
        1. **📋 Planner** breaks down your query into research steps
        2. **🔍 Researcher** gathers evidence from web + academic papers  
        3. **✍️ Writer** synthesizes findings with citations
        4. **⚖️ Critic** verifies quality and accuracy
        4. **Critic** verifies quality
        5. **Safety** checks ensure appropriate content
        """)

    # Safety log (if enabled)
    if st.session_state.show_safety_log:
        st.divider()
        st.markdown("### 🛡️ Safety Event Log")
        if st.session_state.safety_events:
            for event in st.session_state.safety_events:
                st.warning(f"[{event['timestamp']}] {event['type']}: {event.get('details', {}).get('message', 'No details')}")
        else:
            st.info("No safety events recorded.")


def display_evaluation_tab():
    """Display the evaluation interface with LLM-as-a-Judge."""
    st.markdown("### 📊 System Evaluation (LLM-as-a-Judge)")
    
    st.markdown("""
    This evaluation mode runs your system through multiple test queries and evaluates 
    the outputs using LLM-as-a-Judge with the following criteria:
    
    - **Relevance** (25%): How well the response addresses the query
    - **Evidence Quality** (25%): Quality and appropriateness of sources cited
    - **Factual Accuracy** (20%): Correctness and consistency of information
    - **Safety Compliance** (15%): Absence of harmful or inappropriate content
    - **Clarity** (15%): Readability, organization, and presentation
    """)
    
    # Load test queries
    import json
    try:
        with open("data/example_queries.json", 'r') as f:
            queries_data = json.load(f)
            # Handle both list format and dict format
            if isinstance(queries_data, list):
                # Extract just the query text from each object
                test_queries = [q.get("query", q) if isinstance(q, dict) else q for q in queries_data]
            elif isinstance(queries_data, dict):
                test_queries = queries_data.get("queries", [])
            else:
                test_queries = []
            
            # Limit to 1 query for UI display
            test_queries = test_queries[:1]
    except Exception as e:
        st.error(f"Could not load test queries: {e}")
        logger.error(f"Error loading queries: {e}", exc_info=True)
        test_queries = []
    
    st.divider()
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("#### Test Queries")
        if test_queries:
            for i, q in enumerate(test_queries, 1):
                st.markdown(f"**{i}.** {q}")
        else:
            st.warning("No test queries found in data/example_queries.json")
    
    with col2:
        st.markdown("#### Actions")
        
        if st.button("▶️ Run Evaluation", type="primary", use_container_width=True):
            if not test_queries:
                st.error("No test queries available")
            else:
                run_evaluation_async(test_queries)
        
        if st.button("📥 Download Previous Results", use_container_width=True):
            import os
            report_path = "outputs/evaluation_report.json"
            if os.path.exists(report_path):
                with open(report_path, 'r') as f:
                    report_data = f.read()
                st.download_button(
                    label="Download JSON Report",
                    data=report_data,
                    file_name="evaluation_report.json",
                    mime="application/json"
                )
            else:
                st.warning("No previous evaluation results found. Run evaluation first.")
    
    st.divider()
    
    # Display previous results if available
    st.markdown("#### Previous Evaluation Results")
    import os
    import glob
    
    # Find most recent evaluation file
    eval_files = glob.glob("outputs/evaluation_*.json")
    results = None
    
    if eval_files:
        # Try files from newest to oldest until we find a valid one
        for report_path in sorted(eval_files, key=os.path.getctime, reverse=True):
            try:
                with open(report_path, 'r') as f:
                    results = json.load(f)
                break  # Successfully loaded, exit loop
            except json.JSONDecodeError as e:
                logger.warning(f"Skipping corrupt file {report_path}: {e}")
                continue
    
    if results:
        summary = results.get('summary', {})
        scores = results.get('scores', {})
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Overall Score", f"{scores.get('overall_average', 0):.3f}")
        with col2:
            st.metric("Queries Evaluated", summary.get('total_queries', 0))
        with col3:
            st.metric("Successful", summary.get('successful', 0))
        
        # Criterion scores
        st.markdown("##### Criterion Scores")
        criterion_avgs = scores.get('by_criterion', {})
        if criterion_avgs:
            for criterion, score in criterion_avgs.items():
                st.progress(score, text=f"{criterion}: {score:.3f}")
        
        # Best and worst queries
        col1, col2 = st.columns(2)
        with col1:
            best = results.get('best_result')
            if best:
                st.success("**Best Query**")
                st.write(f"Score: {best.get('score', 0):.3f}")
                st.caption(best.get('query', '')[:100] + "...")
        
        with col2:
            worst = results.get('worst_result')
            if worst:
                st.warning("**Lowest Query**")
                st.write(f"Score: {worst.get('score', 0):.3f}")
                st.caption(worst.get('query', '')[:100] + "...")
        
        # Download results as markdown
        if st.button("📥 Download as Markdown Report"):
            markdown_report = generate_evaluation_markdown(results)
            st.download_button(
                label="Download Markdown",
                data=markdown_report,
                file_name=f"evaluation_report_{datetime.now().strftime('%Y%m%d')}.md",
                mime="text/markdown"
            )
    else:
        st.info("No evaluation results yet. Click 'Run Evaluation' to start.")


def run_evaluation_async(test_queries):
    """Run evaluation on test queries."""
    from src.evaluation.evaluator import SystemEvaluator
    
    config = load_config()
    
    with st.spinner("Running evaluation... This may take several minutes."):
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            # Pass the orchestrator to the evaluator
            orchestrator = st.session_state.orchestrator
            evaluator = SystemEvaluator(config, orchestrator=orchestrator)
            
            # Run evaluation - use default file path, not the list
            status_text.text("Initializing evaluator...")
            results = asyncio.run(evaluator.evaluate_system("data/example_queries.json"))
            
            progress_bar.progress(100)
            status_text.text("Evaluation complete!")
            
            overall_score = results.get('scores', {}).get('overall_average', 0.0)
            st.success(f"✅ Evaluation completed! Overall score: {overall_score:.3f}")
            st.info("Results saved to outputs/ directory")
            
            # Rerun to display results
            st.rerun()
            
        except Exception as e:
            st.error(f"Evaluation failed: {str(e)}")
            logger.error(f"Evaluation error: {e}", exc_info=True)


def generate_evaluation_markdown(results: Dict[str, Any]) -> str:
    """Generate markdown report from evaluation results."""
    summary = results.get('summary', {})
    scores = results.get('scores', {})
    
    report = f"""# System Evaluation Report

**Generated:** {results.get('timestamp', datetime.now().isoformat())}

## Overall Results

- **Overall Score:** {scores.get('overall_average', 0):.3f}
- **Total Queries:** {summary.get('total_queries', 0)}
- **Successful:** {summary.get('successful', 0)}
- **Failed:** {summary.get('failed', 0)}

## Criterion Scores

"""
    for criterion, score in results.get('criterion_averages', {}).items():
        report += f"- **{criterion}:** {score:.3f}\n"
    
    if results.get('best_query'):
        report += f"""
## Best Performing Query

**Score:** {results['best_query']['score']:.3f}

**Query:** {results['best_query']['query']}

"""
    
    if results.get('worst_query'):
        report += f"""
## Lowest Performing Query

**Score:** {results['worst_query']['score']:.3f}

**Query:** {results['worst_query']['query']}

"""
    
    report += """
## Per-Query Details

See the full JSON report for detailed per-query evaluations and criterion-level scores.
"""
    
    return report


if __name__ == "__main__":
    main()
