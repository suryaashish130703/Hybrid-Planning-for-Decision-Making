# Direct GitHub Links

## Heuristic Rule File Link

**File:** `modules/heuristics.py`

**Direct GitHub Link:**
https://github.com/suryaashish130703/Hybrid-Planning-for-Decision-Making/blob/main/modules/heuristics.py

**Description:**
This file contains all 10 heuristic functions that process queries and results:
1. Remove Banned Words
2. Remove Profanity
3. Redact Sensitive Info
4. Normalize Whitespace
5. Remove Special Chars
6. Limit Length
7. Extract Key Entities
8. Validate Query Structure
9. Sanitize Result
10. Enhance Query with Context

**Main Functions:**
- `apply_all_heuristics_to_query()` - Applies all heuristics to user queries
- `apply_all_heuristics_to_result()` - Applies all heuristics to results

---

## New Decision Prompt - Direct GitHub Link

**File:** `prompts/decision_prompt_conservative.txt`

**Direct GitHub Link:**
https://github.com/suryaashish130703/Hybrid-Planning-for-Decision-Making/blob/main/prompts/decision_prompt_conservative.txt

**Details:**
- **Word Count:** 277 words (target: <300 words) ✅
- **Reduction:** 62% reduction from original 729 words
- **Status:** Optimized and functional

**What it includes:**
- Task description and rules
- Safe result parsing instructions using `parse_result()` helper
- Three comprehensive examples:
  - Math calculation (using power, factorial, multiply)
  - Search (using duckduckgo_search_results)
  - Summarize (no tool call, direct analysis)
- Formatting requirements for FINAL_ANSWER
- Support for FURTHER_PROCESSING_REQUIRED flow

**Key Features:**
- Uses `parse_result()` helper for safe MCP result parsing
- Supports decimal exponents (e.g., `power(144, 0.5)` for square root)
- Handles multi-step processing
- Clear instructions for summarization and topic extraction

---

## Additional Important Links

### Main README
**Link:** https://github.com/suryaashish130703/Hybrid-Planning-for-Decision-Making/blob/main/README.md

### README with Examples
**Link:** https://github.com/suryaashish130703/Hybrid-Planning-for-Decision-Making/blob/main/README_WITH_EXAMPLES.md

### Bug Fix Report
**Link:** https://github.com/suryaashish130703/Hybrid-Planning-for-Decision-Making/blob/main/BUG_FIX_REPORT.md

### Historical Conversation Store
**File:** `memory/historical_conversation_store.json`
**Link:** https://github.com/suryaashish130703/Hybrid-Planning-for-Decision-Making/blob/main/memory/historical_conversation_store.json

**Note:** This file may not exist in the repository if no sessions have been indexed yet. It's created automatically when sessions are completed.

---

## Repository Root
**Main Repository:** https://github.com/suryaashish130703/Hybrid-Planning-for-Decision-Making

