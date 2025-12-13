"""
Output Guardrail
Checks system outputs for safety violations using the SafetyManager.
"""

from typing import Dict, Any, List
from .safety_manager import SafetyManager


class OutputGuardrail:
    """
    Guardrail for checking output safety.
    
    Uses the SafetyManager's custom policy filters to validate system responses.
    This is a wrapper that provides a simpler interface for output validation.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize output guardrail with SafetyManager.

        Args:
            config: Configuration dictionary
        """
        self.config = config
        
        # Use SafetyManager for policy-based filtering
        self.safety_manager = SafetyManager(config)

    def validate(self, response: str, sources: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Validate output response using SafetyManager's policy filters.

        Args:
            response: Generated response to validate
            sources: Optional list of sources used (for reference checking)

        Returns:
            Validation result with:
            - valid: bool - Whether output passes all checks
            - violations: list - List of policy violations detected
            - warnings: list - Non-blocking issues flagged
            - sanitized_output: str - Original or sanitized response
            - action_taken: str - What action was performed (none/redacted/blocked)
        """
        # Basic validation checks
        if not response or len(response.strip()) == 0:
            return {
                "valid": False,
                "violations": [{
                    "validator": "empty_response",
                    "category": "output_format",
                    "reason": "Response is empty",
                    "severity": "high",
                    "action": "refuse"
                }],
                "warnings": [],
                "sanitized_output": None,
                "action_taken": "blocked"
            }
        
        # Use SafetyManager for comprehensive output checking
        safety_result = self.safety_manager.check_output_safety(response)
        
        # Check if sources were provided and used
        warnings = safety_result.get("warnings", [])
        if sources is None or len(sources) == 0:
            warnings.append({
                "validator": "citation_check",
                "category": "quality",
                "reason": "No sources provided for verification",
                "severity": "low",
                "action": "flag"
            })
        
        # Convert to validation format
        return {
            "valid": safety_result["safe"],
            "violations": safety_result.get("violations", []),
            "warnings": warnings,
            "sanitized_output": safety_result.get("response", response),
            "action_taken": safety_result.get("action_taken", "none")
        }
    
    def get_sanitization_report(self, original: str, sanitized: str) -> Dict[str, Any]:
        """
        Generate a report of what was sanitized.
        
        Args:
            original: Original response
            sanitized: Sanitized response
            
        Returns:
            Report dictionary with changes made
        """
        changes = []
        
        if original != sanitized:
            changes.append({
                "type": "content_redacted",
                "original_length": len(original),
                "sanitized_length": len(sanitized),
                "chars_removed": len(original) - len(sanitized)
            })
        
        return {
            "sanitized": original != sanitized,
            "changes": changes,
            "original_preview": original[:100] + "..." if len(original) > 100 else original,
            "sanitized_preview": sanitized[:100] + "..." if len(sanitized) > 100 else sanitized
        }
