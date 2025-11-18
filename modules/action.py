# modules/action.py

from typing import Dict, Any, Union
from pydantic import BaseModel
import asyncio
import types
import json


# Optional logging fallback
try:
    from agent import log
except ImportError:
    import datetime
    def log(stage: str, msg: str):
        now = datetime.datetime.now().strftime("%H:%M:%S")
        print(f"[{now}] [{stage}] {msg}")

class ToolCallResult(BaseModel):
    tool_name: str
    arguments: Dict[str, Any]
    result: Union[str, list, dict]
    raw_response: Any

MAX_TOOL_CALLS_PER_PLAN = 5

async def run_python_sandbox(code: str, dispatcher: Any) -> str:
    print("[action] 🔍 Entered run_python_sandbox()")

    # Create a fresh module scope
    sandbox = types.ModuleType("sandbox")

    try:
        # Helper function to safely parse MCP tool results
        def safe_parse_mcp_result(result):
            """Safely parse MCP tool result, handling different response formats."""
            try:
                # Check if result has content attribute (MCP response format)
                if hasattr(result, 'content') and result.content:
                    if len(result.content) > 0:
                        text = result.content[0].text
                        if text and text.strip():
                            try:
                                parsed = json.loads(text)
                                if isinstance(parsed, dict) and "result" in parsed:
                                    return parsed["result"]
                                return parsed
                            except json.JSONDecodeError:
                                # If not JSON, return as string
                                return text
                        else:
                            # Empty text, try to get result from response object
                            if hasattr(result, 'result'):
                                return result.result
                            return None
                
                # Check if result is already a dict with "result" key
                if isinstance(result, dict) and "result" in result:
                    return result["result"]
                
                # Check if result has a "result" attribute
                if hasattr(result, 'result'):
                    return result.result
                
                # Return as-is
                return result
            except Exception as e:
                log("sandbox", f"⚠️ Error parsing MCP result: {e}, result type: {type(result)}")
                return result

        # Patch MCP client with real dispatcher
        class SandboxMCP:
            def __init__(self, dispatcher):
                self.dispatcher = dispatcher
                self.call_count = 0

            async def call_tool(self, tool_name: str, input_dict: dict):
                self.call_count += 1
                if self.call_count > MAX_TOOL_CALLS_PER_PLAN:
                    raise RuntimeError(f"Exceeded max tool calls ({MAX_TOOL_CALLS_PER_PLAN}) in solve() plan.")
                # REAL tool call now
                result = await self.dispatcher.call_tool(tool_name, input_dict)
                # Log the result structure for debugging
                log("sandbox", f"Tool '{tool_name}' returned: type={type(result)}, has_content={hasattr(result, 'content')}")
                if hasattr(result, 'content') and result.content:
                    log("sandbox", f"Content[0].text length: {len(result.content[0].text) if result.content[0].text else 0}")
                return result

        sandbox.mcp = SandboxMCP(dispatcher)
        sandbox.safe_parse_mcp_result = safe_parse_mcp_result
        
        # Helper function for safe JSON parsing from MCP results
        def parse_result(result):
            """Helper to safely extract result value from MCP tool response."""
            try:
                if hasattr(result, 'content') and result.content and len(result.content) > 0:
                    text = result.content[0].text
                    if text and text.strip():
                        parsed = json.loads(text)
                        return parsed.get("result") if isinstance(parsed, dict) else parsed
                if hasattr(result, 'structuredContent') and result.structuredContent:
                    if isinstance(result.structuredContent, dict) and "result" in result.structuredContent:
                        return result.structuredContent["result"]
                if hasattr(result, 'result'):
                    return result.result
                return result
            except Exception as e:
                log("sandbox", f"Error in parse_result: {e}")
                return None
        
        sandbox.parse_result = parse_result

        # Preload safe built-ins into the sandbox
        import json, re
        sandbox.__dict__["json"] = json
        sandbox.__dict__["re"] = re

        # Clean and validate code before execution
        code = code.strip()
        
        # Log the code being executed (first 500 chars for debugging)
        log("sandbox", f"Executing code (first 500 chars):\n{code[:500]}...")
        
        # Try to compile first to catch syntax errors early
        try:
            compiled = compile(code, "<solve_plan>", "exec")
        except SyntaxError as e:
            log("sandbox", f"⚠️ Syntax error in generated code: {e}")
            log("sandbox", f"Error at line {e.lineno}: {e.text}")
            raise
        
        # Execute solve fn dynamically
        exec(compiled, sandbox.__dict__)

        solve_fn = sandbox.__dict__.get("solve")
        if solve_fn is None:
            raise ValueError("No solve() function found in plan.")

        if asyncio.iscoroutinefunction(solve_fn):
            result = await solve_fn()
        else:
            result = solve_fn()

        # Clean result formatting
        if isinstance(result, dict) and "result" in result:
            return f"{result['result']}"
        elif isinstance(result, dict):
            return f"{json.dumps(result)}"
        elif isinstance(result, list):
            return f"{' '.join(str(r) for r in result)}"
        else:
            return f"{result}"






    except Exception as e:
        log("sandbox", f"⚠️ Execution error: {e}")
        return f"[sandbox error: {str(e)}]"
