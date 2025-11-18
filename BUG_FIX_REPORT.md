# Bug Fix Report

## Initial Framework Bug

### Location
`core/loop.py`

### Problem Description

The agent loop was bypassing the entire strategy module by directly calling `modules.decision.generate_plan` instead of using `core.strategy.decide_next_action`.

### Impact

This bug caused several critical issues:

- ❌ **Tool filtering based on perception hints was not working** - The agent couldn't filter tools based on what the perception module suggested
- ❌ **Memory fallback on failures was not triggered** - When tools failed, the system didn't fall back to previously successful tools
- ❌ **Planning modes (conservative/exploratory) were ignored** - The configured planning strategy was completely bypassed
- ❌ **Failed tool tracking for replanning was not functional** - The system couldn't track which tools failed and avoid them in replans

### Root Cause

The buggy code was directly importing and calling the decision module, completely bypassing the strategy layer:

```python
# BEFORE (Buggy Code)
from modules.decision import generate_plan

# In the loop:
plan = await generate_plan(
    user_input=user_input,
    perception=perception,
    memory_items=memory_items,
    tool_descriptions=tool_descriptions,
    prompt_path=prompt_path,
    step_num=step,
    max_steps=max_steps,
)
```

This bypassed:
- Tool filtering logic in `core/strategy.py`
- Memory fallback mechanisms
- Planning mode selection (conservative vs exploratory)
- Failed tool tracking
- Force replan logic

### Solution

**Fixed Code:**

```python
# AFTER (Fixed Code)
from core.strategy import decide_next_action

# In the loop:
plan = await decide_next_action(
    context=self.context,
    perception=perception,
    memory_items=self.context.memory.get_session_items(),
    all_tools=selected_tools,
    last_result=last_result,
    failed_tools=failed_tools,
    force_replan=force_replan,
)
```

### What This Fixed

After the fix:

- ✅ **Tool filtering now works** - Tools are properly filtered based on perception hints and selected servers
- ✅ **Memory fallback activates** - When tools fail, the system falls back to previously successful tools from memory
- ✅ **Planning modes are respected** - Conservative and exploratory modes work as designed
- ✅ **Failed tools are tracked** - The system tracks failed tools and avoids them in replans
- ✅ **Force replan works** - When lifelines are exhausted, the system properly triggers replanning with different tools

### Code Changes

**File:** `core/loop.py`

**Before:**
- Imported `generate_plan` from `modules.decision`
- Called `generate_plan` directly with limited parameters
- No tool filtering, no memory fallback, no planning mode support

**After:**
- Imports `decide_next_action` from `core.strategy`
- Calls `decide_next_action` with full context including:
  - `context`: Full agent context
  - `perception`: Perception results with selected servers
  - `memory_items`: Session memory for context
  - `all_tools`: Filtered tools based on perception
  - `last_result`: Previous step result for continuation
  - `failed_tools`: List of tools that failed (for replanning)
  - `force_replan`: Flag to force replanning with different tools

### Testing Verification

**Before Fix:**
- Queries that required tool filtering would fail
- No memory fallback when tools failed
- Planning modes had no effect

**After Fix:**
- Tool filtering works correctly based on perception
- Memory fallback activates on failures
- Planning modes (conservative/exploratory) function properly
- Failed tools are tracked and avoided in replans

### Related Files Modified

1. **`core/loop.py`** - Changed import and function call
2. **`core/strategy.py`** - Already had the correct implementation, now being used

### Additional Notes

- The `modules.decision.generate_plan` function still exists but is now unused (legacy code)
- The strategy module (`core/strategy.py`) was already correctly implemented but wasn't being called
- This fix enables all the advanced features like memory fallback, tool filtering, and planning modes

### Status

✅ **FIXED** - The bug has been resolved and the agent now properly uses the strategy module with all its features.

