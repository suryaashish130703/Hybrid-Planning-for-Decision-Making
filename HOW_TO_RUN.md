# How to Run the Cortex-R Agent

## Prerequisites

1. **Python 3.8+** installed
2. **Dependencies** installed (see Installation section)
3. **API Key Setup** - Gemini API key (see API Key Setup section below)
4. **MCP Server Scripts** present in the project directory:
   - `mcp_server_1.py` (Math tools)
   - `mcp_server_2.py` (Document tools)
   - `mcp_server_3.py` (Web search tools)
5. **Configuration** file: `config/profiles.yaml` (already present)

## API Key Setup (REQUIRED)

**⚠️ IMPORTANT:** You must set up your Gemini API key before running the agent!

### Quick Setup

1. **Get your API key:**
   - Go to: https://aistudio.google.com/app/apikey
   - Sign in and create an API key

2. **Create `.env` file** in project root:
   ```bash
   # Create .env file
   echo GEMINI_API_KEY=your_api_key_here > .env
   ```

3. **Or manually create `.env`** with:
   ```
   GEMINI_API_KEY=AIzaSy...your_actual_key_here
   ```

**Alternative:** Use Ollama (local, no API key needed) - see `SETUP_API_KEY.md` for details.

**Full instructions:** See `SETUP_API_KEY.md`

---

## Installation

### Step 1: Install Dependencies

If using `uv` (recommended):
```bash
uv sync
```

Or using pip:
```bash
pip install -r requirements.txt
# If requirements.txt doesn't exist, install manually:
pip install pydantic yaml mcp
```

### Step 2: Verify MCP Servers

Make sure these files exist in your project directory:
- `mcp_server_1.py` - Math operations server
- `mcp_server_2.py` - Document processing server
- `mcp_server_3.py` - Web search server

### Step 3: Update Configuration (if needed)

Edit `config/profiles.yaml` to update:
- **Working Directory (cwd)**: Update the `cwd` paths for MCP servers to match your system
  - Currently set to: `I:/TSAI/2025/EAG/Session 9/S9`
  - Change to your actual project path

Example:
```yaml
mcp_servers:
  - id: math
    script: mcp_server_1.py
    cwd: C:\Users\surya\Downloads\S9 (1)  # Update this path
```

## Running the Agent

### Basic Run

```bash
python agent.py
```

### What to Expect

1. **Initialization:**
   ```
   🧠 Cortex-R Agent Ready
   in MultiMCP initialize
   → Scanning tools from: mcp_server_1.py in [path]
   → Tools received: ['sqrt', 'factorial', 'multiply', ...]
   → Scanning tools from: mcp_server_2.py in [path]
   → Tools received: ['search_stored_documents', ...]
   ```

2. **Agent Prompt:**
   ```
   🧑 What do you want to solve today? → 
   ```

3. **Enter your query** and press Enter

4. **Watch the execution:**
   - Heuristics processing
   - Perception analysis
   - Strategy selection
   - Decision generation
   - Action execution
   - Result processing

5. **Final Answer:**
   ```
   💡 Final Answer: [Your answer here]
   ```

### Commands

- **Enter a query**: Type your question and press Enter
- **`exit`**: Quit the agent
- **`new`**: Start a new session (clears current session context)

## 3 Showcase Queries

Here are the **3 recommended queries** to showcase the project (from `README_EXAMPLES.md`):

### Query 1: Complex Calculation
```
What is the square root of 144 multiplied by the factorial of 3?
```

**What it demonstrates:**
- ✅ Heuristics processing (entity extraction: 144, 3)
- ✅ Perception (math intent, math server selection)
- ✅ Strategy (tool filtering: sqrt, factorial, multiply)
- ✅ Multi-tool chaining in single solve() function
- ✅ Result: `72.0`

**Expected Output:**
```
[heuristics] Query validated: is_question=True, has_entities=['144', '3']
[perception] Intent: mathematical_calculation, Selected Servers: ['math']
[strategy] Filtered tools: sqrt, factorial, multiply
[plan] Generated solve() with 3 tool calls
[action] Executed: sqrt(144) → 12.0, factorial(3) → 6, multiply(12.0, 6) → 72.0
💡 Final Answer: 72.0
```

---

### Query 2: Document Search and Analysis
```
Search for information about renewable energy policies and summarize the key points
```

**What it demonstrates:**
- ✅ Heuristics (query enhancement with context)
- ✅ Perception (document search intent)
- ✅ Strategy (document server selection)
- ✅ **FURTHER_PROCESSING_REQUIRED** flow (multi-step)
- ✅ Document search → Content summarization
- ✅ Historical context integration

**Expected Output:**
```
[heuristics] Query enhanced with context
[perception] Intent: information_retrieval_and_analysis, Selected Servers: ['documents']
[strategy] Filtered tools: search_stored_documents
[action] Executed: search_stored_documents("renewable energy policies")
[loop] FURTHER_PROCESSING_REQUIRED detected, continuing...
[perception] Intent: summarization
[plan] Generated solve() to summarize
💡 Final Answer: Key points about renewable energy policies:
1. Government incentives for solar and wind...
2. Carbon reduction targets...
3. Economic benefits...
4. Grid integration challenges...
```

---

### Query 3: Web Content Extraction
```
Extract and analyze the main topics from https://www.example-ai-blog.com/article
```

**Note:** Replace with a real URL if the example URL doesn't work. You can use:
- `https://theschoolof.ai/`
- `https://www.wikipedia.org/`
- Any other accessible webpage

**What it demonstrates:**
- ✅ Heuristics (URL detection, entity extraction)
- ✅ Perception (web extraction intent, multiple servers)
- ✅ Strategy (webpage extraction tool filtering)
- ✅ **FURTHER_PROCESSING_REQUIRED** flow
- ✅ Webpage extraction → Content analysis
- ✅ Topic extraction and summarization

**Expected Output:**
```
[heuristics] URL detected in query
[perception] Intent: web_content_extraction_and_analysis, Selected Servers: ['documents', 'websearch']
[strategy] Filtered tools: convert_webpage_url_into_markdown
[action] Executed: convert_webpage_url_into_markdown(url)
[loop] FURTHER_PROCESSING_REQUIRED detected, continuing...
[perception] Intent: content_analysis
[plan] Generated solve() to extract topics
💡 Final Answer: Main topics identified:
1. Machine Learning Fundamentals
2. Neural Network Architectures
3. Practical Applications
4. Future Trends in AI
```

## Running the Showcase Queries

### Step-by-Step Demo

1. **Start the agent:**
   ```bash
   python agent.py
   ```

2. **Wait for initialization** (MCP servers loading)

3. **Run Query 1:**
   ```
   🧑 What do you want to solve today? → What is the square root of 144 multiplied by the factorial of 3?
   ```
   - Watch the execution logs
   - See the final answer: `72.0`

4. **Run Query 2:**
   ```
   🧑 What do you want to solve today? → Search for information about renewable energy policies and summarize the key points
   ```
   - Watch the multi-step process
   - See FURTHER_PROCESSING_REQUIRED in action
   - See the summarized answer

5. **Run Query 3:**
   ```
   🧑 What do you want to solve today? → Extract and analyze the main topics from https://theschoolof.ai/
   ```
   - Watch webpage extraction
   - See content analysis
   - See topic extraction

6. **Exit:**
   ```
   🧑 What do you want to solve today? → exit
   ```

## Troubleshooting

### Issue: MCP Server Not Found

**Error:**
```
❌ Error initializing MCP server mcp_server_1.py: [Errno 2] No such file or directory
```

**Solution:**
- Ensure `mcp_server_1.py`, `mcp_server_2.py`, `mcp_server_3.py` exist in the project directory
- Check the `cwd` path in `config/profiles.yaml` matches your actual directory

### Issue: Import Errors

**Error:**
```
ModuleNotFoundError: No module named 'mcp'
```

**Solution:**
```bash
pip install mcp pydantic yaml
```

### Issue: Working Directory Path

**Error:**
```
❌ Error initializing MCP server: FileNotFoundError
```

**Solution:**
- Update `config/profiles.yaml`:
  - Change `cwd: I:/TSAI/2025/EAG/Session 9/S9` 
  - To your actual project path: `cwd: C:\Users\surya\Downloads\S9 (1)`

### Issue: No Tools Available

**Error:**
```
⚠️ No tools selected — aborting step.
```

**Solution:**
- Check MCP servers are running correctly
- Verify server scripts are executable
- Check server logs for errors

## Expected File Structure

After running queries, you should see:

```
.
├── agent.py
├── memory/
│   ├── 2025/
│   │   └── 01/
│   │       └── 15/
│   │           └── session-*.json
│   └── historical_conversation_store.json  # Auto-generated
├── config/
│   └── profiles.yaml
└── [other files...]
```

## Tips for Demo/Video

1. **Clear Terminal**: Start with a clean terminal window
2. **Show Initialization**: Let viewers see MCP servers loading
3. **Pause Between Queries**: Give time to see each result
4. **Highlight Features**: Point out heuristics, perception, strategy logs
5. **Show Multi-Step**: Emphasize FURTHER_PROCESSING_REQUIRED flow
6. **Check Historical Index**: After queries, show `memory/historical_conversation_store.json`

## Quick Start Script

Create a file `demo.sh` (Linux/Mac) or `demo.bat` (Windows):

**Windows (demo.bat):**
```batch
@echo off
echo Starting Cortex-R Agent Demo...
echo.
python agent.py
pause
```

**Linux/Mac (demo.sh):**
```bash
#!/bin/bash
echo "Starting Cortex-R Agent Demo..."
echo ""
python agent.py
```

Run with:
- Windows: `demo.bat`
- Linux/Mac: `chmod +x demo.sh && ./demo.sh`

## Next Steps

After running the showcase queries:

1. **Check Historical Index:**
   ```bash
   cat memory/historical_conversation_store.json
   ```
   You should see all 3 queries indexed!

2. **View Session Memory:**
   ```bash
   ls memory/2025/*/*/session-*.json
   ```

3. **Test Heuristics:**
   Try queries with banned words to see filtering in action

4. **Test Historical Context:**
   Run similar queries multiple times to see historical context being used

---

## Summary

**To run the agent:**
```bash
python agent.py
```

**3 Showcase Queries:**
1. `What is the square root of 144 multiplied by the factorial of 3?`
2. `Search for information about renewable energy policies and summarize the key points`
3. `Extract and analyze the main topics from https://theschoolof.ai/`

**Commands:**
- Type query and press Enter
- Type `exit` to quit
- Type `new` to start new session

Happy demonstrating! 🚀

