"""
Command Line Interface
Interactive CLI for the multi-agent research system.
"""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import asyncio
from typing import Dict, Any
import yaml
import logging
from dotenv import load_dotenv

from src.autogen_orchestrator import AutoGenOrchestrator
from src.guardrails.safety_manager import SafetyManager

# Load environment variables
load_dotenv()

class CLI:
    """
    Command-line interface for the research assistant.
    
    Features:
    - Interactive query processing
    - Agent trace display
    - Citation and source display
    - Safety event notifications
    - System statistics
    """

    def __init__(self, config_path: str = "config.yaml"):
        """
        Initialize CLI with orchestrator and safety manager.

        Args:
            config_path: Path to configuration file
        """
        # Load configuration
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)

        # Setup logging
        self._setup_logging()

        # Initialize AutoGen orchestrator
        try:
            self.orchestrator = AutoGenOrchestrator(self.config)
            self.logger = logging.getLogger("cli")
            self.logger.info("AutoGen orchestrator initialized successfully")
        except Exception as e:
            self.logger = logging.getLogger("cli")
            self.logger.error(f"Failed to initialize orchestrator: {e}")
            raise

        # Initialize safety manager for displaying safety events
        self.safety_manager = SafetyManager(self.config.get("safety", {}))

        self.running = True
        self.query_count = 0
        self.safety_events_count = 0

    def _setup_logging(self):
        """Setup logging configuration."""
        log_config = self.config.get("logging", {})
        log_level = log_config.get("level", "INFO")
        log_format = log_config.get(
            "format",
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

        logging.basicConfig(
            level=getattr(logging, log_level),
            format=log_format
        )

    async def run(self):
        """
        Main CLI loop.

        TODO: YOUR CODE HERE
        - Implement interactive loop
        - Handle user input
        - Process queries through orchestrator
        - Display results
        - Handle errors gracefully
        """
        self._print_welcome()

        while self.running:
            try:
                # Get user input
                query = input("\nEnter your research query (or 'help' for commands): ").strip()

                if not query:
                    continue

                # Handle commands
                if query.lower() in ['quit', 'exit', 'q']:
                    self._print_goodbye()
                    break
                elif query.lower() == 'help':
                    self._print_help()
                    continue
                elif query.lower() == 'clear':
                    self._clear_screen()
                    continue
                elif query.lower() == 'stats':
                    self._print_stats()
                    continue
                elif query.lower() == 'safety':
                    self._print_safety_report()
                    continue

                # Check input safety before processing
                safety_check = self.safety_manager.check_input_safety(query)
                
                if not safety_check["safe"]:
                    self._display_safety_violation(safety_check)
                    self.safety_events_count += 1
                    continue

                # Process query
                print("\n" + "=" * 70)
                print("Processing your query...")
                print("=" * 70)
                
                try:
                    # Process through orchestrator (synchronous call, not async)
                    result = self.orchestrator.process_query(query)
                    self.query_count += 1
                    
                    # Check output safety
                    response = result.get("response", "")
                    output_safety = self.safety_manager.check_output_safety(response)
                    
                    if not output_safety["safe"]:
                        result["safety_warning"] = True
                        result["safety_details"] = output_safety
                        self.safety_events_count += 1
                    elif output_safety.get("warnings"):
                        result["safety_warnings"] = output_safety["warnings"]
                    
                    # Display result
                    self._display_result(result)
                    
                except Exception as e:
                    print(f"\nError processing query: {e}")
                    logging.exception("Error processing query")

            except KeyboardInterrupt:
                print("\n\nInterrupted by user.")
                self._print_goodbye()
                break
            except Exception as e:
                print(f"\nError: {e}")
                logging.exception("Error in CLI loop")

    def _print_welcome(self):
        """Print welcome message."""
        print("=" * 70)
        print(f"  {self.config['system']['name']}")
        print(f"  Topic: {self.config['system']['topic']}")
        print("=" * 70)
        print("\nWelcome! Ask me anything about your research topic.")
        print("Type 'help' for available commands, or 'quit' to exit.\n")

    def _print_help(self):
        """Print help message."""
        print("\nAvailable commands:")
        print("  help    - Show this help message")
        print("  clear   - Clear the screen")
        print("  stats   - Show system statistics")
        print("  safety  - Show safety event summary")
        print("  quit    - Exit the application")
        print("\nOr enter a research query to get started!")

    def _print_goodbye(self):
        """Print goodbye message."""
        print("\nThank you for using the Multi-Agent Research Assistant!")
        print("Goodbye!\n")

    def _clear_screen(self):
        """Clear the terminal screen."""
        import os
        os.system('clear' if os.name == 'posix' else 'cls')
    def _print_stats(self):
        """Print system statistics."""
        print("\nSystem Statistics:")
        print(f"  Queries processed: {self.query_count}")
        print(f"  Safety events: {self.safety_events_count}")
        print(f"  System: {self.config.get('system', {}).get('name', 'Unknown')}")
        print(f"  Topic: {self.config.get('system', {}).get('topic', 'Unknown')}")
        print(f"  Model: {self.config.get('models', {}).get('default', {}).get('name', 'Unknown')}")
    def _display_result(self, result: Dict[str, Any]):
        """Display query result with formatting."""
        print("\n" + "=" * 70)
        print("RESPONSE")
        print("=" * 70)

        # Check for errors
        if "error" in result:
            print(f"\n❌ Error: {result['error']}")
            return

        # Display safety warning if present
        if result.get("safety_warning"):
            print("\n⚠️  WARNING: Safety issues detected in response")
            safety_details = result.get("safety_details", {})
            if safety_details.get("action_taken") == "redacted":
                print("   Some content has been redacted for safety.")
            print()

        # Display response
        response = result.get("response", "")
        if response:
            print(f"\n{response}\n")
        else:
            print("\n❌ Response was blocked due to safety concerns.\n")
            return
        
        # Display safety warnings (non-blocking issues)
        if result.get("safety_warnings"):
            print("\n" + "-" * 70)
            print("ℹ️  SAFETY NOTES")
            print("-" * 70)
            for warning in result["safety_warnings"]:
                print(f"  • {warning.get('message', 'Quality issue detected')}")breakdown'):
            print("\nViolations by category:")
            for category, count in report['category_breakdown'].items():
                print(f"  • {category}: {count}")
        
        if report.get('severity_breakdown'):
            print("\nViolations by severity:")
            for severity, count in report['severity_breakdown'].items():
                if count > 0:
                    print(f"  • {severity}: {count}")
        
        print("=" * 70)
    
    def _display_safety_violation(self, safety_check: Dict[str, Any]):
        """Display safety violation message."""
        print("\n" + "=" * 70)
        print("🛡️  SAFETY VIOLATION DETECTED")
        print("=" * 70)
        
        message = safety_check.get("message", "This query violates safety policies.")
        print(f"\n❌ {message}\n")
        
        violations = safety_check.get("violations", [])
        if violations:
            print("Details:")
            for v in violations:
                category = v.get("category", "unknown")
                severity = v.get("severity", "unknown")
                reason = v.get("message", "Unknown reason")
                print(f"  • [{severity.upper()}] {category}: {reason}")
        
        print("\nPlease rephrase your query and try again.")
        print("=" * 70)
        print(f"  Model: {self.config.get('models', {}).get('default', {}).get('name', 'Unknown')}")

    def _display_result(self, result: Dict[str, Any]):
        """Display query result with formatting."""
        print("\n" + "=" * 70)
        print("RESPONSE")
        print("=" * 70)

        # Check for errors
        if "error" in result:
            print(f"\n❌ Error: {result['error']}")
            return

        # Display response
        response = result.get("response", "")
        print(f"\n{response}\n")

        # Extract and display citations from conversation
        citations = self._extract_citations(result)
        if citations:
            print("\n" + "-" * 70)
            print("📚 CITATIONS")
            print("-" * 70)
            for i, citation in enumerate(citations, 1):
                print(f"[{i}] {citation}")

        # Display metadata
        metadata = result.get("metadata", {})
        if metadata:
            print("\n" + "-" * 70)
            print("📊 METADATA")
            print("-" * 70)
            print(f"  • Messages exchanged: {metadata.get('num_messages', 0)}")
            print(f"  • Sources gathered: {metadata.get('num_sources', 0)}")
            print(f"  • Agents involved: {', '.join(metadata.get('agents_involved', []))}")

        # Display conversation summary if verbose mode
        if self._should_show_traces():
            self._display_conversation_summary(result.get("conversation_history", []))

        print("=" * 70 + "\n")
    
    def _extract_citations(self, result: Dict[str, Any]) -> list:
        """Extract citations/URLs from conversation history."""
        citations = []
        
        for msg in result.get("conversation_history", []):
            content = msg.get("content", "")
            
            # Find URLs in content
            import re
            urls = re.findall(r'https?://[^\s<>"{}|\\^`\[\]]+', content)
            
            for url in urls:
                if url not in citations:
                    citations.append(url)
        
        return citations[:10]  # Limit to top 10

    def _should_show_traces(self) -> bool:
        """Check if agent traces should be displayed."""
        # Check config for verbose mode
        return self.config.get("ui", {}).get("verbose", False)

    def _display_conversation_summary(self, conversation_history: list):
        """Display a summary of the agent conversation."""
        if not conversation_history:
            return
            
        print("\n" + "-" * 70)
        print("🔍 CONVERSATION SUMMARY")
        print("-" * 70)
        
        for i, msg in enumerate(conversation_history, 1):
            agent = msg.get("source", "Unknown")
            content = msg.get("content", "")
            
            # Truncate long content
            preview = content[:150] + "..." if len(content) > 150 else content
            preview = preview.replace("\n", " ")
            
            print(f"\n{i}. {agent}:")
            print(f"   {preview}")


def main():
    """Main entry point for CLI."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Multi-Agent Research Assistant CLI"
    )
    parser.add_argument(
        "--config",
        default="config.yaml",
        help="Path to configuration file"
    )

    args = parser.parse_args()

    # Run CLI
    cli = CLI(config_path=args.config)
    asyncio.run(cli.run())


if __name__ == "__main__":
    main()
