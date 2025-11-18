# Cortex-R Agent Framework

A reasoning-driven AI agent framework capable of using external tools, memory, and historical context to solve complex tasks step-by-step.

## Architecture Overview

### System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         User Input                              │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │  Heuristics     │  ← Query sanitization, banned words
                    │  Module         │     profanity filter, entity extraction
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │  Perception      │  ← Intent analysis, entity extraction
                    │  Module          │     MCP server selection
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │  Strategy        │  ← Planning mode (conservative/exploratory)
                    │  Module          │     Tool filtering, memory fallback
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │  Decision        │  ← LLM-based plan generation
                    │  Generation      │     Historical context integration
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │  Action         │  ← Python sandbox execution
                    │  Execution      │     Tool calling via MCP
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │  Heuristics     │  ← Result sanitization
                    │  (Result)       │     Sensitive info redaction
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │  Memory         │  ← Session storage
                    │  Manager        │     Historical indexing
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │  Final Answer   │
                    └─────────────────┘
```

### Component Details

#### 1. **Agent Loop** (`core/loop.py`)
- Main orchestration loop that coordinates all components
- Manages step-by-step execution with retry logic (lifelines)
- Handles `FURTHER_PROCESSING_REQUIRED` for multi-step tasks
- Integrates heuristics for query and result processing

#### 2. **Perception Module** (`modules/perception.py`)
- Analyzes user queries to extract:
  - **Intent**: What the user wants to accomplish
  - **Entities**: Key names, numbers, concepts
  - **Tool Hint**: Suggested tool category
  - **Selected Servers**: Relevant MCP servers to use
- Uses LLM to generate structured perception results

#### 3. **Strategy Module** (`core/strategy.py`)
- **Planning Modes**:
  - **Conservative**: Plans one tool call at a time
  - **Exploratory**: Can plan multiple tool options (parallel/sequential)
- **Tool Filtering**: Uses perception hints to filter available tools
- **Memory Fallback**: Falls back to previously successful tools on failure
- **Force Replan**: Triggers replanning when lifelines are exhausted

#### 4. **Decision Generation** (`core/strategy.py` → `generate_plan`)
- Generates Python `solve()` function using LLM
- Integrates historical conversation context
- Uses decision prompts (conservative/exploratory variants)
- Returns executable Python code

#### 5. **Action Execution** (`modules/action.py`)
- Executes generated `solve()` function in Python sandbox
- Provides `mcp` object for tool calling
- Limits tool calls per plan (MAX_TOOL_CALLS_PER_PLAN = 5)
- Returns results or error messages

#### 6. **Heuristics Module** (`modules/heuristics.py`)
**10 Heuristics Implemented:**
1. **Remove Banned Words**: Filters inappropriate content
2. **Remove Profanity**: Regex-based profanity filtering
3. **Redact Sensitive Info**: Credit cards, SSN, long numeric IDs
4. **Normalize Whitespace**: Cleans excessive spaces/newlines
5. **Remove Special Chars**: Optional special character removal
6. **Limit Length**: Prevents token overflow (max 5000 chars)
7. **Extract Key Entities**: Numbers, capitalized words, quoted strings
8. **Validate Query Structure**: Checks question format, imperative verbs
9. **Sanitize Result**: Comprehensive result cleaning pipeline
10. **Enhance Query with Context**: Adds historical context to queries

#### 7. **Memory Manager** (`modules/memory.py`)
- Stores session-based memory items:
  - `run_metadata`: Session start info
  - `tool_call`: Tool invocation records
  - `tool_output`: Tool results with success/failure
  - `final_answer`: Final answers
- Persists to JSON files in date-based directory structure
- Provides historical context for heuristics

#### 8. **Historical Conversation Index** (`modules/historical_conversation.py`)
- Indexes all past conversations from memory files
- Stores: query, answer, tools used, entities, success status
- **Search Functionality**: Semantic search by query text
- **Context Retrieval**: Returns relevant historical conversations for LLM context
- Auto-indexes sessions after completion
- Stores index in `memory/historical_conversation_store.json`

#### 9. **MCP Integration** (`core/session.py`)
- **MultiMCP**: Manages multiple MCP servers
- Discovers tools from configured servers
- Routes tool calls to appropriate servers
- Stateless design (fresh connection per call)

#### 10. **Context Management** (`core/context.py`)
- **AgentContext**: Holds session state, user input, memory, strategies
- **AgentProfile**: Loads configuration from `config/profiles.yaml`
- Tracks step progress, subtasks, final answers

## Data Flow

### Query Processing Flow

1. **User Input** → Heuristics (sanitize, enhance)
2. **Perception** → Extract intent, entities, select servers
3. **Strategy** → Filter tools, select planning mode
4. **Decision** → Generate `solve()` function with historical context
5. **Action** → Execute in sandbox, call tools via MCP
6. **Result** → Heuristics (sanitize), check for FINAL_ANSWER
7. **Memory** → Store results, index conversation
8. **Return** → Final answer or continue with FURTHER_PROCESSING_REQUIRED

### Memory and Historical Context Flow

```
Session Memory → Historical Index → Search by Query → 
Context Retrieval → Decision Prompt Enhancement → LLM
```

## Configuration

### `config/profiles.yaml`

```yaml
strategy:
  planning_mode: conservative  # or exploratory
  exploration_mode: parallel    # or sequential
  memory_fallback_enabled: true
  max_steps: 3
  max_lifelines_per_step: 3

mcp_servers:
  - id: math
    script: mcp_server_1.py
    description: "Math tools"
  - id: documents
    script: mcp_server_2.py
    description: "Document tools"
```

## Usage Examples

### Example 1: Complex Calculation Query

**Query:** "What is the square root of 144 multiplied by the factorial of 3?"

**Full Log:**
```
🧑 What do you want to solve today? → What is the square root of 144 multiplied by the factorial of 3?
🔁 Step 1/3 starting...
[19:55:55] [perception] Raw output: ```json
{
  "intent": "Calculate a mathematical expression involving square root and factorial.",
  "entities": ["square root", "144", "factorial", "3"],
  "tool_hint": "python sandbox",
  "selected_servers": ["math"]
}
```
result {'intent': 'Calculate a mathematical expression involving square root and factorial.', 'entities': ['square root', '144', 'factorial', '3'], 'tool_hint': 'python sandbox', 'selected_servers': ['math']}
[perception] intent='Calculate a mathematical expression involving square root and factorial.' entities=['square root', '144', 'factorial', '3'] tool_hint='python sandbox' tags=[] selected_servers=['math']
[19:55:57] [plan] Generated solve():
```python
async def solve():
    sqrt_result = await mcp.call_tool('power', {"input": {"a": 144, "b": 0.5}})
    sqrt_val = parse_result(sqrt_result)

    fact_result = await mcp.call_tool('factorial', {"input": {"a": 3}})
    fact_val = parse_result(fact_result)

    mult_result = await mcp.call_tool('multiply', {"input": {"a": sqrt_val, "b": fact_val}})
    answer = parse_result(mult_result)
    return f"FINAL_ANSWER: {answer}"
```
[plan] async def solve():
    sqrt_result = await mcp.call_tool('power', {"input": {"a": 144, "b": 0.5}})
    sqrt_val = parse_result(sqrt_result)

    fact_result = await mcp.call_tool('factorial', {"input": {"a": 3}})
    fact_val = parse_result(fact_result)

    mult_result = await mcp.call_tool('multiply', {"input": {"a": sqrt_val, "b": fact_val}})
    answer = parse_result(mult_result)
    return f"FINAL_ANSWER: {answer}"
[loop] Detected solve() plan — running sandboxed...
[action] 🔍 Entered run_python_sandbox()
[19:55:57] [sandbox] Executing code (first 500 chars):
async def solve():
    sqrt_result = await mcp.call_tool('power', {"input": {"a": 144, "b": 0.5}})
    sqrt_val = parse_result(sqrt_result)

    fact_result = await mcp.call_tool('factorial', {"input": {"a": 3}})
    fact_val = parse_result(fact_result)

    mult_result = await mcp.call_tool('multiply', {"input": {"a": sqrt_val, "b": fact_val}})
    answer = parse_result(mult_result)
    return f"FINAL_ANSWER: {answer}"...
[19:55:58] [sandbox] Tool 'power' returned: type=<class 'mcp.types.CallToolResult'>, has_content=True
[19:55:58] [sandbox] Content[0].text length: 20
[19:55:59] [sandbox] Tool 'factorial' returned: type=<class 'mcp.types.CallToolResult'>, has_content=True
[19:55:59] [sandbox] Content[0].text length: 17
[19:56:00] [sandbox] Tool 'multiply' returned: type=<class 'mcp.types.CallToolResult'>, has_content=True
[19:56:00] [sandbox] Content[0].text length: 18

💡 Final Answer:
72

### Example 2: Document Search and Analysis Query

**Query:** "Search for information about renewable energy policies and summarize the key points"

**Full Log:**
```
 What do you want to solve today? → Search for information about renewable energy policies and summarize the key pointsSearch for information about renewable energy policies and summarize the key points
🔁 Step 1/3 starting...
[19:56:14] [perception] Raw output: ```json
{
  "intent": "Research and summarize information on renewable energy policies.",
  "entities": ["renewable energy policies"],
  "tool_hint": "websearch to find relevant articles and documents to summarize using documents",
  "selected_servers": ["websearch", "documents"]
}
```
result {'intent': 'Research and summarize information on renewable energy policies.', 'entities': ['renewable energy policies'], 'tool_hint': 'websearch to find relevant articles and documents to summarize using documents', 'selected_servers': ['websearch', 'documents']}
[perception] intent='Research and summarize information on renewable energy policies.' entities=['renewable energy policies'] tool_hint='websearch to find relevant articles and documents to summarize using documents' tags=[] selected_servers=['websearch', 'documents']
[19:56:15] [plan] Generated solve():
```python
async def solve():
    result = await mcp.call_tool('duckduckgo_search_results', {"input": {"query": "renewable energy policies", "max_results": 5}})
    content = parse_result(result)
    return f"FURTHER_PROCESSING_REQUIRED: {content}"
```
[plan] async def solve():
    result = await mcp.call_tool('duckduckgo_search_results', {"input": {"query": "renewable energy policies", "max_results": 5}})
    content = parse_result(result)
    return f"FURTHER_PROCESSING_REQUIRED: {content}"
[loop] Detected solve() plan — running sandboxed...
[action] 🔍 Entered run_python_sandbox()
[19:56:15] [sandbox] Executing code (first 500 chars):
async def solve():
    result = await mcp.call_tool('duckduckgo_search_results', {"input": {"query": "renewable energy policies", "max_results": 5}})
    content = parse_result(result)
    return f"FURTHER_PROCESSING_REQUIRED: {content}"...
[19:56:18] [sandbox] Tool 'duckduckgo_search_results' returned: type=<class 'mcp.types.CallToolResult'>, has_content=True
[19:56:18] [sandbox] Content[0].text length: 1846
[19:56:18] [loop] 📨 Forwarding intermediate result to next step:
Original user task: Search for information about renewable energy policies and summarize the key pointsSearch for information about renewable energy policies and summarize the key points

Your last tool produced this content:

Found 5 search results: 1. Policies and Regulations - US EPA URL: https://www.epa.gov/green-power-markets/policies-and-regulations Summary: This page describes the patchwork of federal, state, and localpoliciesand regulations pertaining torenewableenergysystems that impact project development. 2. Renewables Under the New Administration: Navigating an Uncertain ... URL: https://www.morganlewis.com/pubs/2025/06/renewables-under-the-new-administration-navigating-an-uncertain-roadmap Summary: Recent policy shifts at the federal level have introduced significant variability to the USrenewableenergysector. While demand for cleanenergycontinues to grow, executive orders, regulatory changes, and evolving legislative priorities are reshaping the landscape for project development and investment. 3. Federal Renewable Energy Policy Shifts in 2025: What Developers Need to ... URL: https://www.transect.com/blog/federal-renewable-energy-policy-shifts-in-2025-what-developers-need-to-know Summary: Federal policy shifts in 2025 create challenges and opportunities forrenewableenergydevelopers, impacting permitting, financing, and siting across the U.S. 4. Renewable Energy Policies and Regulations Worldwide URL: https://energyevolutionconference.com/renewable-energy-policies-regulations/ Summary: Explore globalrenewableenergypoliciesand regulations shaping the future of sustainability. Learn how countries promote cleanenergy& combat climate change. 5. Clean Energy and Renewable Portfolio Standards | State Climate Policy ... URL: https://www.climatepolicydashboard.org/policies/electricity/clean-energy-standard Summary: An overview of CleanEnergyandRenewablePortfolio Standards across 50 U.S. States, with state-by-state policy progress, key resources, and model rules.     

TASK: Summarize this content into key points. Return a FINAL_ANSWER with:
- Bullet points (use • or -)
- Clear, concise key points
- Format: FINAL_ANSWER: • Point 1\n• Point 2\n• Point 3

DO NOT call any tools. Just analyze and summarize the content provided above.


[19:56:18] [loop] 🔁 Continuing based on FURTHER_PROCESSING_REQUIRED — Step 1 continues...
🔁 Step 2/3 starting...
[19:56:18] [heuristics] Query modified: Original user task: Search for information about r... -> Original user task: Search for information about r...
[19:56:19] [perception] Raw output: ```json
{
  "intent": "Summarize search results about renewable energy policies.",
  "entities": ["renewable energy policies", "federal policy shifts", "US EPA", "state climate policy"],
  "tool_hint": null,
  "selected_servers": ["documents"]
}
```
result {'intent': 'Summarize search results about renewable energy policies.', 'entities': ['renewable energy policies', 'federal policy shifts', 'US EPA', 'state climate policy'], 'tool_hint': None, 'selected_servers': ['documents']}
[perception] intent='Summarize search results about renewable energy policies.' entities=['renewable energy policies', 'federal policy shifts', 'US EPA', 'state climate policy'] tool_hint=None tags=[] selected_servers=['documents']
[19:56:19] [loop] ℹ️ No tools needed - processing provided content (summarize/analyze)
[19:56:21] [plan] Generated solve():
```python
async def solve():
    return f"FINAL_ANSWER: • Federal, state, and local policies and regulations impact renewable energy project development in the US.\n• Recent federal policy shifts are creating uncertainty in the US renewable energy sector.\n• These shifts affect permitting, financing, and siting of renewable energy projects.\n• Global renewable energy policies are shaping the future of sustainability and combating climate change.\n• Clean Energy and Renewable Portfolio Standards vary across the 50 US states."
```
[plan] async def solve():
    return f"FINAL_ANSWER: • Federal, state, and local policies and regulations impact renewable energy project development in the US.\n• Recent federal policy shifts are creating uncertainty in the US renewable energy sector.\n• These shifts affect permitting, financing, and siting of renewable energy projects.\n• Global renewable energy policies are shaping the future of sustainability and combating climate change.\n• Clean Energy and Renewable Portfolio Standards vary across the 50 US states."
[loop] Detected solve() plan — running sandboxed...
[action] 🔍 Entered run_python_sandbox()
[19:56:21] [sandbox] Executing code (first 500 chars):
async def solve():
    return f"FINAL_ANSWER: • Federal, state, and local policies and regulations impact renewable energy project development in the US.\n• Recent federal policy shifts are creating uncertainty in the US renewable energy sector.\n• These shifts affect permitting, financing, and siting of renewable energy projects.\n• Global renewable energy policies are shaping the future of sustainability and combating climate change.\n• Clean Energy and Renewable Portfolio Standards vary acros...

💡 Final Answer:
• Federal, state, and local policies and regulations impact renewable energy project development in the US. 
• Recent federal policy shifts are creating uncertainty in the US renewable energy sector. 
• These shifts affect permitting, financing, and siting of renewable energy projects. 
• Global renewable energy policies are shaping the future of sustainability and combating climate change.
• Clean Energy and Renewable Portfolio Standards vary across the 50 US states.

### Example 3: Web Search and Content Extraction Query

**Query:** "Extract and analyze the main topics from https://theschoolof.ai/"

**Full Log:**
```
🧑 What do you want to solve today? → Extract and analyze the main topics from https://theschoolof.ai/
🔁 Step 1/3 starting...
[19:56:44] [perception] Raw output: ```json
{
  "intent": "Extract and analyze content from a specific URL.",
  "entities": ["https://theschoolof.ai/"],
  "tool_hint": "webpage extraction and topic analysis",
  "selected_servers": ["websearch", "documents"]
}
```
result {'intent': 'Extract and analyze content from a specific URL.', 'entities': ['https://theschoolof.ai/'], 'tool_hint': 'webpage extraction and topic analysis', 'selected_servers': ['websearch', 'documents']}
[perception] intent='Extract and analyze content from a specific URL.' entities=['https://theschoolof.ai/'] tool_hint='webpage extraction and topic analysis' tags=[] selected_servers=['websearch', 'documents']
⚠️ Rate limit exceeded (429). Waiting 60.0s before retry 1/3...
[19:57:47] [plan] Generated solve():
```python
async def solve():
    result = await mcp.call_tool('download_raw_html_from_url', {"input": {"url": "https://theschoolof.ai/"}})
    content = result.content[0].text if result.content else ""
    return f"FURTHER_PROCESSING_REQUIRED: {content}"
```
[plan] async def solve():
    result = await mcp.call_tool('download_raw_html_from_url', {"input": {"url": "https://theschoolof.ai/"}})
    content = result.content[0].text if result.content else ""
    return f"FURTHER_PROCESSING_REQUIRED: {content}"
[loop] Detected solve() plan — running sandboxed...
[action] 🔍 Entered run_python_sandbox()
[19:57:47] [sandbox] Executing code (first 500 chars):
async def solve():
    result = await mcp.call_tool('download_raw_html_from_url', {"input": {"url": "https://theschoolof.ai/"}})
    content = result.content[0].text if result.content else ""
    return f"FURTHER_PROCESSING_REQUIRED: {content}"...
[19:57:48] [sandbox] Tool 'download_raw_html_from_url' returned: type=<class 'mcp.types.CallToolResult'>, has_content=True
[19:57:48] [sandbox] Content[0].text length: 8156
[19:57:48] [loop] 📨 Forwarding intermediate result to next step:
Original user task: Extract and analyze the main topics from https://theschoolof.ai/

Your last tool produced this content:

{"result": "The School of AI Welcome to THESCHOOLOF AI Intro About Programs Join Intro An effort to create a state of art institution for AI study and research. A disciplined and structured approach to learning and implementing the fundamentals of AIML. About TSAI provides a profound understanding of AI for Visual Comprehension and NLP Problems through bleeding edge concepts, and an amazing peer group to learn with. Programs Three unique and challenging semester-style programs Through ERA, EAG and EPAi, TSAI has trained more than 7000 students! In ERA we learn how to \"actually\" train LLMs from scratch. EAG focuses on Agents, and EPAi is a comprehensive course focusing on Python and programming for AI! Details - Extensive AI Agents Program EAG - V2 (AI Agents) Registrations are open now! EAG V1 saw our highest enrollment ever! More than 400 students from 15 countries took part in it!. This comprehensive 20-session course equips students to build advanced Agentic AI systems, capable of autonomous decision-making, task orchestration, and seamless interaction within complex web environments. Unlike traditional AI programs, this curriculum focuses on designing browser-based agents that leverage the latest advancements in LLMs, retrieval-augmented systems, and multi-agent collaboration, preparing students to lead the development of next-generation AI solutions. This course does not teach how to use langChain, langGraph, crew.ai or n8n! This course is about making such, and more advanced multi-model Agentic Frameworks and Agents on top of them. The EAG course offers a revolutionary approach to learning AI, enabling students to design agents that mirror human-like intelligence in interacting with the web, bridging the gap between theory and application.Registrations are closed now. Registrations for EAG V3 are scheduled to be in April 2026. EAG V2 Lecture Title Session 1: Transformers & LLM Foundations \u2013 Understand how transformer architecture and large language models work at their core. Session 2: Modern LLM Internals + SFT Basics \u2013 Explore pretraining internals, scaling rules, and the fundamentals of supervised fine-tuning. Session 3: What Makes an Agent? Reactive vs. Proactive \u2013 Learn the traits and trade-offs between reactive and goal-driven AI agents. Session 4: Tool Protocols 101 (HTTP, JSON-RPC, schema validation) \u2013 Master communication protocols and schema-driven tool integration. Session 5: Model Context Protocol & Interop Standards \u2013 Discover MCP and other standards enabling cross-platform agent interoperability. Session 6: Planning & Reasoning (CoT, Structured, Self-Consistency) \u2013 Apply structured reasoning techniques for accurate, multi-step problem-solving. Session 7: Agent Architecture \u2013 Cognitive Layers \u2013 Design agents with perception, memory, and decision-making layers for robust performance. Session 8: RAG & Memory Architectures \u2013 Build agents with retrieval-augmented generation and efficient memory management. Session 9: Tool Use: Secure API & Command Execution \u2013 Enable agents to safely execute APIs and commands within controlled environments. Session 10:Hybrid Planning (AI + Heuristics) \u2013 Combine LLM reasoning with traditional heuristics for optimal decision-making. Session 11:Multi-Agent Systems & Meta-Agents \u2013 Coordinate multiple agents to work collaboratively on complex goals. Session 12:Environment-Aware Agents (Web + Desktop) \u2013 Equip agents to perceive and act within both browser and desktop environments. Session 13:Perception: Multimodal Input Handling \u2013 Integrate text, image, audio, and other modalities into unified agent perception. Session 14:Sandboxed Execution & Safety \u2013 Run agent actions in secure sandboxes to ensure reliability and prevent harm. Session 15:Scaling Agents Across Machines \u2013 Architect systems for distributed, multi-machine agent deployment. Session 16:Intelligent Goal Interpretation \u2013 Train agents to interpret, refine, and align with human goals accurately. Session 17:Managing Uncertainty & Error Recovery \u2013 Handle ambiguity and implement robust error-correction strategies. Session 18:Agent Debugging & Introspection \u2013 Monitor, debug, and refine agents through introspection and trace analysis. Session 19:Evaluation & Continuous Improvement \u2013 Measure agent performance and iterate for ongoing enhancement. Session 20:Capstone: Autonomous Environment-Aware Agent \u2013 Design, build, and demo a fully autonomous, environment-aware AI agent. EAG V1 Lecture Title Session 1: Foundations of the Transformer Architecture - A deep dive into the self-attention mechanism and why Transformers revolutionized NLP. Session 2: Modern Language Model Internals - Examines pre-training objectives, parameter scaling, and advanced fine-tuning for LLMs. Session 3: Introduction to Agentic AI - Overviews AI agents that plan, reason, and take actions beyond simple text g... [TRUNCATED]

TASK: Analyze and extract the main topics from this content. Return a FINAL_ANSWER with:
- Main topics listed clearly (use • or numbered list)
- Format: FINAL_ANSWER: Main Topics:\n• Topic 1\n• Topic 2\n• Topic 3

DO NOT call any tools. Just analyze the content and extract the main topics.


[19:57:48] [loop] 🔁 Continuing based on FURTHER_PROCESSING_REQUIRED — Step 1 continues...
🔁 Step 2/3 starting...
[19:57:48] [heuristics] Query modified: Original user task: Extract and analyze the main t... -> Original user task: Extract and analyze the main t...
[19:57:50] [perception] Raw output: ```json
{
  "intent": "Extract and analyze the main topics from a given text content.",
  "entities": ["main topics", "content analysis"],
  "tool_hint": null,
  "selected_servers": ["documents"]
}
```
result {'intent': 'Extract and analyze the main topics from a given text content.', 'entities': ['main topics', 'content analysis'], 'tool_hint': None, 'selected_servers': ['documents']}
[perception] intent='Extract and analyze the main topics from a given text content.' entities=['main topics', 'content analysis'] tool_hint=None tags=[] selected_servers=['documents']
[19:57:50] [loop] ℹ️ No tools needed - processing provided content (summarize/analyze)
[19:57:52] [plan] Generated solve():
```python
async def solve():
    return f"FINAL_ANSWER: Main Topics:\n• AI Education and Research\n• Agentic AI Systems\n• Large Language Models (LLMs)\n• Tool Use and Integration\n• Multi-Agent Systems\n• Environment-Aware Agents\n• AI Agent Architecture\n• Safety and Security\n• AI Agent Evaluation and Improvement"
```
```
[plan] async def solve():
[plan] async def solve():
    return f"FINAL_ANSWER: Main Topics:\n• AI Education and Research\n• Agentic AI Systems\n• Large Language Models (LLMs)\n• Tool Use and Integration\n• Multi-Agent Systems\n• Environment-Aware Agents\n• AI Agent Architecture\n• Safety and Security\n• AI Agent Evaluation and Improvement"
[loop] Detected solve() plan — running sandboxed...
[action] 🔍 Entered run_python_sandbox()
[19:57:52] [sandbox] Executing code (first 500 chars):
async def solve():
    return f"FINAL_ANSWER: Main Topics:\n• AI Education and Research\n• Agentic AI Systems\n• Large Language Models (LLMs)\n• Tool Use and Integration\n• Multi-Agent Systems\n• Environment-Aware Agents\n• AI Agent Architecture\n• Safety and Security\n• AI Agent Evaluation and Improvement"...

💡 Final Answer:
Main Topics: 
• AI Education and Research
 • Agentic AI Systems 
 • Large Language Models (LLMs) 
 • Tool Use and Integration • Multi-Agent Systems 
 • Environment-Aware Agents 
 • AI Agent Architecture 
 • Safety and Security 
 • AI Agent Evaluation and Improvement
```

## Key Features

### 1. **Heuristic-Based Safety**
- Automatic banned word filtering
- Profanity removal
- Sensitive information redaction
- Query validation and enhancement

### 2. **Historical Context Integration**
- Indexes all past conversations
- Semantic search for relevant history
- Provides context to LLM for better decisions
- Learns from successful tool usage patterns

### 3. **Flexible Planning Strategies**
- **Conservative**: One tool at a time, safer
- **Exploratory**: Multiple options, more flexible
- Memory fallback on failures
- Force replan with different tools

### 4. **Robust Error Handling**
- Lifelines per step (retry mechanism)
- Tool failure tracking
- Memory fallback to successful tools
- Graceful degradation

## File Structure

```
.
├── agent.py                          # Main entry point
├── core/
│   ├── context.py                    # AgentContext, AgentProfile
│   ├── loop.py                       # Main agent loop
│   ├── session.py                    # MCP integration
│   └── strategy.py                   # Planning strategies
├── modules/
│   ├── action.py                     # Sandbox execution
│   ├── decision.py                  # Legacy decision (unused)
│   ├── heuristics.py                # 10 heuristics
│   ├── historical_conversation.py   # Conversation indexing
│   ├── memory.py                     # Memory management
│   ├── model_manager.py             # LLM integration
│   ├── perception.py                # Query perception
│   └── tools.py                      # Tool utilities
├── prompts/
│   ├── decision_prompt_conservative.txt  # 277 words (reduced from 729)
│   ├── decision_prompt_exploratory_parallel.txt
│   ├── decision_prompt_exploratory_sequential.txt
│   └── perception_prompt.txt
├── config/
│   ├── profiles.yaml                 # Agent configuration
│   └── models.json                   # LLM model configs
└── memory/
    └── historical_conversation_store.json  # Conversation index
```

## Running the Agent

```bash
python agent.py
```

The agent will:
1. Initialize MCP servers
2. Wait for user input
3. Process query through full pipeline
4. Return final answer or request further processing

Commands:
- `exit`: Quit the agent
- `new`: Start a new session

## Decision Prompt Optimization

The decision prompt was reduced from **729 words to 277 words** (62% reduction) while maintaining:
- All core functionality
- Tool calling syntax with safe parsing (`parse_result()` helper)
- Result parsing rules
- FINAL_ANSWER vs FURTHER_PROCESSING_REQUIRED logic
- Three comprehensive examples (Math, Search, Summarize)
- Support for decimal exponents (e.g., square root using `power(144, 0.5)`)

**Word Count:** **277 words** (target: <300 words) ✅

**File:** `prompts/decision_prompt_conservative.txt`

The prompt includes:
- Task description and rules
- Safe result parsing instructions
- Helper function usage (`parse_result()`)
- Three complete examples covering different use cases
- Formatting requirements for final answers

## Historical Conversation Indexing

The system automatically:
1. Indexes completed sessions
2. Extracts query, answer, tools used, entities
3. Stores in `memory/historical_conversation_store.json`
4. Provides semantic search for relevant past conversations
5. Enhances decision prompts with historical context

## Heuristics File

See `modules/heuristics.py` for all 10 heuristics:
- Banned word removal
- Profanity filtering
- Sensitive info redaction
- Whitespace normalization
- Length limiting
- Entity extraction
- Query validation
- Result sanitization
- Context enhancement

## Recent Updates

### Power Tool Enhancement
- Updated `PowerInput` to accept `float` for exponent `b` (supports decimal exponents like 0.5 for square root)
- Updated `PowerOutput` to return `float` (handles decimal results)
- Enables calculations like `power(144, 0.5)` for square root operations

### Safe Result Parsing
- Added `parse_result()` helper function in sandbox for safe MCP result parsing
- Handles empty content, different response formats, and JSON parsing errors
- Prevents "Expecting value: line 1 column 1 (char 0)" errors

### Rate Limiting
- Automatic rate limiting for Gemini API (5 seconds between calls)
- Automatic retry with exponential backoff on 429 errors
- Extracts retry delay from error messages for smart waiting

## License

[Your License Here]

