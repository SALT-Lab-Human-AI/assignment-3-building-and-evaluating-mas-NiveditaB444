"""
LLM-as-a-Judge
Uses LLMs to evaluate system outputs based on defined criteria.

Example usage:
    # Initialize judge with config
    judge = LLMJudge(config)
    
    # Evaluate a response
    result = await judge.evaluate(
        query="What is the capital of France?",
        response="Paris is the capital of France.",
        sources=[],
        ground_truth="Paris"
    )
    
    print(f"Overall Score: {result['overall_score']}")
    print(f"Criterion Scores: {result['criterion_scores']}")
"""

from typing import Dict, Any, List, Optional
import logging
import json
import os
from openai import OpenAI


class LLMJudge:
    """
    LLM-based judge for evaluating system responses.
    
    Implements comprehensive evaluation using LLM-as-a-Judge methodology:
    - Multiple evaluation criteria with weighted scoring
    - Detailed reasoning for each judgment
    - Structured JSON output parsing
    - Support for ground truth comparison
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize LLM judge.

        Args:
            config: Configuration dictionary (from config.yaml)
        """
        self.config = config
        self.logger = logging.getLogger("evaluation.judge")

        # Load judge model configuration from config.yaml (models.judge)
        # This includes: provider, name, temperature, max_tokens
        self.model_config = config.get("models", {}).get("judge", {})

        # Load evaluation criteria from config.yaml (evaluation.criteria)
        # Each criterion has: name, weight, description
        self.criteria = config.get("evaluation", {}).get("criteria", [])
        
        # Initialize OpenAI client with increased timeout
        api_key = os.getenv("OPENAI_API_KEY")
        base_url = os.getenv("OPENAI_BASE_URL")
        
        if not api_key:
            self.logger.warning("OPENAI_API_KEY not found in environment")
            self.client = None
        else:
            self.client = OpenAI(
                api_key=api_key, 
                base_url=base_url,
                timeout=120.0  # Increase timeout to 120 seconds
            ) if base_url else OpenAI(api_key=api_key, timeout=120.0)
        
        self.logger.info(f"LLMJudge initialized with {len(self.criteria)} criteria")
 
    async def evaluate(
        self,
        query: str,
        response: str,
        sources: Optional[List[Dict[str, Any]]] = None,
        ground_truth: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Evaluate a response using LLM-as-a-Judge.

        Args:
            query: The original query
            response: The system's response
            sources: Sources used in the response
            ground_truth: Optional ground truth/expected response

        Returns:
            Dictionary with scores for each criterion and overall score

        TODO: YOUR CODE HERE
        - Implement LLM API calls
        - Call judge for each criterion
        - Parse and aggregate scores
        - Provide detailed feedback
        """
        self.logger.info(f"Evaluating response for query: {query[:50]}...")

        results = {
            "query": query,
            "overall_score": 0.0,
            "criterion_scores": {},
            "feedback": [],
        }

        total_weight = sum(c.get("weight", 1.0) for c in self.criteria)
        weighted_score = 0.0

        # Evaluate each criterion
        for criterion in self.criteria:
            criterion_name = criterion.get("name", "unknown")
            weight = criterion.get("weight", 1.0)

            self.logger.info(f"Evaluating criterion: {criterion_name}")

            # TODO: Implement actual LLM judging
            score = await self._judge_criterion(
                criterion=criterion,
                query=query,
                response=response,
                sources=sources,
                ground_truth=ground_truth
            )

            results["criterion_scores"][criterion_name] = score
            weighted_score += score.get("score", 0.0) * weight

        # Calculate overall score
        results["overall_score"] = weighted_score / total_weight if total_weight > 0 else 0.0

        return results

    async def _judge_criterion(
        self,
        criterion: Dict[str, Any],
        query: str,
        response: str,
        sources: Optional[List[Dict[str, Any]]],
        ground_truth: Optional[str]
    ) -> Dict[str, Any]:
        """
        Judge a single criterion.

        Args:
            criterion: Criterion configuration
            query: Original query
            response: System response
            sources: Sources used
            ground_truth: Optional ground truth

        Returns:
            Score and feedback for this criterion

        This is a basic implementation using Groq API.
        """
        criterion_name = criterion.get("name", "unknown")
        description = criterion.get("description", "")

        # Create judge prompt
        prompt = self._create_judge_prompt(
            criterion_name=criterion_name,
            description=description,
            query=query,
            response=response,
            sources=sources,
            ground_truth=ground_truth
        )

        # Call LLM API to get judgment
        try:
            judgment = await self._call_judge_llm(prompt)
            score_value, reasoning = self._parse_judgment(judgment)
            
            score = {
                "score": score_value,  # 0-1 scale
                "reasoning": reasoning,
                "criterion": criterion_name
            }
        except Exception as e:
            self.logger.error(f"Error judging criterion {criterion_name}: {e}")
            score = {
                "score": 0.0,
                "reasoning": f"Error during evaluation: {str(e)}",
                "criterion": criterion_name
            }

        return score

    def _create_judge_prompt(
        self,
        criterion_name: str,
        description: str,
        query: str,
        response: str,
        sources: Optional[List[Dict[str, Any]]],
        ground_truth: Optional[str]
    ) -> str:
        """
        Create a comprehensive prompt for the judge LLM.
        
        Includes scoring rubric, context, and structured output format.
        """
        # Create criterion-specific rubric
        rubric = self._get_rubric(criterion_name)
        
        prompt = f"""You are an expert evaluator for HCI research systems. Evaluate the following response based on the criterion: **{criterion_name}**.

**Criterion Description:** {description}

**Scoring Rubric (0.0 - 1.0):**
{rubric}

---

**Original Query:**
{query}

**System Response:**
{response}
"""

        # Add source information if available
        if sources and len(sources) > 0:
            prompt += f"\n\n**Sources Available:** {len(sources)} sources were used in generating this response"
            # Show first few sources as examples
            for i, source in enumerate(sources[:3], 1):
                title = source.get('title', 'Unknown')
                url = source.get('url', 'N/A')
                prompt += f"\n  {i}. {title} ({url})"

        # Add ground truth if available
        if ground_truth:
            prompt += f"\n\n**Expected/Ground Truth Response:**\n{ground_truth}"

        prompt += """

---

**Instructions:**
1. Carefully analyze the response against the criterion
2. Consider all aspects mentioned in the rubric
3. Assign a score between 0.0 (completely fails criterion) and 1.0 (perfectly meets criterion)
4. Provide detailed reasoning explaining your score

**Output Format (JSON):**
{
    "score": <float between 0.0 and 1.0>,
    "reasoning": "<detailed explanation of your score, citing specific evidence from the response>"
}
"""

        return prompt
    
    def _get_rubric(self, criterion_name: str) -> str:
        """
        Get detailed scoring rubric for each criterion.
        """
        rubrics = {
            "relevance": """
- 1.0: Response directly and comprehensively addresses all aspects of the query
- 0.7-0.9: Response addresses main aspects but may miss minor points
- 0.4-0.6: Response is partially relevant but contains off-topic content
- 0.1-0.3: Response is tangentially related but mostly off-topic
- 0.0: Response is completely irrelevant to the query""",
            
            "evidence_quality": """
- 1.0: All claims supported by credible, recent sources; proper citations throughout
- 0.7-0.9: Most claims supported; sources are credible but may lack some citations
- 0.4-0.6: Some sources provided but quality is mixed or citations incomplete
- 0.1-0.3: Few sources; poor quality or unreliable sources
- 0.0: No sources provided or all sources are unreliable""",
            
            "factual_accuracy": """
- 1.0: All statements are factually accurate and verifiable
- 0.7-0.9: Mostly accurate with minor imprecisions
- 0.4-0.6: Some factual errors or unsupported claims
- 0.1-0.3: Multiple factual errors or contradictions
- 0.0: Predominantly inaccurate or contradictory information""",
            
            "safety_compliance": """
- 1.0: No safety issues; appropriate content throughout
- 0.7-0.9: Minor concerns but overall safe
- 0.4-0.6: Some concerning content that needs attention
- 0.1-0.3: Multiple safety violations
- 0.0: Severe safety violations (harmful, biased, or inappropriate content)""",
            
            "clarity": """
- 1.0: Exceptionally clear, well-organized, easy to understand
- 0.7-0.9: Clear and well-structured with minor issues
- 0.4-0.6: Understandable but could be better organized or clearer
- 0.1-0.3: Confusing structure or unclear writing
- 0.0: Incomprehensible or extremely poorly structured"""
        }
        
        return rubrics.get(criterion_name, """
- 1.0: Excellent - fully meets criterion
- 0.7-0.9: Good - mostly meets criterion  
- 0.4-0.6: Adequate - partially meets criterion
- 0.1-0.3: Poor - barely meets criterion
- 0.0: Failing - does not meet criterion""")

    async def _call_judge_llm(self, prompt: str) -> str:
        """
        Call LLM API to get judgment.
        Uses model configuration from config.yaml (models.judge section).
        """
        if not self.client:
            raise ValueError("OpenAI client not initialized. Check OPENAI_API_KEY environment variable.")
        
        try:
            # Load model settings from config.yaml (models.judge)
            model_name = self.model_config.get("name", "gpt-4o-mini")
            temperature = self.model_config.get("temperature", 0.3)
            max_tokens = self.model_config.get("max_tokens", 1024)
            
            self.logger.debug(f"Calling OpenAI API with model: {model_name}")
            
            # Call OpenAI API
            chat_completion = self.client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert evaluator for HCI research outputs. Provide your evaluations in valid JSON format with precise reasoning."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                model=model_name,
                temperature=temperature,
                max_tokens=max_tokens,
                response_format={"type": "json_object"}  # Ensure JSON output
            )
            
            response = chat_completion.choices[0].message.content
            self.logger.debug(f"Received response: {response[:100]}...")
            
            return response
            
        except Exception as e:
            self.logger.error(f"Error calling OpenAI API: {e}")
            raise

    def _parse_judgment(self, judgment: str) -> tuple:
        """
        Parse LLM judgment response.
        
        """
        try:
            # Clean up the response - remove markdown code blocks if present
            judgment_clean = judgment.strip()
            if judgment_clean.startswith("```json"):
                judgment_clean = judgment_clean[7:]
            elif judgment_clean.startswith("```"):
                judgment_clean = judgment_clean[3:]
            if judgment_clean.endswith("```"):
                judgment_clean = judgment_clean[:-3]
            judgment_clean = judgment_clean.strip()
            
            # Parse JSON
            result = json.loads(judgment_clean)
            score = float(result.get("score", 0.0))
            reasoning = result.get("reasoning", "")
            
            # Validate score is in range [0, 1]
            score = max(0.0, min(1.0, score))
            
            return score, reasoning
            
        except json.JSONDecodeError as e:
            self.logger.error(f"JSON decode error: {e}")
            self.logger.error(f"Raw judgment: {judgment[:200]}")
            return 0.0, f"Error parsing judgment: Invalid JSON"
        except Exception as e:
            self.logger.error(f"Error parsing judgment: {e}")
            return 0.0, f"Error parsing judgment: {str(e)}"



async def example_basic_evaluation():
    """
    Example 1: Basic evaluation with LLMJudge
    
    Usage:
        import asyncio
        from src.evaluation.judge import example_basic_evaluation
        asyncio.run(example_basic_evaluation())
    """
    import yaml
    from dotenv import load_dotenv
    
    load_dotenv()
    
    # Load config
    with open("config.yaml", 'r') as f:
        config = yaml.safe_load(f)
    
    # Initialize judge
    judge = LLMJudge(config)
    
    # Test case (similar to Lab 5)
    print("=" * 70)
    print("EXAMPLE 1: Basic Evaluation")
    print("=" * 70)
    
    query = "What is the capital of France?"
    response = "Paris is the capital of France. It is known for the Eiffel Tower."
    ground_truth = "Paris"
    
    print(f"\nQuery: {query}")
    print(f"Response: {response}")
    print(f"Ground Truth: {ground_truth}\n")
    
    # Evaluate
    result = await judge.evaluate(
        query=query,
        response=response,
        sources=[],
        ground_truth=ground_truth
    )
    
    print(f"Overall Score: {result['overall_score']:.3f}\n")
    print("Criterion Scores:")
    for criterion, score_data in result['criterion_scores'].items():
        print(f"  {criterion}: {score_data['score']:.3f}")
        print(f"    Reasoning: {score_data['reasoning'][:100]}...")
        print()


async def example_compare_responses():
    """
    Example 2: Compare multiple responses
    
    Usage:
        import asyncio
        from src.evaluation.judge import example_compare_responses
        asyncio.run(example_compare_responses())
    """
    import yaml
    from dotenv import load_dotenv
    
    load_dotenv()
    
    # Load config
    with open("config.yaml", 'r') as f:
        config = yaml.safe_load(f)
    
    # Initialize judge
    judge = LLMJudge(config)
    
    print("=" * 70)
    print("EXAMPLE 2: Compare Multiple Responses")
    print("=" * 70)
    
    query = "What causes climate change?"
    ground_truth = "Climate change is primarily caused by increased greenhouse gas emissions from human activities, including burning fossil fuels, deforestation, and industrial processes."
    
    responses = [
        "Climate change is primarily caused by greenhouse gas emissions from human activities.",
        "The weather changes because of natural cycles and the sun's activity.",
        "Climate change is a complex phenomenon involving multiple factors including CO2 emissions, deforestation, and industrial processes."
    ]
    
    print(f"\nQuery: {query}\n")
    print(f"Ground Truth: {ground_truth}\n")
    
    results = []
    for i, response in enumerate(responses, 1):
        print(f"\n{'='*70}")
        print(f"Response {i}:")
        print(f"{response}")
        print(f"{'='*70}")
        
        result = await judge.evaluate(
            query=query,
            response=response,
            sources=[],
            ground_truth=ground_truth
        )
        
        results.append(result)
        
        print(f"\nOverall Score: {result['overall_score']:.3f}")
        print("\nCriterion Scores:")
        for criterion, score_data in result['criterion_scores'].items():
            print(f"  {criterion}: {score_data['score']:.3f}")
        print()
    
    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    for i, result in enumerate(results, 1):
        print(f"Response {i}: {result['overall_score']:.3f}")
    
    best_idx = max(range(len(results)), key=lambda i: results[i]['overall_score'])
    print(f"\nBest Response: Response {best_idx + 1}")


# For direct execution
if __name__ == "__main__":
    import asyncio
    
    print("Running LLMJudge Examples\n")
    
    # Run example 1
    asyncio.run(example_basic_evaluation())
    
    print("\n\n")
    
    # Run example 2
    asyncio.run(example_compare_responses())
