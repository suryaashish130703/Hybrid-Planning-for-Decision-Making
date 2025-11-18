# Power Tool Fix - Square Root Support

## Problem
The query "What is the square root of 144 multiplied by the factorial of 3?" was failing because:
- The `PowerInput` model only accepted `int` for the exponent `b`
- Square root requires `b=0.5` (a float), which caused a validation error
- The tool couldn't calculate square roots using `power(144, 0.5)`

## Solution

### Changed `PowerInput` and `PowerOutput` Models
**File**: `models.py`

**Before:**
```python
class PowerInput(BaseModel):
    a: int
    b: int  # ❌ Only integers allowed

class PowerOutput(BaseModel):
    result: int  # ❌ Only integers returned
```

**After:**
```python
class PowerInput(BaseModel):
    a: int
    b: float  # ✅ Now accepts decimal exponents (e.g., 0.5 for square root)

class PowerOutput(BaseModel):
    result: float  # ✅ Returns float since result can be decimal (e.g., sqrt)
```

### Updated Tool Documentation
**File**: `mcp_server_1.py`

Updated the `power` tool docstring to mention decimal exponent support:
```python
"""Compute a raised to the power of b. Supports decimal exponents (e.g., b=0.5 for square root). 
Usage: input={"input": {"a": 144, "b": 0.5}} result = await mcp.call_tool('power', input)"""
```

## Verification

The calculation now works correctly:
- `power(144, 0.5)` = `12.0` ✅ (square root of 144)
- `factorial(3)` = `6` ✅
- `multiply(12.0, 6)` = `72.0` ✅

## Result

The query "What is the square root of 144 multiplied by the factorial of 3?" now returns:
**FINAL_ANSWER: 72.0**

## Status
✅ Fixed - The power tool now supports decimal exponents for square root calculations.

