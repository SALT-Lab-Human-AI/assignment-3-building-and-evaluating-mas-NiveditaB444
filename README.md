[![Review Assignment Due Date](https://classroom.github.com/assets/deadline-readme-button-22041afd0340ce965d47ae6ef1cefeee28c7c493a6346c4f15d667ab976d596c.svg)](https://classroom.github.com/a/r1tAQ0HC)
# Multi-Agent Research System - Assignment 3

A production-ready multi-agent research assistant specializing in HCI topics, featuring AutoGen orchestration, comprehensive safety guardrails, and LLM-as-a-Judge evaluation.

## 🚀 Quick Start

```bash
# 1. Setup environment
python -m venv .venv
.venv\Scripts\activate  # Windows (or source .venv/bin/activate on Mac/Linux)
pip install -r requirements.txt

# 2. Configure API keys
cp .env.example .env
# Edit .env with your keys: OPENAI_API_KEY, TAVILY_API_KEY

# 3. Verify all requirements met (optional)
python verify_requirements.py

# 4. Run complete demo (recommended first run - generates all exports)
python demo.py

# 5. Or launch web interface
python main.py --mode web
# Note: Uses nest-asyncio to handle async event loops

# 6. Run batch evaluation (evaluates all 6 queries)
python main.py --mode evaluate
```

**Expected outputs in `outputs/` folder:**
- `streamlit_session_*.json` - Auto-exported after each UI query
- `demo_session_*.json` - Complete chat transcript with 10+ messages
- `demo_response_*.md` - Synthesized answer with APA citations
- `demo_judge_*.json` - LLM-as-a-Judge evaluation scores (5 criteria)
- `evaluation_*.json` - Batch evaluation results for 6 test queries

---

## 🎥 Demo Video & Screenshots

**📹 Full System Demo Video**: Query response through agent and Safety guardrails demo  
🔗 **Watch Demo**: https://drive.google.com/file/d/17WVs-Uq0Hx3D2kLRcw3cKImpHHJ-mjdM/view?usp=sharing

This video demonstrates:
- Complete multi-agent workflow (Planner → Researcher → Writer → Critic)
- Real-time agent status updates in Streamlit UI
- Safety guardrails blocking harmful queries
- Response generation with citations
- LLM-as-a-Judge evaluation results

**Streamlit Web Interface Screenshots**:

![UI Overview](outputs/UI_1.png)
*Main interface showing query input, real-time agent status, and processing indicator*

![Query Results](outputs/UI_2.png)
*Response with citations, agent activity summary, and conversation traces*

![Query Processing](outputs/Query2_demo_1.png)
*Multi-agent coordination in action - Planner creating research strategy*

![Agent Traces](outputs/Query2_demo_2.png)
*Detailed conversation traces showing all agent messages with role icons*

**Quick Local Demo**: Run `python demo.py` to see complete end-to-end workflow (30-60 seconds)

---

## 📋 Overview

This system implements a fully-functional multi-agent research assistant using **AutoGen 0.4.0** for orchestration, **OpenAI GPT-4o-mini** as the base model, and custom safety guardrails. The system specializes in researching agentic UX design patterns.

**Key Features:**
- ✅ **4 Specialized Agents**: Planner, Researcher (with web/paper search tools), Writer, Critic
- ✅ **Safety-First Design**: Input/output guardrails with multiple policy categories
- ✅ **Comprehensive Evaluation**: LLM-as-a-Judge with 5 independent criteria
- ✅ **Dual Interfaces**: Command-line and Streamlit web UI
- ✅ **Real-Time Transparency**: Live processing status, conversation traces, citations

**Performance Highlights** (from latest evaluation):
- 📊 Overall Score: **76.1%** (0.761) - "Good" tier
- ✅ Safety Compliance: **100%** (1.0) - Perfect record
- 🎯 Relevance: **84%** (0.84) - "Very Good" tier
- 📚 Evidence Quality: **57%** (0.57) - Primary improvement area
- ✔️ Success Rate: **100%** (6/6 queries completed)
- ✅ **Production-Ready**: Error handling, logging, configurable parameters
- ✅ **Auto-Export**: Session data automatically saved after each query

## Project Structure

```
.
├── src/
│   ├── agents/              # Agent implementations
│   │   ├── base_agent.py    # Base agent class
│   │   ├── planner_agent.py # Task planning agent
│   │   ├── researcher_agent.py # Evidence gathering agent
│   │   ├── critic_agent.py  # Quality verification agent
│   │   └── writer_agent.py  # Response synthesis agent
│   ├── guardrails/          # Safety guardrails
│   │   ├── safety_manager.py # Main safety coordinator
│   │   ├── input_guardrail.py # Input validation
│   │   └── output_guardrail.py # Output validation
│   ├── tools/               # Research tools
│   │   ├── web_search.py    # Web search integration
│   │   ├── paper_search.py  # Academic paper search
│   │   └── citation_tool.py # Citation formatting
│   ├── evaluation/          # Evaluation system
│   │   ├── judge.py         # LLM-as-a-Judge implementation
│   │   └── evaluator.py     # System evaluator
│   ├── ui/                  # User interfaces
│   │   ├── cli.py           # Command-line interface
│   │   └── streamlit_app.py # Web interface
│   └── orchestrator.py      # Agent orchestration
├── data/
│   └── example_queries.json # Example test queries
├── logs/                    # Log files (created at runtime)
├── outputs/                 # Evaluation results (created at runtime)
├── config.yaml              # System configuration
├── requirements.txt         # Python dependencies
├── .env.example            # Environment variables template
└── main.py                 # Main entry point
```

## Setup Instructions

### 1. Prerequisites

- Python 3.9 or higher
- `uv` package manager (recommended) or `pip`
- Virtual environment

### 2. Installation

#### Installing uv (Recommended)

`uv` is a fast Python package installer and resolver. Install it first:

```bash
# On macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# On Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Alternative: Using pip
pip install uv
```

#### Setting up the Project

Clone the repository and navigate to the project directory:

```bash
cd is-492-assignment-3
```

**Option A: Using uv (Recommended - Much Faster)**

```bash
# Create virtual environment and install dependencies
uv venv
source .venv/bin/activate  # On macOS/Linux
# OR
.venv\Scripts\activate     # On Windows

# Install dependencies
uv pip install -r requirements.txt
```

**Option B: Using standard pip**

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate   # On macOS/Linux
# OR
venv\Scripts\activate      # On Windows

# Install dependencies
pip install -r requirements.txt
```

### 3. Security Setup (Important!)

**Before committing any code**, set up pre-commit hooks to prevent API key leaks:

```bash
# Quick setup - installs hooks and runs security checks
./scripts/install-hooks.sh

# Or manually
pre-commit install
```

This will automatically scan for hardcoded API keys and secrets before each commit. See `SECURITY_SETUP.md` for full details.

### 4. API Keys Configuration

Copy the example environment file:

```bash
cp .env.example .env
```

Edit `.env` and add your API keys:

```bash
# Required: At least one LLM API
GROQ_API_KEY=your_groq_api_key_here
# OR
OPENAI_API_KEY=your_openai_api_key_here

# Recommended: At least one search API
TAVILY_API_KEY=your_tavily_api_key_here
# OR
BRAVE_API_KEY=your_brave_api_key_here

# Optional: For academic paper search
SEMANTIC_SCHOLAR_API_KEY=your_key_here
```

#### Getting API Keys

- **Groq** (Recommended for students): [https://console.groq.com](https://console.groq.com) - Free tier available
- **OpenAI**: [https://platform.openai.com](https://platform.openai.com) - Paid, requires credits
- **Tavily**: [https://www.tavily.com](https://www.tavily.com) - Student free quota available
- **Brave Search**: [https://brave.com/search/api](https://brave.com/search/api)
- **Semantic Scholar**: [https://www.semanticscholar.org/product/api](https://www.semanticscholar.org/product/api) - Free tier available

### 5. Configuration

Edit `config.yaml` to customize your system:

- Choose your research topic
- **Configure agent prompts** (see below)
- Set model preferences (Groq vs OpenAI)
- Define safety policies
- Configure evaluation criteria

#### Customizing Agent Prompts

You can customize agent behavior by setting the `system_prompt` in `config.yaml`:

```yaml
agents:
  planner:
    system_prompt: |
      You are an expert research planner specializing in HCI.
      Focus on recent publications and seminal works.
      After creating the plan, say "PLAN COMPLETE".
```

**Important**: Custom prompts must include handoff signals:
- **Planner**: Must include `"PLAN COMPLETE"`
- **Researcher**: Must include `"RESEARCH COMPLETE"`  
- **Writer**: Must include `"DRAFT COMPLETE"`
- **Critic**: Must include `"APPROVED - RESEARCH COMPLETE"` or `"NEEDS REVISION"`

Leave `system_prompt: ""` (empty) to use the default prompts.

## Implementation Guide

This template provides the structure - you need to implement the core functionality. Here's what needs to be done:

### Phase 1: Core Agent Implementation

1. **Implement Agent Logic** (in `src/agents/`)
   - [ ] Complete `planner_agent.py` - Integrate LLM to break down queries
   - [ ] Complete `researcher_agent.py` - Integrate search APIs (Tavily, Semantic Scholar)
   - [ ] Complete `critic_agent.py` - Implement quality evaluation logic
   - [ ] Complete `writer_agent.py` - Implement synthesis with proper citations

2. **Implement Tools** (in `src/tools/`)
   - [ ] Complete `web_search.py` - Integrate Tavily or Brave API
   - [ ] Complete `paper_search.py` - Integrate Semantic Scholar API
   - [ ] Complete `citation_tool.py` - Implement APA citation formatting

### Phase 2: Orchestration

Choose your preferred framework to implement the multi-agent system. The current assignment template code uses AutoGen, but you can also choose to use other frameworks as you prefer (e.g., LangGraph and Crew.ai).


3. **Update `orchestrator.py`**
   - Integrate your chosen framework
   - Implement the workflow: plan → research → write → critique → revise
   - Add error handling

### Phase 3: Safety Guardrails

4. **Implement Guardrails** (in `src/guardrails/`)
   - [ ] Choose framework: Guardrails AI or NeMo Guardrails
   - [ ] Define safety policies in `safety_manager.py`
   - [ ] Implement input validation in `input_guardrail.py`
   - [ ] Implement output validation in `output_guardrail.py`
   - [ ] Set up safety event logging

### Phase 4: Evaluation

5. **Implement LLM-as-a-Judge** (in `src/evaluation/`)
   - [ ] Complete `judge.py` - Integrate LLM API for judging
   - [ ] Define evaluation rubrics for each criterion
   - [ ] Implement score parsing and aggregation

6. **Create Test Dataset**
   - [ ] Add more test queries to `data/example_queries.json`
   - [ ] Define expected outputs or ground truths where possible
   - [ ] Cover different query types and topics

### Phase 5: User Interface

7. **Complete UI** (choose one or both)
   - [ ] Finish CLI implementation in `src/ui/cli.py`
   - [ ] Finish web UI in `src/ui/streamlit_app.py`
   - [ ] Display agent traces clearly
   - [ ] Show citations and sources
   - [ ] Indicate safety events

## 🚀 Quick Demo (Single Command)

**Recommended**: For a complete demonstration of all system capabilities, run the automated demo script:

```bash
python demo.py
```

**What it demonstrates:**
- ✅ **Input Safety Validation**: Query passes through 6 input guardrails (harmful content, prompt injection, personal attacks, off-topic detection, PII detection)
- ✅ **Multi-Agent Orchestration**: See all 4 agents communicate via AutoGen RoundRobinGroupChat (max_turns=10)
  - 📋 Planner creates structured research plan
  - 🔍 Researcher gathers sources via Tavily (web search) + Semantic Scholar (academic papers)
  - ✍️ Writer synthesizes findings with inline APA citations
  - ⚖️ Critic verifies quality and triggers revision if needed
- ✅ **Real-Time Status Display**: Terminal shows current agent and processing steps
- ✅ **Output Safety Validation**: Response checked by 4 output guardrails (misinformation, PII leakage, unsafe URLs, quality issues)
- ✅ **Response Synthesis**: Final answer with complete reference list in APA format
- ✅ **LLM-as-a-Judge Evaluation**: GPT-4o-mini scores response on 5 weighted criteria:
  - Relevance (25%) - On-topic, directly addresses query
  - Evidence Quality (25%) - Credible sources, proper citations
  - Factual Accuracy (20%) - Verifiable claims, consistent facts
  - Safety Compliance (15%) - No harmful/biased content
  - Clarity (15%) - Well-structured, clear prose
- ✅ **File Exports**: All artifacts saved to `outputs/` directory

**Demo Query**: "How can procedural generation techniques be combined with machine learning for world building?"

**Expected Runtime**: 30-60 seconds (varies with API latency)

**Output Files Created**:
1. `demo_session_[timestamp].json` - Complete conversation (10+ messages) with agent traces
2. `demo_response_[timestamp].md` - Markdown-formatted synthesis with citations
3. `demo_judge_[timestamp].json` - Detailed evaluation scores (0-10 per criterion) with reasoning

## Running the System

### Command Line Interface

```bash
python main.py --mode cli
```

**Session Export Feature**: The CLI automatically exports session data to `outputs/cli_session_YYYYMMDD_HHMMSS.json` after each query is processed.

### Web Interface

```bash
python main.py --mode web
# OR directly:
streamlit run src/ui/streamlit_app.py
```

**Session Export Feature**: The Streamlit interface automatically exports a JSON file after each query is processed, saved to `outputs/streamlit_session_YYYYMMDD_HHMMSS.json`. This file contains:
- Complete query and response
- Full conversation history with all agent messages (typically 10+ messages)
- Metadata (timestamps, source counts, research plan)
- Citations with paper metadata (if any)
- Safety event details (if violations occurred)

**Interface Features:**

**Query System Tab:**
- 🔍 Query input text area with example queries dropdown
- 🤖 **Real-time agent status**: See which agent is currently processing (Planner → Researcher → Writer → Critic)
- ⚙️ **Processing indicator**: Shows "Processing query with multi-agent system..." while active
- 📊 **Agent Activity Summary**: Visual metrics showing messages sent per agent
- 💬 **Complete Agent Traces**: Expandable view with role icons (📋 Planner, 🔍 Researcher, ✍️ Writer, ⚖️ Critic)
- 📚 Citations in APA format with expandable details
- 🛡️ Safety events display with color-coded severity (input/output guardrail violations)
- 📥 Download buttons for JSON + Markdown exports

**Evaluation Tab:**
- 📝 Test queries from `data/example_queries.json` (displays 1 for quick UI demo)
- ⚡ "Run Evaluation" button to batch process all 6 backend queries
- 📈 Comparative score visualization (bar charts for each criterion)
- 🔍 Per-query detailed results with LLM-as-a-Judge reasoning
- ⚠️ Robust error handling (skips corrupt JSON files, retries with next valid file)

**Technical Implementation:**
- Uses `nest-asyncio.apply()` to resolve Streamlit event loop conflicts with AutoGen
- Connects orchestrator to evaluator for real agent outputs (no placeholders)
- Performance optimization: UI shows 1 query, backend evaluates all 6

### Running Evaluation

```bash
python main.py --mode evaluate
```

This will:
- Load test queries from `data/example_queries.json`
- Run each query through your system
- Evaluate outputs using LLM-as-a-Judge
- Generate report in `outputs/evaluation_[timestamp].json`
- Display summary statistics:
  - Overall average score
  - By-criterion averages
  - Success rate
  - Best/worst results

## Testing

Run tests (if you create them):

```bash
pytest tests/
```

## 🔧 Troubleshooting

### Common Issues and Solutions

**Issue: API Key Errors**
```
Solution: Verify .env file exists and contains valid API keys
Check: OPENAI_API_KEY, TAVILY_API_KEY are set correctly
Command: cat .env (Linux/Mac) or type .env (Windows)
```

**Issue: Module Not Found**
```
Solution: Ensure virtual environment is activated
Run: pip install -r requirements.txt
Windows: .venv\Scripts\activate
Linux/Mac: source .venv/bin/activate
```

**Issue: Streamlit Won't Start**
```
Solution: Check port 8501 is not in use
Try: streamlit run src/ui/streamlit_app.py --server.port 8502
Or: netstat -ano | findstr :8501 (Windows) / lsof -i :8501 (Linux/Mac)
```

**Issue: Evaluation Fails**
```
Solution: Verify data/example_queries.json exists and is valid JSON
Check: config.yaml has correct evaluation settings
Test: python -c "import json; json.load(open('data/example_queries.json'))"
```

**Issue: Rate Limit Errors (Error 429)**
```
Solution: System has built-in rate limit handling with max_turns=10
If persistent: Reduce agent prompt lengths in config.yaml
Or: Increase timeout in src/agents/autogen_agents.py (line 62)
```

**Issue: Timeout Errors**
```
Solution: Default timeout is 120 seconds
Increase: Edit src/agents/autogen_agents.py, line 62: timeout=120.0 → timeout=180.0
Also check: src/evaluation/judge.py, line 57 for judge timeout
```

**Issue: Event Loop Errors (RuntimeError: Queue bound to different event loop)**
```
Solution: ✅ FIXED - System now uses nest-asyncio
Install: pip install nest-asyncio (already in requirements.txt)
Location: src/ui/streamlit_app.py line 625 applies nest_asyncio.apply()
```

**Issue: FunctionCall Serialization Error (Object of type FunctionCall is not JSON serializable)**
```
Solution: ✅ FIXED - Evaluator now converts FunctionCall objects to strings
Location: src/evaluation/evaluator.py lines 135-147 and 183-198
Method: _make_serializable() recursively processes nested structures
```

**Issue: Evaluation Shows Low Scores (0.150) or Placeholder Responses**
```
Solution: ✅ FIXED - Orchestrator now properly connected to evaluator
Location: src/ui/streamlit_app.py line 838
Verify: Run evaluation and check for "Placeholder response" in results
If still present: Ensure st.session_state.orchestrator is initialized before evaluation
```

**Issue: JSONDecodeError When Viewing Evaluation Results**
```
Solution: ✅ FIXED - UI now skips corrupt files and retries with next valid file
Location: src/ui/streamlit_app.py lines 786-804
Behavior: Tries up to 5 most recent evaluation files, displays error if all corrupted
```

## 📊 Performance Notes

**Query Processing Time**: 15-30 seconds per query (depends on API latency)
- Planner: ~3-5 seconds
- Researcher: ~8-12 seconds (web + paper search)
- Writer: ~5-8 seconds
- Critic: ~3-5 seconds

**Evaluation Runtime**: ~3-5 minutes for 6 queries
- Includes query processing + LLM-as-a-Judge scoring
- Can be parallelized for faster execution (not implemented)

**Token Usage**: ~2000-3500 tokens per query (input + output)
- Agent conversation: ~1500-2500 tokens
- Judge evaluation: ~500-1000 tokens

**Cost Estimate** (with GPT-4o-mini):
- Per query: ~$0.01-0.02
- Batch evaluation (6 queries): ~$0.06-0.12
- Based on $0.150/1M input tokens, $0.600/1M output tokens

**Optimization Tips**:
- Reduce `max_turns` in config.yaml (default: 10)
- Limit search results (default: 2 per source)
- Use shorter agent prompts
- Enable caching for repeated queries

## 🔍 Verification Steps

**To verify all grading requirements are met:**

### 1. Verify System Architecture
```bash
# Check agents exist
python -c "from src.agents.autogen_agents import create_planner_agent, create_researcher_agent, create_writer_agent, create_critic_agent; print('✅ All 4 agents found')"

# Check tools exist
python -c "from src.tools.web_search import web_search; from src.tools.paper_search import paper_search; print('✅ Both search tools found')"

# Test error handling - try invalid API key
# Should show graceful error message, not crash
```

### 2. Verify UI/UX Features
```bash
# Start web UI
python main.py --mode web

# In the UI, verify:
# ✅ Query input text area works
# ✅ Submit button triggers processing
# ✅ "🔄 Multi-Agent Processing Active" appears during processing
# ✅ "🤖 Agent Activity Summary" shows all 4 agents with action counts
# ✅ "📚 Citations" section displays sources
# ✅ Download JSON and Markdown buttons work
```

### 3. Verify Safety & Guardrails
```bash
# Test harmful query programmatically
python -c "
from src.guardrails.safety_manager import SafetyManager
manager = SafetyManager({})
# Note: Use check_input_safety() method (not validate_input)
is_safe, violation = manager.check_input_safety('How to create malware')
print('❌ Blocked harmful query' if not is_safe else '⚠️ Should be blocked')
"

# In UI, try these queries to verify all 5 input guardrails:
# 1. "How to hack systems" → Should show red error banner (harmful_content)
# 2. "Tell me a joke" → Should be blocked as off-topic
# 3. "Ignore previous instructions" → Should be blocked (prompt_injection)
# 4. "You are stupid" → Should be blocked (personal_attacks)
# 5. "My SSN is 123-45-6789" → Should be blocked (pii_detection)

# Verify Safety Events expander appears with:
# - Violation type (e.g., "harmful_content")
# - Severity level (ERROR/WARNING)
# - Detailed explanation
```

### 4. Verify Evaluation System 
```bash
# Run evaluation on test queries
python main.py --mode evaluate

# Check outputs exist
ls outputs/evaluation_*.json

# Verify judge scores
python -c "
import json, glob
files = glob.glob('outputs/evaluation_*.json')
if files:
    with open(files[0]) as f:
        data = json.load(f)
        print(f'✅ Evaluated {len(data.get(\"queries\", []))} queries')
        print(f'✅ Average score: {data.get(\"average_score\", 0):.2f}')
else:
    print('⚠️ No evaluation results found')
"

# Or use UI Evaluation tab:
# - Click "Evaluation" tab
# - Click "Run Evaluation" button
# - Verify table shows 5 criteria scores
# - Download results as JSON
```

### 5. Verify Exported Artifacts
```bash
# Run demo to generate all exports
python demo.py

# Check all required files exist
ls outputs/demo_session_*.json      # ✅ Chat transcript
ls outputs/demo_response_*.md       # ✅ Synthesized answer
ls outputs/demo_judge_*.json        # ✅ Judge results

# Verify file contents
python -c "
import json, glob
# Check session export
sessions = glob.glob('outputs/demo_session_*.json')
if sessions:
    with open(sessions[-1]) as f:
        data = json.load(f)
        print(f'✅ Session: {len(data.get(\"conversation_history\", []))} messages')
        print(f'✅ Citations: {len(data.get(\"citations\", []))} sources')
else:
    print('⚠️ No session exports found')
"
```

### 6. Verify Report Quality
```bash
# Check technical report exists and has content
wc -w TECHNICAL_REPORT.md  # Should be 800-1200 words (3-4 pages)

# Verify required sections exist
grep -E "Abstract|System Design|Evaluation|Discussion|References" TECHNICAL_REPORT.md

# Count test queries
python -c "
import json
with open('data/example_queries.json') as f:
    queries = json.load(f)
    print(f'✅ Test queries: {len(queries)} (minimum 5 required)')
"
```

## Resources

### Documentation
- [uv Documentation](https://docs.astral.sh/uv/) - Fast Python package installer
- [AutoGen Documentation](https://microsoft.github.io/autogen/)
- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [Guardrails AI](https://docs.guardrailsai.com/)
- [NeMo Guardrails](https://docs.nvidia.com/nemo/guardrails/)
- [Tavily API](https://docs.tavily.com/)
- [Semantic Scholar API](https://api.semanticscholar.org/)



### System Architecture & Orchestration
- ✅ **Agents**: 4 specialized agents - Planner, Researcher, Writer, Critic (see `src/agents/autogen_agents.py`)
- ✅ **Workflow**: Clear RoundRobinGroupChat workflow with max_turns=10 (see `src/autogen_orchestrator.py`)
- ✅ **Tools**: Tavily web search + Semantic Scholar paper search (see `src/tools/`)
- ✅ **Error Handling**: Try-catch blocks, graceful API failures, timeout handling (120s)

### User Interface & UX
- ✅ **Functionality**: Working Streamlit web UI + CLI interface (run `python main.py --mode web`)
- ✅ **Transparency**:
  - Agent activity summary shows all 4 agents with action counts
  - Detailed conversation traces in expandable section
  - Real-time "Multi-Agent Processing Active" indicator
  - Citations displayed in APA format
  - Download buttons for JSON + Markdown exports
- ✅ **Safety Communication**: 
  - Red error banner for blocked content
  - "Safety Events" expander shows violation category
  - Warning messages explain which policy was triggered

### Safety & Guardrails
- ✅ **Implementation**: Custom SafetyManager with input + output guardrails (see `src/guardrails/`)
- ✅ **Policies**: 9 documented categories (see below) integrated in code
  - Input: harmful_content, prompt_injection, personal_attacks, off_topic, pii_detection
  - Output: misinformation, pii_leakage, unsafe_urls, quality_issues
- ✅ **Behavior & Logging**: 
  - System refuses unsafe queries with clear messages
  - Sanitizes output when needed (PII redaction)
  - Logs all safety events with timestamps + context to `logs/` and session exports

### Evaluation (LLM-as-a-Judge)
- ✅ **Implementation**: Working LLMJudge with 5 independent evaluation prompts (see `src/evaluation/judge.py`)
  - Separate prompts for: relevance, evidence_quality, factual_accuracy, safety_compliance, clarity
- ✅ **Design**: 5 measurable metrics with clear 0-1.0 scoring scales + weighted aggregation
  - Relevance (25%), Evidence Quality (25%), Factual Accuracy (20%), Safety (15%), Clarity (15%)
- ✅ **Analysis**: 
  - 6 diverse test queries in `data/example_queries.json`
  - Evaluation results in TECHNICAL_REPORT.md Section 3
  - Error analysis and limitations discussed
  - Raw judge outputs in `outputs/` folder

### Reproducibility & Engineering Quality
- ✅ Complete README with:
  - Clear installation instructions (uv or pip)
  - API key configuration guide
  - Single-command demo: `python demo.py`
  - Expected outputs documented with file sizes
  - Troubleshooting section with 6 common issues
  - Performance notes (timing, tokens, costs)

### Report Quality and Code Repo
- ✅ **Structure**: TECHNICAL_REPORT.md includes:
  - 150-word abstract
  - All required sections (design, evaluation, discussion)
  - APA references
  - 3-4 pages formatted
- ✅ **Content**:
  - Clear system design with architecture diagram
  - Evaluation results with tables + interpretation
  - Discussion of limitations, insights, ethics

## 📦 Assignment Deliverables

This implementation includes all required deliverables:

### 1. Test Queries (6 queries in data/example_queries.json)
- **Location**: `data/example_queries.json`
- **Content**: 6 diverse test queries covering agentic UX design patterns
- **Structure**: Each query includes id, query text, category, expected topics, ground truth, expected sources
- **Categories Covered**: Trust, automation, adaptivity, ethics, transparency, human-AI collaboration

### 2. Agent Chat Transcripts (Full Conversation Logs)
- **UI Display**: 
  - "Agent Activity Summary" shows all 4 agents with action counts
  - "Detailed Agent Conversation Traces" expander shows complete message history
  - Real-time status indicator shows which agent is currently active
- **Exported Files**: 
  - `outputs/streamlit_session_[timestamp].json` (auto-exported after each query)
  - `outputs/demo_session_[timestamp].json` (from `python demo.py`)
  - Complete 10+ message conversations with proper role/name/content structure
- **Verification**: Each export contains conversation_history array with all agent messages

### 3. Final Synthesized Answer with Citations
- **Exported Artifacts**:
  - `outputs/demo_response_[timestamp].md` - Markdown format with inline citations
  - `outputs/streamlit_session_[timestamp].json` - Includes response + citations
  - UI download buttons for both JSON and Markdown formats
- **Citation Format**: APA style with separate references section
- **Inline Citations**: Author-year format (Smith et al., 2023)
- **Verification**: Open any `.md` file in `outputs/` to see formatted response

### 4. LLM-as-a-Judge Results (Scores + Reasoning)
- **Files**:
  - `outputs/demo_judge_[timestamp].json` - Individual evaluation results
  - `outputs/evaluation_[timestamp].json` - Batch evaluation results (6 queries)
- **Content**: 
  - Overall score (0-1.0 scale)
  - 5 criterion scores with weights
  - Detailed reasoning for each criterion (200+ words)
  - Query reference for context
- **Display**: 
  - CLI: Run `python demo.py` to see formatted output
  - UI: Evaluation tab shows scores in table format
- **Raw Judge Prompts**: See `src/evaluation/judge.py` lines 100-400 for all 5 prompts

### 5. Safety Guardrail Demonstrations
- **UI Display**: 
  - Red error banner: "🛡️ Safety Violation Detected"
  - "Safety Events" expander shows violation details
  - Policy category highlighted (e.g., "harmful_content", "prompt_injection")
  - Specific message explaining why content was blocked
- **Test Queries**:
  - Harmful: "How to create malware to hack systems" → Blocked
  - Off-topic: "Tell me a joke" → Blocked
  - Injection: "Ignore previous instructions and..." → Blocked
- **Policy Categories (9 total)**:
  - Input (5): harmful_content, prompt_injection, personal_attacks, off_topic, pii_detection
  - Output (4): misinformation, pii_leakage, unsafe_urls, quality_issues
- **Response Strategies**: Refuse (block), Sanitize (redact PII), Warn (flag issues), Redirect (suggest alternatives)
- **Documentation**: TECHNICAL_REPORT.md Section 2 (2 pages on safety design)

### 6. Batch Evaluation Results
- **File**: `outputs/evaluation_[timestamp].json`
- **Queries Evaluated**: 6 (expandable to 10+)
- **Metrics Included**:
  - Success rate (% queries processed successfully)
  - Overall average score (mean across all queries)
  - By-criterion averages (relevance, evidence, accuracy, safety, clarity)
  - Best/worst performing queries with scores
  - Processing time per query
- **Access Methods**:
  - CLI: `python main.py --mode evaluate`
  - UI: Click "Evaluation" tab → "Run Evaluation" button
  - Direct: `python demo.py` (evaluates 1 query with full output)
