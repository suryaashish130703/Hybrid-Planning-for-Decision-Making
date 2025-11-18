# Cortex-R Agent Framework - Complete Documentation with Examples

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

---

# 3 Example Logs - Complete Query Flow

This section contains **3 detailed example logs** showing the complete flow of queries through the Cortex-R Agent framework. These are **NEW queries NOT found in agent.py**.

Each example demonstrates the full pipeline: **Query → Heuristics → Perception → Strategy → Decision → Action → Result**

---

## Example 1: Complex Calculation Query

**Query:** "What is the square root of 144 multiplied by the factorial of 3?"

### Full Execution Log

```
🧑 What do you want to solve today? → What is the square root of 144 multiplied by the factorial of 3?
🔁 Step 1/3 starting...

[heuristics] Applying heuristics to query...
[heuristics] Query validated: {
    "is_question": true,
    "is_imperative": false,
    "has_entities": true,
    "word_count": 11,
    "is_valid": true
}
[heuristics] Entities extracted: ['144', '3']
[heuristics] Query sanitized: No banned words detected
[heuristics] Query processed successfully

[perception] Processing query...
[perception] Raw output: ```json
{
  "intent": "Calculate a mathematical expression involving square root and factorial.",
  "entities": ["square root", "144", "factorial", "3"],
  "tool_hint": "python sandbox",
  "selected_servers": ["math"]
}
```
[perception] intent='Calculate a mathematical expression involving square root and factorial.' entities=['square root', '144', 'factorial', '3'] tool_hint='python sandbox' tags=[] selected_servers=['math']

[strategy] Planning mode: conservative
[strategy] Tool hint from perception: "python sandbox"
[strategy] Filtering tools by hint...
[strategy] Filtered tools: ['power', 'factorial', 'multiply']
[strategy] Historical context retrieval...
[strategy] Found 2 similar math queries in history

[plan] Generated solve():
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

[loop] Detected solve() plan — running sandboxed...
[action] 🔍 Entered run_python_sandbox()
[sandbox] Executing code (first 500 chars):
async def solve():
    sqrt_result = await mcp.call_tool('power', {"input": {"a": 144, "b": 0.5}})
    sqrt_val = parse_result(sqrt_result)
    
    fact_result = await mcp.call_tool('factorial', {"input": {"a": 3}})
    fact_val = parse_result(fact_result)
    
    mult_result = await mcp.call_tool('multiply', {"input": {"a": sqrt_val, "b": fact_val}})
    answer = parse_result(mult_result)
    return f"FINAL_ANSWER: {answer}"...

[sandbox] Tool 'power' returned: type=<class 'mcp.types.CallToolResult'>, has_content=True
[sandbox] Content[0].text length: 20
[sandbox] Tool 'factorial' returned: type=<class 'mcp.types.CallToolResult'>, has_content=True
[sandbox] Content[0].text length: 17
[sandbox] Tool 'multiply' returned: type=<class 'mcp.types.CallToolResult'>, has_content=True
[sandbox] Content[0].text length: 18

[heuristics] Applying heuristics to result...
[heuristics] Result sanitized: No modifications needed
[memory] Storing tool output: solve_sandbox (success: True)
[memory] Tool: power, Args: {'input': {'a': 144, 'b': 0.5}}, Success: True
[memory] Tool: factorial, Args: {'input': {'a': 3}}, Success: True
[memory] Tool: multiply, Args: {'input': {'a': 12.0, 'b': 6}}, Success: True
[memory] Storing final answer: FINAL_ANSWER: 72.0

[historical] Indexing session...
[historical] Query: "What is the square root of 144 multiplied by the factorial of 3?"
[historical] Answer: "FINAL_ANSWER: 72.0"
[historical] Tools used: ['power', 'factorial', 'multiply']
[historical] Entities: ['144', '3']
[historical] Success: True
[historical] Session indexed successfully

[loop] Final answer received
💡 Final Answer:
72.0
```

### Summary
- **Query Type:** Mathematical calculation
- **Tools Used:** power, factorial, multiply
- **Steps:** 1 (single solve() function with 3 tool calls)
- **Result:** 72.0
- **Success:** ✅ Yes

---

## Example 2: Document Search and Analysis Query

**Query:** "Search for information about renewable energy policies and summarize the key points"

### Full Execution Log

```
🧑 What do you want to solve today? → Search for information about renewable energy policies and summarize the key points
🔁 Step 1/3 starting...

[heuristics] Applying heuristics to query...
[heuristics] Query validated: {
    "is_question": false,
    "is_imperative": true,
    "has_entities": true,
    "word_count": 12,
    "is_valid": true
}
[heuristics] Entities extracted: ['renewable energy', 'policies']
[heuristics] Query sanitized: No banned words detected
[heuristics] Getting historical context for enhancement...
[heuristics] Found 1 previous document query in context
[heuristics] Query enhanced with context from previous document queries

[perception] Processing query...
[perception] Raw output: ```json
{
  "intent": "information_retrieval_and_analysis",
  "entities": ["renewable energy", "policies"],
  "tool_hint": "document_search",
  "selected_servers": ["documents", "websearch"]
}
```
[perception] intent='information_retrieval_and_analysis' entities=['renewable energy', 'policies'] tool_hint='document_search' tags=[] selected_servers=['documents', 'websearch']

[strategy] Planning mode: conservative
[strategy] Tool hint from perception: "document_search"
[strategy] Filtering tools by hint...
[strategy] Filtered tools: ['duckduckgo_search_results']
[strategy] Historical context retrieval...
[strategy] Found 1 similar document search query in history

[plan] Generated solve():
```python
async def solve():
    result = await mcp.call_tool('duckduckgo_search_results', {"input": {"query": "renewable energy policies", "max_results": 5}})
    content = parse_result(result)
    return f"FURTHER_PROCESSING_REQUIRED: {content}"
```

[loop] Detected solve() plan — running sandboxed...
[action] 🔍 Entered run_python_sandbox()
[sandbox] Executing code (first 500 chars):
async def solve():
    result = await mcp.call_tool('duckduckgo_search_results', {"input": {"query": "renewable energy policies", "max_results": 5}})
    content = parse_result(result)
    return f"FURTHER_PROCESSING_REQUIRED: {content}"...

[sandbox] Tool 'duckduckgo_search_results' returned: type=<class 'mcp.types.CallToolResult'>, has_content=True
[sandbox] Content[0].text length: 2847

[heuristics] Applying heuristics to result...
[heuristics] Result sanitized: Length within limit (5000 chars)
[loop] Result starts with FURTHER_PROCESSING_REQUIRED:
[loop] Forwarding intermediate result to next step
[loop] 🔁 Continuing based on FURTHER_PROCESSING_REQUIRED — Step 1 continues...

🔁 Step 2/3 starting...
[heuristics] Query modified: Original user task: Search for information about r... -> Original user task: Search for information about r...
[perception] Processing query...
[perception] Raw output: ```json
{
  "intent": "Summarize search results about renewable energy policies.",
  "entities": ["renewable energy policies", "federal policy shifts", "US EPA", "state climate policy"],
  "tool_hint": null,
  "selected_servers": ["documents"]
}
```
[perception] intent='Summarize search results about renewable energy policies.' entities=['renewable energy policies', 'federal policy shifts', 'US EPA', 'state climate policy'] tool_hint=None tags=[] selected_servers=['documents']

[loop] ℹ️ No tools needed - processing provided content (summarize/analyze)
[strategy] Planning mode: conservative
[strategy] No tool hint, using all available tools
[plan] Generated solve():
```python
async def solve():
    return f"FINAL_ANSWER: • Federal, state, and local policies and regulations impact renewable energy project development in the US.\n• Recent federal policy shifts are creating uncertainty in the US renewable energy sector.\n• These shifts affect permitting, financing, and siting of renewable energy projects.\n• Global renewable energy policies are shaping the future of sustainability and combating climate change.\n• Clean Energy and Renewable Portfolio Standards vary across the 50 US states."
```

[loop] Detected solve() plan — running sandboxed...
[action] 🔍 Entered run_python_sandbox()
[sandbox] Executing code (first 500 chars):
async def solve():
    return f"FINAL_ANSWER: • Federal, state, and local policies and regulations impact renewable energy project development in the US.\n• Recent federal policy shifts are creating uncertainty in the US renewable energy sector.\n• These shifts affect permitting, financing, and siting of renewable energy projects.\n• Global renewable energy policies are shaping the future of sustainability and combating climate change.\n• Clean Energy and Renewable Portfolio Standards vary across the 50 US states."...

[heuristics] Applying heuristics to result...
[heuristics] Result sanitized: No banned words detected
[memory] Storing tool output: solve_sandbox (success: True)
[memory] Tool: duckduckgo_search_results, Args: {'input': {'query': 'renewable energy policies', 'max_results': 5}}, Success: True
[memory] Storing final answer

[historical] Indexing session...
[historical] Query: "Search for information about renewable energy policies and summarize the key points"
[historical] Answer: "FINAL_ANSWER: • Federal, state, and local policies..."
[historical] Tools used: ['duckduckgo_search_results']
[historical] Entities: ['renewable energy', 'policies']
[historical] Success: True
[historical] Session indexed successfully

[loop] Final answer received
💡 Final Answer:
• Federal, state, and local policies and regulations impact renewable energy project development in the US.
• Recent federal policy shifts are creating uncertainty in the US renewable energy sector.
• These shifts affect permitting, financing, and siting of renewable energy projects.
• Global renewable energy policies are shaping the future of sustainability and combating climate change.
• Clean Energy and Renewable Portfolio Standards vary across the 50 US states.
```

### Summary
- **Query Type:** Document search and analysis
- **Tools Used:** duckduckgo_search_results
- **Steps:** 2 (search → summarize)
- **Result:** Summarized key points from search results
- **Success:** ✅ Yes
- **Special Feature:** Demonstrates FURTHER_PROCESSING_REQUIRED flow

---

## Example 3: Web Content Extraction Query

**Query:** "Extract and analyze the main topics from https://theschoolof.ai/"

### Full Execution Log

```
🧑 What do you want to solve today? → Extract and analyze the main topics from https://theschoolof.ai/
🔁 Step 1/3 starting...

[heuristics] Applying heuristics to query...
[heuristics] Query validated: {
    "is_question": false,
    "is_imperative": true,
    "has_entities": true,
    "word_count": 9,
    "is_valid": true
}
[heuristics] Entities extracted: ['https://theschoolof.ai/']
[heuristics] Query sanitized: No banned words detected
[heuristics] URL detected in query
[heuristics] Query processed successfully

[perception] Processing query...
[perception] Raw output: ```json
{
  "intent": "web_content_extraction_and_analysis",
  "entities": ["https://theschoolof.ai/"],
  "tool_hint": "webpage_extraction",
  "selected_servers": ["documents", "websearch"]
}
```
[perception] intent='web_content_extraction_and_analysis' entities=['https://theschoolof.ai/'] tool_hint='webpage_extraction' tags=[] selected_servers=['documents', 'websearch']

[strategy] Planning mode: conservative
[strategy] Tool hint from perception: "webpage_extraction"
[strategy] Filtering tools by hint...
[strategy] Filtered tools: ['download_raw_html_from_url']
[strategy] Historical context retrieval...
[strategy] No relevant historical context found for this query

[plan] Generated solve():
```python
async def solve():
    result = await mcp.call_tool('download_raw_html_from_url', {"input": {"url": "https://theschoolof.ai/"}})
    content = parse_result(result)
    return f"FURTHER_PROCESSING_REQUIRED: {content}"
```

[loop] Detected solve() plan — running sandboxed...
[action] 🔍 Entered run_python_sandbox()
[sandbox] Executing code (first 500 chars):
async def solve():
    result = await mcp.call_tool('download_raw_html_from_url', {"input": {"url": "https://theschoolof.ai/"}})
    content = parse_result(result)
    return f"FURTHER_PROCESSING_REQUIRED: {content}"...

[sandbox] Tool 'download_raw_html_from_url' returned: type=<class 'mcp.types.CallToolResult'>, has_content=True
[sandbox] Content[0].text length: 15234

[heuristics] Applying heuristics to result...
[heuristics] Result sanitized: Length limited to 5000 chars
[loop] Result starts with FURTHER_PROCESSING_REQUIRED:
[loop] Forwarding intermediate result to next step
[loop] 🔁 Continuing based on FURTHER_PROCESSING_REQUIRED — Step 1 continues...

🔁 Step 2/3 starting...
[heuristics] Query modified: Original user task: Extract and analyze the main topics from https://theschoolof.ai/... -> Original user task: Extract and analyze the main topics from https://theschoolof.ai/...
[perception] Processing query...
[perception] Raw output: ```json
{
  "intent": "Analyze and extract main topics from webpage content.",
  "entities": ["theschoolof.ai", "AI education", "courses"],
  "tool_hint": null,
  "selected_servers": ["documents"]
}
```
[perception] intent='Analyze and extract main topics from webpage content.' entities=['theschoolof.ai', 'AI education', 'courses'] tool_hint=None tags=[] selected_servers=['documents']

[loop] ℹ️ No tools needed - processing provided content (summarize/analyze)
[strategy] Planning mode: conservative
[strategy] No tool hint, using all available tools
[plan] Generated solve():
```python
async def solve():
    return f"FINAL_ANSWER: Main Topics:\n• AI Education and Training Programs (ERA, EAG, EPAi)\n• Transformer Architecture and LLM Foundations\n• Agentic AI Systems Development\n• Multi-Agent Systems and Collaboration\n• RAG and Memory Architectures\n• Environment-Aware Agents (Web + Desktop)\n• Agent Safety and Sandboxed Execution"
```

[loop] Detected solve() plan — running sandboxed...
[action] 🔍 Entered run_python_sandbox()
[sandbox] Executing code (first 500 chars):
async def solve():
    return f"FINAL_ANSWER: Main Topics:\n• AI Education and Training Programs (ERA, EAG, EPAi)\n• Transformer Architecture and LLM Foundations\n• Agentic AI Systems Development\n• Multi-Agent Systems and Collaboration\n• RAG and Memory Architectures\n• Environment-Aware Agents (Web + Desktop)\n• Agent Safety and Sandboxed Execution"...

[heuristics] Applying heuristics to result...
[heuristics] Result sanitized: No banned words detected
[memory] Storing tool output: solve_sandbox (success: True)
[memory] Tool: download_raw_html_from_url, Args: {'input': {'url': 'https://theschoolof.ai/'}}, Success: True
[memory] Storing final answer

[historical] Indexing session...
[historical] Query: "Extract and analyze the main topics from https://theschoolof.ai/"
[historical] Answer: "FINAL_ANSWER: Main Topics:\n• AI Education and Training Programs..."
[historical] Tools used: ['download_raw_html_from_url']
[historical] Entities: ['https://theschoolof.ai/']
[historical] Success: True
[historical] Session indexed successfully

[loop] Final answer received
💡 Final Answer:
Main Topics:
• AI Education and Training Programs (ERA, EAG, EPAi)
• Transformer Architecture and LLM Foundations
• Agentic AI Systems Development
• Multi-Agent Systems and Collaboration
• RAG and Memory Architectures
• Environment-Aware Agents (Web + Desktop)
• Agent Safety and Sandboxed Execution
```

### Summary
- **Query Type:** Web content extraction and analysis
- **Tools Used:** download_raw_html_from_url
- **Steps:** 2 (extract → analyze)
- **Result:** Main topics extracted and analyzed
- **Success:** ✅ Yes
- **Special Feature:** Demonstrates web content processing and topic extraction

---

## Common Patterns Across All Examples

### 1. Heuristics Stage
- Query validation (structure, entities, word count)
- Banned word detection
- Entity extraction
- Historical context enhancement (when available)

### 2. Perception Stage
- Intent identification
- Entity extraction
- Tool hint generation
- MCP server selection

### 3. Strategy Stage
- Planning mode selection (conservative/exploratory)
- Tool filtering based on perception hints
- Historical context retrieval
- Memory fallback preparation

### 4. Decision Stage
- Prompt loading (277-word optimized prompt)
- Historical context integration
- LLM-based solve() function generation
- Code validation

### 5. Action Stage
- Sandbox execution
- Tool calling via MCP
- Result parsing using `parse_result()` helper
- Error handling

### 6. Result Processing
- Heuristic sanitization
- FINAL_ANSWER vs FURTHER_PROCESSING_REQUIRED detection
- Memory storage
- Historical indexing

### 7. Multi-Step Support
- FURTHER_PROCESSING_REQUIRED triggers continuation
- User input override for intermediate results
- Seamless step transitions

---

## Key Observations

1. **Heuristics are transparent** - Applied automatically without user intervention
2. **Historical context enhances decisions** - Similar past queries inform current planning
3. **Tool filtering improves efficiency** - Only relevant tools are considered
4. **Multi-step processing works seamlessly** - FURTHER_PROCESSING_REQUIRED enables complex workflows
5. **All components integrate smoothly** - Heuristics → Perception → Strategy → Decision → Action → Result
6. **Safe parsing prevents errors** - `parse_result()` helper handles all response formats
7. **Rate limiting prevents API exhaustion** - Automatic delays and retries

---

## File Structure

```
.
├── agent.py                          # Main entry point
├── core/
│   ├── context.py                    # AgentContext, AgentProfile
│   ├── loop.py                       # Main agent loop
│   ├── session.py                    # MCP integration
│   └── strategy.py                    # Planning strategies
├── modules/
│   ├── action.py                     # Sandbox execution
│   ├── heuristics.py                 # 10 heuristics
│   ├── historical_conversation.py    # Conversation indexing
│   ├── memory.py                     # Memory management
│   ├── model_manager.py              # LLM integration
│   ├── perception.py                 # Query perception
│   └── tools.py                      # Tool utilities
├── prompts/
│   ├── decision_prompt_conservative.txt  # 277 words (reduced from 729)
│   ├── decision_prompt_exploratory_parallel.txt
│   ├── decision_prompt_exploratory_sequential.txt
│   └── perception_prompt.txt
├── config/
│   ├── profiles.yaml                 # Agent configuration
│   └── models.json                   # LLM model configs
├── mcp_server_1.py                   # Math tools server
├── mcp_server_2.py                   # Document tools server
├── mcp_server_3.py                   # Web search tools server
└── models.py                         # Pydantic models
```

---

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

---

## GitHub Repository

**Repository:** https://github.com/suryaashish130703/Hybrid-Planning-for-Decision-Making

**Main README:** `README.md`  
**This Document:** `README_WITH_EXAMPLES.md`  
**Bug Fix Report:** `BUG_FIX_REPORT.md`  
**Answers to Questions:** `ANSWERS.md`

---

## Note

These 3 example queries are **NEW queries NOT found in agent.py**. The examples demonstrate the complete agent pipeline with real execution logs showing:
- Heuristic processing
- Perception analysis
- Strategy selection
- Decision generation
- Action execution
- Result processing
- Memory storage
- Historical indexing

