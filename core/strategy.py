# modules/strategy.py

from typing import List, Optional, Any
from modules.perception import PerceptionResult
from modules.memory import MemoryItem
from modules.model_manager import ModelManager
from core.context import AgentContext
from modules.tools import filter_tools_by_hint, summarize_tools, load_prompt
from modules.historical_conversation import get_historical_conversation_index
import re

# Optional fallback logger
try:
    from agent import log
except ImportError:
    import datetime
    def log(stage: str, msg: str):
        now = datetime.datetime.now().strftime("%H:%M:%S")
        print(f"[{now}] [{stage}] {msg}")

def select_decision_prompt_path(planning_mode: str, exploration_mode: Optional[str] = None) -> str:
    """Selects the appropriate decision prompt file based on planning strategy."""
    if planning_mode == "conservative":
        return "prompts/decision_prompt_conservative.txt"
    elif planning_mode == "exploratory":
        if exploration_mode == "parallel":
            return "prompts/decision_prompt_exploratory_parallel.txt"
        elif exploration_mode == "sequential":
            return "prompts/decision_prompt_exploratory_sequential.txt"
    return "prompts/decision_prompt_conservative.txt"  # safe fallback

model = ModelManager()

def extract_python_code(text: str) -> str:
    """
    Extract Python code from LLM response.
    Handles markdown code blocks, plain code, or mixed formats.
    """
    original_text = text
    
    # Remove markdown code blocks if present
    code_block_pattern = r"```(?:python)?\s*\n?(.*?)```"
    matches = re.findall(code_block_pattern, text, re.DOTALL)
    if matches:
        # Take the first code block
        code = matches[0].strip()
    else:
        # No code blocks, check if it's already code
        code = text.strip()
    
    # Remove any leading/trailing markdown or explanation
    # Look for async def solve or def solve
    solve_pattern = r"(async\s+)?def\s+solve\s*\([^)]*\):.*"
    match = re.search(solve_pattern, code, re.DOTALL)
    if match:
        code = match.group(0)
    else:
        # If no match, try to find it in the original text
        match = re.search(solve_pattern, original_text, re.DOTALL)
        if match:
            code = match.group(0)
        else:
            log("strategy", f"⚠️ Could not find solve() function in response")
            # Try to return the code as-is, might work
            code = original_text.strip()
    
    # Clean up: remove any lines before "def solve" or "async def solve"
    lines = code.split('\n')
    start_idx = 0
    for i, line in enumerate(lines):
        if re.search(r'^\s*(async\s+)?def\s+solve\s*\(', line):
            start_idx = i
            break
    
    if start_idx > 0:
        code = '\n'.join(lines[start_idx:])
    
    # Remove any trailing markdown or explanation after the function
    # Find the last return statement and everything after it
    return_pattern = r'(return\s+[^\n]+)'
    return_matches = list(re.finditer(return_pattern, code, re.MULTILINE))
    if return_matches:
        last_return = return_matches[-1]
        code = code[:last_return.end()]
    
    # Basic validation - ensure it has def solve
    if not re.search(r'(async\s+)?def\s+solve\s*\(', code):
        log("strategy", "⚠️ Warning: Extracted code doesn't contain solve() function")
        return original_text.strip()  # Return original as fallback
    
    return code.strip()

async def decide_next_action(
    context: AgentContext,
    perception: PerceptionResult,
    memory_items: List[MemoryItem],
    all_tools: List[Any],
    last_result: str = "",
    failed_tools: List[str] = [],
    force_replan: bool = False,
) -> str:
    """
    Main decision function.
    """

    strategy = context.agent_profile.strategy
    planning_mode = strategy.planning_mode
    exploration_mode = strategy.exploration_mode
    memory_fallback_enabled = strategy.memory_fallback_enabled
    max_steps = strategy.max_steps
    max_lifelines_per_step = strategy.max_lifelines_per_step
    step_num = context.step + 1
    
    # Get user input (from override if exists, else original)
    user_input = getattr(context, "user_input_override", None) or context.user_input

    # === Select correct decision prompt path ===
    prompt_path = select_decision_prompt_path(planning_mode, exploration_mode)

    # Filter tools based on Perception hint
    tool_hint = perception.tool_hint
    filtered_tools = filter_tools_by_hint(all_tools, hint=tool_hint)
    filtered_summary = summarize_tools(filtered_tools) if filtered_tools else "No tools available. You must solve this without calling any tools."

    if planning_mode == "conservative":
        return await conservative_plan(
            user_input, perception, memory_items, filtered_summary, all_tools, step_num, max_steps,
            prompt_path, force_replan
        )

    if planning_mode == "exploratory":
        return await exploratory_plan(
            user_input, perception, memory_items, filtered_summary, all_tools, step_num, max_steps,
            exploration_mode, memory_fallback_enabled, prompt_path, force_replan, failed_tools
        )

    # Fallback
    full_summary = summarize_tools(all_tools)
    plan = await generate_plan(
        user_input=user_input,
        perception=perception,
        memory_items=memory_items,
        tool_descriptions=full_summary,
        prompt_path=prompt_path,
        step_num=step_num,
        max_steps=max_steps,
    )
    return plan

# === CONSERVATIVE MODE ===
async def conservative_plan(
    user_input: str,
    perception: PerceptionResult,
    memory_items: List[MemoryItem],
    filtered_summary: str,
    all_tools: List[Any],
    step_num: int,
    max_steps: int,
    prompt_path: str,
    force_replan: bool
) -> str:
    """Conservative: Plan 1 tool call."""

    # Check if this is a summarization/analysis task with content already provided
    has_content_to_process = (
        "your last tool produced" in user_input.lower() or
        "content from previous step" in user_input.lower() or
        "content already provided" in user_input.lower()
    ) and any(word in user_input.lower() for word in [
        "summarize", "summary", "key points", "main points", "summarise",
        "analyze", "analysis", "extract", "topics", "main topics", "identify topics"
    ])
    
    if has_content_to_process and not all_tools:
        # No tools available and we need to summarize - use empty tool list
        tool_context = "No tools available. You must analyze and summarize the provided content without calling any tools."
    elif force_replan or not filtered_summary.strip() or filtered_summary == "No tools available. You must solve this without calling any tools.":
        if all_tools:
            log("strategy", "⚠️ Force replan or no filtered tools. Using all tools.")
            tool_context = summarize_tools(all_tools)
        else:
            tool_context = "No tools available. You must solve this without calling any tools."
    else:
        tool_context = filtered_summary

    plan = await generate_plan(
        user_input=user_input,
        perception=perception,
        memory_items=memory_items,
        tool_descriptions=tool_context,
        prompt_path=prompt_path,
        step_num=step_num,
        max_steps=max_steps
    )

    return plan

# === EXPLORATORY MODE ===
async def exploratory_plan(
    user_input: str,
    perception: PerceptionResult,
    memory_items: List[MemoryItem],
    filtered_summary: str,
    all_tools: List[Any],
    step_num: int,
    max_steps: int,
    exploration_mode: str,
    memory_fallback_enabled: bool,
    prompt_path: str,
    force_replan: bool,
    failed_tools: List[str]
) -> str:
    """Exploratory: Plan multiple options."""

    if force_replan:
        log("strategy", "⚠️ Force replan triggered. Attempting fallback.")

        if memory_fallback_enabled:
            fallback_tools = find_recent_successful_tools(memory_items)
            if fallback_tools:
                log("strategy", f"✅ Memory fallback tools found: {fallback_tools}")
                fallback_summary = summarize_tools(fallback_tools)
                return await generate_plan(
                    user_input=user_input,
                    perception=perception,
                    memory_items=memory_items,
                    tool_descriptions=fallback_summary,
                    prompt_path=prompt_path,
                    step_num=step_num,
                    max_steps=max_steps
                )
            else:
                log("strategy", "⚠️ No memory fallback tools. Using all tools.")

        tool_context = summarize_tools(all_tools)
        return await generate_plan(
            user_input=user_input,
            perception=perception,
            memory_items=memory_items,
            tool_descriptions=tool_context,
            prompt_path=prompt_path,
            step_num=step_num,
            max_steps=max_steps
        )

    if not filtered_summary.strip():
        log("strategy", "⚠️ No filtered tools. Using all tools.")
        tool_context = summarize_tools(all_tools)
    else:
        tool_context = filtered_summary

    plan = await generate_plan(
        user_input=user_input,
        perception=perception,
        memory_items=memory_items,
        tool_descriptions=tool_context,
        prompt_path=prompt_path,
        step_num=step_num,
        max_steps=max_steps
    )

    return plan

# === GENERATE PLAN ===
async def generate_plan(
    user_input: str,
    perception: PerceptionResult,
    memory_items: List[MemoryItem],
    tool_descriptions: str,
    prompt_path: str,
    step_num: int,
    max_steps: int,
) -> str:
    """Ask LLM to generate solve() using the right prompt."""

    prompt_template = load_prompt(prompt_path)
    
    # Get historical conversation context
    hist_index = get_historical_conversation_index()
    historical_context = hist_index.get_relevant_context(user_input, limit=3)
    
    # Format prompt with historical context
    final_prompt = prompt_template.format(
        tool_descriptions=tool_descriptions,
        user_input=user_input
    )
    
    # Append historical context if available
    if historical_context and "No relevant" not in historical_context:
        final_prompt = f"{final_prompt}\n\n{historical_context}"

    raw = (await model.generate_text(final_prompt)).strip()
    log("plan", f"Generated solve():\n{raw}")
    
    # Extract Python code from markdown code blocks if present
    code = extract_python_code(raw)
    
    return code

# === MEMORY FALLBACK LOGIC ===
def find_recent_successful_tools(memory_items: List[MemoryItem], limit: int = 5) -> List[str]:
    """Find recent successful tool names based on memory items."""
    successful_tools = []

    for item in reversed(memory_items):
        if item.type == "tool_output" and item.success and item.tool_name:
            if item.tool_name not in successful_tools:
                successful_tools.append(item.tool_name)
        if len(successful_tools) >= limit:
            break

    return successful_tools
