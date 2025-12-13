"""
Input Guardrail
Checks user inputs for safety violations using the SafetyManager.
"""

from typing import Dict, Any, List
from .safety_manager import SafetyManager


class InputGuardrail:
    """
    Guardrail for checking input safety.
    
    Uses the SafetyManager's custom policy filters to validate user inputs.
    This is a wrapper that provides a simpler interface.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize input guardrail with SafetyManager.

        Args:
            config: Configuration dictionary
        """
        self.config = config
        
        # Use SafetyManager for policy-based filtering
        self.safety_manager = SafetyManager(config)

    def validate(self, query: str) -> Dict[str, Any]:
        """
        Validate input query using SafetyManager's policy filters.

        Args:
            query: User input to validate

        Returns:
            Validation result with:
            - valid: bool - Whether input passes all checks
            - violations: list - List of policy violations detected
            - action: str - Recommended action (refuse/redirect/allow)
            - message: str - User-facing message if validation fails
            - sanitized_input: str - Original or modified query
        """
        # Basic validation checks
        violations = []
        
        # Length validation
        if len(query.strip()) < 5:
            violations.append({
                "validator": "length",
                "category": "input_format",
                "reason": "Query too short (minimum 5 characters)",
                "severity": "low",
                "action": "refuse"
            })
        
        if len(query) > 2000:
            violations.append({
                "validator": "length",
                "category": "input_format",
                "reason": "Query too long (maximum 2000 characters)",
                "severity": "medium",
                "action": "refuse"
            })
        
        # If basic validation fails, return early
        if violations:
            return {
                "valid": False,
                "violations": violations,
                "action": "refuse",
                "message": violations[0]["reason"],
                "sanitized_input": query
            }
        
        # Use SafetyManager for comprehensive policy checking
        safety_result = self.safety_manager.check_input_safety(query)
        
        # Convert to validation format
        return {
            "valid": safety_result["safe"],
            "violations": safety_result.get("violations", []),
            "action": safety_result.get("action", "allow"),
            "message": safety_result.get("message", ""),
            "sanitized_input": safety_result.get("sanitized_query", query)
        }
        # Check for common prompt injection patterns
        injection_patterns = [
            "ignore previous instructions",
            "disregard",
            "forget everything",
            "system:",
            "sudo",
        ]

        for pattern in injection_patterns:
            if pattern.lower() in text.lower():
                violations.append({
                    "validator": "prompt_injection",
                    "reason": f"Potential prompt injection: {pattern}",
                    "severity": "high"
                })

        return violations

    def _check_relevance(self, query: str) -> List[Dict[str, Any]]:
        """
        Check if query is relevant to the system's purpose.

        TODO: YOUR CODE HERE Implement relevance checking
        """
        violations = []
        # Check if query is about HCI research (or configured topic)
        return violations
