"""
AutoGen Agent Implementations

This module provides concrete AutoGen-based implementations of the research agents.
Each agent is implemented as an AutoGen AssistantAgent with specific tools and behaviors.

Based on the AutoGen literature review example:
https://microsoft.github.io/autogen/stable/user-guide/agentchat-user-guide/examples/literature-review.html
"""

import os
from typing import Dict, Any, List, Optional
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_agentchat.conditions import TextMentionTermination
from autogen_core.tools import FunctionTool
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_core.models import ModelFamily
# Import our research tools
from src.tools.web_search import web_search
from src.tools.paper_search import paper_search


def create_model_client(config: Dict[str, Any]) -> OpenAIChatCompletionClient:
    """
    Create model client for AutoGen agents.
    
    Args:
        config: Configuration dictionary from config.yaml
        
    Returns:
        OpenAIChatCompletionClient configured for the specified provider
    """
    model_config = config.get("models", {}).get("default", {})
    provider = model_config.get("provider", "groq")
    
    # Groq configuration (uses OpenAI-compatible API)
    if provider == "groq":
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY not found in environment")
        
        return OpenAIChatCompletionClient(
            model=model_config.get("name", "llama-3.3-70b-versatile"),
            api_key=api_key,
            base_url="https://api.groq.com/openai/v1",
            model_capabilities={
                "json_output": False,
                "vision": False,
                "function_calling": True,
            }
        )
    
    # OpenAI configuration
    elif provider == "openai":
        api_key = os.getenv("OPENAI_API_KEY")
        base_url = os.getenv("OPENAI_BASE_URL")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in environment")
        
        return OpenAIChatCompletionClient(
            model=model_config.get("name", "gpt-4o-mini"),
            api_key=api_key,
            base_url=base_url,
            timeout=120.0,  # Increase timeout to 120 seconds
        )

    elif provider == "vllm":
        api_key = os.getenv("OPENAI_API_KEY")
        base_url = os.getenv("OPENAI_BASE_URL")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in environment")
        
        return OpenAIChatCompletionClient(
            model=model_config.get("name", "gpt-4o-mini"),
            api_key=api_key,
            base_url=base_url,
            model_info={
                "vision": False,
                "function_calling": True,
                "json_output": True,
                "family": ModelFamily.GPT_4O,
                "structured_output": True,
            },
        )
    
    else:
        raise ValueError(f"Unsupported provider: {provider}")


def create_planner_agent(config: Dict[str, Any], model_client: OpenAIChatCompletionClient) -> AssistantAgent:
    """
    Create a Planner Agent using AutoGen.
    
    The planner breaks down research queries into actionable steps.
    It doesn't use tools, but provides strategic direction.
    
    Args:
        config: Configuration dictionary
        model_client: Model client for the agent
        
    Returns:
        AutoGen AssistantAgent configured as a planner
    """
    agent_config = config.get("agents", {}).get("planner", {})
    
    # Load system prompt from config or use default
    default_system_message = """You are a Research Planner. Break down queries into 3-4 clear, actionable steps.

1. Identify 2-3 key concepts to investigate
2. Suggest specific search queries for the Researcher (max 2-3 queries)
3. Note how findings should be synthesized

Be concise and specific. Keep your plan to 5-6 sentences max."""

    # Use custom prompt from config if available, otherwise use default
    custom_prompt = agent_config.get("system_prompt", "")
    if custom_prompt and custom_prompt != "You are a task planner. Break down research queries into actionable steps.":
        system_message = custom_prompt
    else:
        system_message = default_system_message

    planner = AssistantAgent(
        name="Planner",
        model_client=model_client,
        description="Breaks down research queries into actionable steps",
        system_message=system_message,
    )
    
    return planner


def create_researcher_agent(config: Dict[str, Any], model_client: OpenAIChatCompletionClient) -> AssistantAgent:
    """
    Create a Researcher Agent using AutoGen.
    
    The researcher has access to web search and paper search tools.
    It gathers evidence based on the planner's guidance.
    
    Args:
        config: Configuration dictionary
        model_client: Model client for the agent
        
    Returns:
        AutoGen AssistantAgent configured as a researcher with tool access
    """
    agent_config = config.get("agents", {}).get("researcher", {})
    
    # Load system prompt from config or use default
    default_system_message = """You are a Research Assistant. Your job is to gather high-quality information from academic papers and web sources.

You have access to tools for web search and paper search. When conducting research:
1. Use both web search and paper search for comprehensive coverage
2. Look for recent, high-quality sources
3. Extract key findings, quotes, and data
4. Note all source URLs and citations
5. Gather evidence that directly addresses the research query"""

    # Use custom prompt from config if available
    custom_prompt = agent_config.get("system_prompt", "")
    if custom_prompt and custom_prompt != "You are a researcher. Find and collect relevant information from various sources.":
        system_message = custom_prompt
    else:
        system_message = default_system_message

    # Wrap tools in FunctionTool
    web_search_tool = FunctionTool(
        web_search,
        description="Search the web for articles, blog posts, and general information. Returns formatted search results with titles, URLs, and snippets."
    )
    
    paper_search_tool = FunctionTool(
        paper_search,
        description="Search academic papers on Semantic Scholar. Returns papers with authors, abstracts, citation counts, and URLs. Use year_from parameter to filter recent papers."
    )

    # Create the researcher with tool access
    researcher = AssistantAgent(
        name="Researcher",
        model_client=model_client,
        tools=[web_search_tool, paper_search_tool],
        description="Gathers evidence from web and academic sources using search tools",
        system_message=system_message,
    )
    
    return researcher


def create_writer_agent(config: Dict[str, Any], model_client: OpenAIChatCompletionClient) -> AssistantAgent:
    """
    Create a Writer Agent using AutoGen.
    
    The writer synthesizes research findings into coherent responses with proper citations.
    
    Args:
        config: Configuration dictionary
        model_client: Model client for the agent
        
    Returns:
        AutoGen AssistantAgent configured as a writer
    """
    agent_config = config.get("agents", {}).get("writer", {})
    
    # Load system prompt from config or use default
    default_system_message = """You are a Research Writer. Synthesize findings into a clear, concise response (max 400 words).

1. Brief overview (1-2 sentences)
2. Key findings with inline citations [Source: Title]
3. Brief references section

Be direct, well-organized, and cite sources. Keep response focused and concise."""

    # Use custom prompt from config if available
    custom_prompt = agent_config.get("system_prompt", "")
    if custom_prompt and custom_prompt != "You are a writer. Synthesize research findings into a coherent report.":
        system_message = custom_prompt
    else:
        system_message = default_system_message

    writer = AssistantAgent(
        name="Writer",
        model_client=model_client,
        description="Synthesizes research findings into coherent, well-cited responses",
        system_message=system_message,
    )
    
    return writer


def create_critic_agent(config: Dict[str, Any], model_client: OpenAIChatCompletionClient) -> AssistantAgent:
    """
    Create a Critic Agent using AutoGen.
    
    The critic evaluates the quality of the research and writing,
    providing feedback for improvement.
    
    Args:
        config: Configuration dictionary
        model_client: Model client for the agent
        
    Returns:
        AutoGen AssistantAgent configured as a critic
    """
    agent_config = config.get("agents", {}).get("critic", {})
    
    # Load system prompt from config or use default
    default_system_message = """You are a Research Critic. Provide brief quality evaluation.

Rate (1-10) and check:
1. Sources: Sufficient citations?
2. Relevance: Answers query?
3. Clarity: Well-organized?

Keep feedback to 3-4 sentences. End with "TERMINATE" if score >=7, or suggest 1-2 key improvements."""

    # Use custom prompt from config if available
    custom_prompt = agent_config.get("system_prompt", "")
    if custom_prompt and custom_prompt != "You are a critic. Evaluate the quality and accuracy of research findings.":
        system_message = custom_prompt
    else:
        system_message = default_system_message

    critic = AssistantAgent(
        name="Critic",
        model_client=model_client,
        description="Evaluates research quality and provides feedback",
        system_message=system_message,
    )
    
    return critic


def create_research_team(config: Dict[str, Any]) -> RoundRobinGroupChat:
    """
    Create the research team as a RoundRobinGroupChat.
    
    Args:
        config: Configuration dictionary
        
    Returns:
        RoundRobinGroupChat with all agents configured
    """
    # Create model client (shared by all agents)
    model_client = create_model_client(config)
    
    # Create all agents
    planner = create_planner_agent(config, model_client)
    researcher = create_researcher_agent(config, model_client)
    writer = create_writer_agent(config, model_client)
    critic = create_critic_agent(config, model_client)
    
    # Create termination condition
    termination = TextMentionTermination("TERMINATE")
    
    # Create team with round-robin ordering and max_turns to prevent excessive context
    team = RoundRobinGroupChat(
        participants=[planner, researcher, writer, critic],
        termination_condition=termination,
        max_turns=10,  # Limit to 10 turns to prevent token overflow
    )
    
    return team

