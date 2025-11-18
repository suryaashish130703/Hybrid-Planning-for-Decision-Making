# modules/loop.py

import asyncio
from modules.perception import run_perception
from core.strategy import decide_next_action
from modules.action import run_python_sandbox
from modules.model_manager import ModelManager
from core.session import MultiMCP
from core.context import AgentContext
from modules.heuristics import apply_all_heuristics_to_query, apply_all_heuristics_to_result
from modules.historical_conversation import get_historical_conversation_index
import re

try:
    from agent import log
except ImportError:
    import datetime
    def log(stage: str, msg: str):
        now = datetime.datetime.now().strftime("%H:%M:%S")
        print(f"[{now}] [{stage}] {msg}")

class AgentLoop:
    def __init__(self, context: AgentContext):
        self.context = context
        self.mcp = self.context.dispatcher
        self.model = ModelManager()

    async def run(self):
        max_steps = self.context.agent_profile.strategy.max_steps

        for step in range(max_steps):
            print(f"🔁 Step {step+1}/{max_steps} starting...")
            self.context.step = step
            lifelines_left = self.context.agent_profile.strategy.max_lifelines_per_step

            while lifelines_left >= 0:
                # === Apply Heuristics to Query ===
                user_input_override = getattr(self.context, "user_input_override", None)
                raw_input = user_input_override or self.context.user_input
                
                # Get historical context for heuristic enhancement
                historical_context = self.context.memory.get_historical_context_for_heuristics()
                
                # Apply heuristics
                heuristic_result = apply_all_heuristics_to_query(raw_input, historical_context)
                processed_input = heuristic_result["processed_query"]
                
                if heuristic_result["was_modified"]:
                    log("heuristics", f"Query modified: {raw_input[:50]}... -> {processed_input[:50]}...")
                
                # === Perception ===
                perception = await run_perception(context=self.context, user_input=processed_input)

                print(f"[perception] {perception}")

                selected_servers = perception.selected_servers
                selected_tools = self.mcp.get_tools_from_servers(selected_servers)
                
                # Check if this is a summarization/analysis task with content already provided
                user_input_lower = processed_input.lower()
                has_content_to_process = (
                    "your last tool produced" in processed_input.lower() or
                    "content from previous step" in processed_input.lower() or
                    "content already provided" in processed_input.lower()
                ) and any(word in user_input_lower for word in [
                    "summarize", "summary", "key points", "main points", "summarise",
                    "analyze", "analysis", "extract", "topics", "main topics", "identify topics"
                ])
                
                # If summarizing/analyzing provided content, allow proceeding without tools
                if not selected_tools:
                    if has_content_to_process:
                        log("loop", "ℹ️ No tools needed - processing provided content (summarize/analyze)")
                        # Use empty tools list - the LLM will process without calling tools
                        selected_tools = []
                    else:
                        log("loop", "⚠️ No tools selected — aborting step.")
                        break

                # === Planning using Strategy Module ===
                last_result = getattr(self.context, "last_result", "")
                failed_tools = getattr(self.context, "failed_tools", [])
                force_replan = (lifelines_left < self.context.agent_profile.strategy.max_lifelines_per_step)
                
                plan = await decide_next_action(
                    context=self.context,
                    perception=perception,
                    memory_items=self.context.memory.get_session_items(),
                    all_tools=selected_tools,
                    last_result=last_result,
                    failed_tools=failed_tools,
                    force_replan=force_replan,
                )
                print(f"[plan] {plan}")

                # === Execution ===
                if re.search(r"^\s*(async\s+)?def\s+solve\s*\(", plan, re.MULTILINE):
                    print("[loop] Detected solve() plan — running sandboxed...")

                    self.context.log_subtask(tool_name="solve_sandbox", status="pending")
                    result = await run_python_sandbox(plan, dispatcher=self.mcp)

                    success = False
                    if isinstance(result, str):
                        result = result.strip()
                        # Apply heuristics to result
                        result = apply_all_heuristics_to_result(result)
                        
                        if result.startswith("FINAL_ANSWER:"):
                            success = True
                            self.context.final_answer = result
                            self.context.update_subtask_status("solve_sandbox", "success")
                            self.context.memory.add_tool_output(
                                tool_name="solve_sandbox",
                                tool_args={"plan": plan},
                                tool_result={"result": result},
                                success=True,
                                tags=["sandbox"],
                            )
                            return {"status": "done", "result": self.context.final_answer}
                        elif result.startswith("FURTHER_PROCESSING_REQUIRED:"):
                            content = result.split("FURTHER_PROCESSING_REQUIRED:")[1].strip()
                            # Check if the original task asks for summarization or analysis
                            original_task_lower = self.context.user_input.lower()
                            needs_summary = any(word in original_task_lower for word in [
                                "summarize", "summary", "key points", "main points", "summarise"
                            ])
                            needs_analysis = any(word in original_task_lower for word in [
                                "analyze", "analysis", "extract", "topics", "main topics", "identify topics"
                            ])
                            
                            if needs_summary:
                                self.context.user_input_override = (
                                    f"Original user task: {self.context.user_input}\n\n"
                                    f"Your last tool produced this content:\n\n"
                                    f"{content}\n\n"
                                    f"TASK: Summarize this content into key points. Return a FINAL_ANSWER with:\n"
                                    f"- Bullet points (use • or -)\n"
                                    f"- Clear, concise key points\n"
                                    f"- Format: FINAL_ANSWER: • Point 1\\n• Point 2\\n• Point 3\n\n"
                                    f"DO NOT call any tools. Just analyze and summarize the content provided above."
                                )
                            elif needs_analysis:
                                self.context.user_input_override = (
                                    f"Original user task: {self.context.user_input}\n\n"
                                    f"Your last tool produced this content:\n\n"
                                    f"{content}\n\n"
                                    f"TASK: Analyze and extract the main topics from this content. Return a FINAL_ANSWER with:\n"
                                    f"- Main topics listed clearly (use • or numbered list)\n"
                                    f"- Format: FINAL_ANSWER: Main Topics:\\n• Topic 1\\n• Topic 2\\n• Topic 3\n\n"
                                    f"DO NOT call any tools. Just analyze the content and extract the main topics."
                                )
                            else:
                                self.context.user_input_override = (
                                    f"Original user task: {self.context.user_input}\n\n"
                                    f"Your last tool produced this result:\n\n"
                                    f"{content}\n\n"
                                    f"If this fully answers the task, return:\n"
                                    f"FINAL_ANSWER: your answer\n\n"
                                    f"Otherwise, return the next FUNCTION_CALL."
                                )
                            log("loop", f"📨 Forwarding intermediate result to next step:\n{self.context.user_input_override}\n\n")
                            log("loop", f"🔁 Continuing based on FURTHER_PROCESSING_REQUIRED — Step {step+1} continues...")
                            break  # Step will continue
                        elif result.startswith("[sandbox error:"):
                            success = False
                            self.context.final_answer = "FINAL_ANSWER: [Execution failed]"
                        else:
                            success = True
                            self.context.final_answer = f"FINAL_ANSWER: {result}"
                    else:
                        self.context.final_answer = f"FINAL_ANSWER: {result}"

                    if success:
                        self.context.update_subtask_status("solve_sandbox", "success")
                        self.context.last_result = result
                        if "solve_sandbox" in getattr(self.context, "failed_tools", []):
                            self.context.failed_tools.remove("solve_sandbox")
                    else:
                        self.context.update_subtask_status("solve_sandbox", "failure")
                        if not hasattr(self.context, "failed_tools"):
                            self.context.failed_tools = []
                        if "solve_sandbox" not in self.context.failed_tools:
                            self.context.failed_tools.append("solve_sandbox")

                    self.context.memory.add_tool_output(
                        tool_name="solve_sandbox",
                        tool_args={"plan": plan},
                        tool_result={"result": result},
                        success=success,
                        tags=["sandbox"],
                    )

                    if success and "FURTHER_PROCESSING_REQUIRED:" not in result:
                        # Index this conversation before returning
                        hist_index = get_historical_conversation_index()
                        hist_index.index_session(self.context.session_id, self.context.memory.memory_path)
                        return {"status": "done", "result": self.context.final_answer}
                    else:
                        lifelines_left -= 1
                        log("loop", f"🛠 Retrying... Lifelines left: {lifelines_left}")
                        continue
                else:
                    log("loop", f"⚠️ Invalid plan detected — retrying... Lifelines left: {lifelines_left-1}")
                    lifelines_left -= 1
                    continue

        log("loop", "⚠️ Max steps reached without finding final answer.")
        self.context.final_answer = "FINAL_ANSWER: [Max steps reached]"
        # Index conversation even if failed
        hist_index = get_historical_conversation_index()
        hist_index.index_session(self.context.session_id, self.context.memory.memory_path)
        return {"status": "done", "result": self.context.final_answer}
