"""
Safety Manager
Coordinates safety guardrails and logs safety events.
"""

from typing import Dict, Any, List, Optional
import logging
from datetime import datetime
import json
import re
from pathlib import Path


class SafetyManager:
    """
    Manages safety guardrails for the multi-agent system.
    
    Implements custom policy filter with:
    - Input validation (unsafe queries, prompt injection attempts)
    - Output validation (harmful content, data leaks, quality issues)
    - Safety event logging with detailed context
    - Multiple response strategies (refuse, sanitize, redirect)
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize safety manager with custom policy filters.

        Args:
            config: Safety configuration
        """
        self.config = config
        self.enabled = config.get("enabled", True)
        self.log_events = config.get("log_events", True)
        self.logger = logging.getLogger("safety")

        # Safety event log
        self.safety_events: List[Dict[str, Any]] = []

        # Prohibited categories with detailed definitions
        self.prohibited_categories = config.get("prohibited_categories", [
            "harmful_content",
            "personal_attacks",
            "misinformation",
            "off_topic_queries"
        ])

        # Violation response strategy
        self.on_violation = config.get("on_violation", {})
        
        # Initialize custom policy filters
        self._initialize_policy_filters()
        
        # Setup safety event logging
        self._setup_logging()
        
        self.logger.info(f"SafetyManager initialized (enabled={self.enabled})")
    
    def _initialize_policy_filters(self):
        """Initialize custom policy filters for input and output validation."""
        
        # Input filters: Detect harmful, off-topic, or malicious queries
        self.input_filters = {
            "harmful_content": {
                "patterns": [
                    r"\b(hack|exploit|bypass|crack|malware|virus|attack)\b",
                    r"\b(bomb|weapon|explosive|poison|drug)\b",
                    r"\b(kill|harm|hurt|damage|destroy)\s+(people|person|human|user)",
                ],
                "severity": "high",
                "action": "refuse",
                "message": "This query contains potentially harmful content that violates our safety policies."
            },
            "prompt_injection": {
                "patterns": [
                    r"ignore\s+(previous|all|above)\s+(instructions|prompts|rules)",
                    r"disregard\s+(your|all)\s+(instructions|rules|guidelines)",
                    r"you\s+are\s+now\s+(a|an)\s+\w+",
                    r"forget\s+(everything|all|previous)",
                    r"system\s*:\s*\w+",
                ],
                "severity": "high",
                "action": "refuse",
                "message": "This appears to be a prompt injection attempt and cannot be processed."
            },
            "personal_attacks": {
                "patterns": [
                    r"\b(stupid|idiot|moron|dumb|incompetent)\b",
                    r"\b(hate|despise|loathe)\s+(you|this|that)\b",
                ],
                "severity": "medium",
                "action": "refuse",
                "message": "This query contains personal attacks or offensive language."
            },
            "off_topic": {
                "patterns": [
                    r"\b(recipe|cooking|baking)\s+(for|instructions|how\s+to)\b",
                    r"\b(weather|temperature|forecast)\s+(today|tomorrow|in)\b",
                    r"\b(sports\s+score|game\s+result|who\s+won)\b",
                    r"\b(lottery\s+numbers|winning\s+numbers)\b",
                    r"\b(stock\s+price|share\s+price|cryptocurrency\s+value)\b",
                    r"\b(dating\s+advice|relationship\s+tips|how\s+to\s+date)\b",
                    r"\b(medical\s+diagnosis|health\s+symptoms|am\s+I\s+sick)\b"
                ],
                "severity": "low",
                "action": "redirect",
                "message": "This query appears to be off-topic. This system specializes in HCI and agentic UX research. Please ask questions related to user experience, AI agents, or human-computer interaction."
            },
            "data_extraction": {
                "patterns": [
                    r"show\s+me\s+(your|the)\s+(api|key|password|token|secret)",
                    r"what\s+is\s+(your|the)\s+(system|internal|database)",
                    r"reveal\s+(your|the)\s+\w+",
                ],
                "severity": "high",
                "action": "refuse",
                "message": "This query attempts to extract system information and is not allowed."
            }
        }
        
        # Output filters: Detect harmful, low-quality, or inappropriate outputs
        self.output_filters = {
            "harmful_instructions": {
                "patterns": [
                    r"how\s+to\s+(hack|exploit|bypass|crack|steal|cheat)",
                    r"steps\s+to\s+(harm|hurt|damage|attack)",
                ],
                "severity": "high",
                "action": "redact",
                "replacement": "[CONTENT REMOVED: Potentially harmful instructions]"
            },
            "personal_data": {
                "patterns": [
                    r"\b\d{3}-\d{2}-\d{4}\b",  # SSN
                    r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",  # Email
                    r"\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b",  # Credit card
                ],
                "severity": "high",
                "action": "redact",
                "replacement": "[REDACTED: Personal Information]"
            },
            "low_quality": {
                "checks": [
                    {"type": "length", "min": 50, "message": "Response is too short (less than 50 characters)"},
                    {"type": "no_sources", "pattern": r"(http|www|\.com|\.org|\.edu)", "message": "Response contains no citations or sources"},
                ],
                "severity": "medium",
                "action": "flag",
            },
            "hallucination_markers": {
                "patterns": [
                    r"I (don't|do not|cannot) (know|have access|remember)",
                    r"as an AI (language model|assistant)",
                    r"I (apologize|sorry),?\s+(but )?I (can't|cannot|am unable)",
                ],
                "severity": "low",
                "action": "flag",
            }
        }
    
    def _setup_logging(self):
        """Setup safety event logging to file."""
        if self.log_events:
            log_dir = Path("logs")
            log_dir.mkdir(exist_ok=True)
            
            # Create file handler for safety events
            safety_log_path = log_dir / "safety_events.log"
            file_handler = logging.FileHandler(safety_log_path)
            file_handler.setLevel(logging.INFO)
            
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            file_handler.setFormatter(formatter)
            
            self.logger.addHandler(file_handler)

    def check_input_safety(self, query: str) -> Dict[str, Any]:
        """
        Check if input query is safe to process using custom policy filters.

        Args:
            query: User query to check

        Returns:
            Dictionary with:
            - safe: bool - Whether query is safe
            - violations: list - List of detected violations
            - action: str - Recommended action (refuse/redirect/allow)
            - message: str - Message to display to user
            - sanitized_query: str - Modified query if applicable
        """
        if not self.enabled:
            return {"safe": True, "action": "allow"}

        violations = []
        highest_severity = "low"
        recommended_action = "allow"
        user_message = None
        
        # Check each input filter
        for category, filter_config in self.input_filters.items():
            violation = self._check_filter(query, category, filter_config, "input")
            
            if violation:
                violations.append(violation)
                
                # Track highest severity
                if self._severity_level(violation["severity"]) > self._severity_level(highest_severity):
                    highest_severity = violation["severity"]
                    recommended_action = violation["action"]
                    user_message = violation["message"]

        is_safe = len(violations) == 0

        # Log safety event
        if not is_safe and self.log_events:
            self._log_safety_event("input", query, violations, is_safe)

        result = {
            "safe": is_safe,
            "violations": violations,
            "action": recommended_action,
            "sanitized_query": query  # For now, no sanitization
        }
        
        if user_message:
            result["message"] = user_message
        
        return result

    def check_output_safety(self, response: str) -> Dict[str, Any]:
        """
        Check if output response is safe to return using custom policy filters.

        Args:
            response: Generated response to check

        Returns:
            Dictionary with:
            - safe: bool - Whether response is safe
            - response: str - Original or sanitized response
            - violations: list - List of detected issues
            - action_taken: str - What action was performed
            - warnings: list - Non-blocking issues flagged
        """
        if not self.enabled:
            return {"safe": True, "response": response, "violations": [], "warnings": []}
        
        violations = []
        warnings = []
        sanitized_response = response
        action_taken = "none"
        
        # Check each output filter
        for category, filter_config in self.output_filters.items():
            violation = self._check_filter(response, category, filter_config, "output")
            
            if violation:
                if violation["action"] == "redact":
                    # Redact problematic content
                    for pattern in filter_config.get("patterns", []):
                        sanitized_response = re.sub(
                            pattern,
                            filter_config.get("replacement", "[REDACTED]"),
                            sanitized_response,
                            flags=re.IGNORECASE
                        )
                    violations.append(violation)
                    action_taken = "redacted"
                    
                elif violation["action"] == "flag":
                    # Flag but don't block
                    warnings.append(violation)
                    
                else:
                    # Block entirely
                    violations.append(violation)
        
        # Determine if response should be blocked
        high_severity_violations = [v for v in violations if v["severity"] == "high"]
        is_safe = len(high_severity_violations) == 0
        
        # Log safety event
        if (violations or warnings) and self.log_events:
            self._log_safety_event("output", response[:200], violations + warnings, is_safe)
        
        return {
            "safe": is_safe,
            "response": sanitized_response if is_safe else None,
            "violations": violations,
            "warnings": warnings,
            "action_taken": action_taken
        }
    
    def _check_filter(
        self,
        content: str,
        category: str,
        filter_config: Dict[str, Any],
        check_type: str
    ) -> Optional[Dict[str, Any]]:
        """
        Check content against a specific filter.
        
        Args:
            content: Content to check
            category: Filter category name
            filter_config: Filter configuration
            check_type: "input" or "output"
            
        Returns:
            Violation dictionary if found, None otherwise
        """
        # Check regex patterns
        for pattern in filter_config.get("patterns", []):
            if re.search(pattern, content, re.IGNORECASE):
                return {
                    "category": category,
                    "severity": filter_config.get("severity", "medium"),
                    "action": filter_config.get("action", "refuse"),
                    "message": filter_config.get("message", f"Content violates {category} policy"),
                    "matched_pattern": pattern,
                    "type": check_type
                }
        
        # Check keywords (for off-topic detection)
        for keyword in filter_config.get("keywords", []):
            if keyword.lower() in content.lower():
                return {
                    "category": category,
                    "severity": filter_config.get("severity", "low"),
                    "action": filter_config.get("action", "redirect"),
                    "message": filter_config.get("message", f"Content matches {category}"),
                    "matched_keyword": keyword,
                    "type": check_type
                }
        
        # Check quality checks (for output)
        for check in filter_config.get("checks", []):
            if check["type"] == "length":
                if len(content) < check.get("min", 0):
                    return {
                        "category": category,
                        "severity": filter_config.get("severity", "medium"),
                        "action": filter_config.get("action", "flag"),
                        "message": check.get("message", "Content quality issue"),
                        "type": check_type
                    }
            elif check["type"] == "no_sources":
                if not re.search(check.get("pattern", ""), content, re.IGNORECASE):
                    return {
                        "category": category,
                        "severity": filter_config.get("severity", "medium"),
                        "action": filter_config.get("action", "flag"),
                        "message": check.get("message", "No sources found"),
                        "type": check_type
                    }
        
        return None
    
    def _severity_level(self, severity: str) -> int:
        """Convert severity string to numeric level for comparison."""
        levels = {"low": 1, "medium": 2, "high": 3}
        return levels.get(severity, 0)

    def _log_safety_event(
        self,
        event_type: str,
        content: str,
        violations: List[Dict[str, Any]],
        is_safe: bool
    ):
        """
        Log a safety event with detailed context.

        Args:
            event_type: Type of event ("input" or "output")
            content: Content that was checked
            violations: List of violations detected
            is_safe: Whether content was deemed safe
        """
        event = {
            "timestamp": datetime.now().isoformat(),
            "type": event_type,
            "content_preview": content[:100] + "..." if len(content) > 100 else content,
            "is_safe": is_safe,
            "violations": violations,
            "num_violations": len(violations),
            "categories": [v["category"] for v in violations],
            "highest_severity": max([v["severity"] for v in violations], default="none")
        }

        self.safety_events.append(event)

        # Log to file with detailed information
        if self.log_events:
            log_level = logging.ERROR if not is_safe else logging.WARNING
            
            violation_summary = ", ".join([
                f"{v['category']}({v['severity']})" for v in violations
            ])
            
            self.logger.log(
                log_level,
                f"Safety event: {event_type} - Safe: {is_safe} - "
                f"Violations: [{violation_summary}] - "
                f"Content preview: {event['content_preview']}"
            )

    def get_safety_report(self) -> Dict[str, Any]:
        """
        Generate comprehensive safety report from logged events.

        Returns:
            Dictionary with statistics, breakdown by category, and event log
        """
        total_events = len(self.safety_events)
        unsafe_inputs = sum(
            1 for e in self.safety_events
            if e["type"] == "input" and not e["is_safe"]
        )
        unsafe_outputs = sum(
            1 for e in self.safety_events
            if e["type"] == "output" and not e["is_safe"]
        )
        
        # Category breakdown
        category_counts = {}
        for event in self.safety_events:
            for violation in event.get("violations", []):
                category = violation.get("category", "unknown")
                category_counts[category] = category_counts.get(category, 0) + 1
        
        # Severity breakdown
        severity_counts = {"low": 0, "medium": 0, "high": 0}
        for event in self.safety_events:
            severity = event.get("highest_severity", "none")
            if severity in severity_counts:
                severity_counts[severity] += 1

        return {
            "total_events": total_events,
            "unsafe_inputs": unsafe_inputs,
            "unsafe_outputs": unsafe_outputs,
            "safe_rate": (total_events - unsafe_inputs - unsafe_outputs) / total_events if total_events > 0 else 1.0,
            "category_breakdown": category_counts,
            "severity_breakdown": severity_counts,
            "recent_events": self.safety_events[-10:],  # Last 10 events
            "all_events": self.safety_events
        }
    
    def get_policy_documentation(self) -> Dict[str, Any]:
        """
        Get documentation of all safety policies for reporting.
        
        Returns:
            Dictionary with policy descriptions and response strategies
        """
        return {
            "input_policies": {
                category: {
                    "description": self._get_policy_description(category),
                    "severity": config.get("severity"),
                    "action": config.get("action"),
                    "example_patterns": config.get("patterns", [])[:2] if "patterns" in config else config.get("keywords", [])[:3]
                }
                for category, config in self.input_filters.items()
            },
            "output_policies": {
                category: {
                    "description": self._get_policy_description(category),
                    "severity": config.get("severity"),
                    "action": config.get("action")
                }
                for category, config in self.output_filters.items()
            },
            "response_strategies": {
                "refuse": "Block the request entirely and return an error message",
                "redirect": "Suggest an alternative approach or clarify the system's capabilities",
                "redact": "Remove or mask problematic content while allowing the response",
                "flag": "Allow the content but log a warning for review"
            }
        }
    
    def _get_policy_description(self, category: str) -> str:
        """Get human-readable description of a policy category."""
        descriptions = {
            "harmful_content": "Detects queries or responses containing harmful keywords related to violence, weapons, or malicious activities",
            "prompt_injection": "Identifies attempts to manipulate the system through prompt injection techniques",
            "personal_attacks": "Filters offensive language and personal attacks",
            "off_topic": "Detects queries outside the system's domain expertise (HCI, UX, agentic design)",
            "data_extraction": "Prevents attempts to extract system credentials or internal information",
            "harmful_instructions": "Blocks output containing step-by-step harmful instructions",
            "personal_data": "Redacts personal identifiable information (PII) like SSN, emails, credit cards",
            "low_quality": "Flags responses that are too short or lack proper citations",
            "hallucination_markers": "Detects phrases indicating the model's uncertainty or limitations"
        }
        return descriptions.get(category, f"Policy for {category}")
