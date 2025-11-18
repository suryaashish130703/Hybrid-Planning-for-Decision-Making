# modules/historical_conversation.py

"""
Historical Conversation Indexing and Retrieval System.
Indexes past conversations and provides them to the agent for context.
"""

import json
import os
from typing import List, Dict, Any, Optional
from pathlib import Path
from datetime import datetime
import time

try:
    from agent import log
except ImportError:
    import datetime
    def log(stage: str, msg: str):
        now = datetime.datetime.now().strftime("%H:%M:%S")
        print(f"[{now}] [{stage}] {msg}")

class HistoricalConversationIndex:
    """
    Indexes and retrieves historical conversations from memory files.
    """
    
    def __init__(self, memory_dir: str = "memory", index_file: str = "historical_conversation_store.json"):
        self.memory_dir = memory_dir
        self.index_file = index_file
        self.index_path = os.path.join(memory_dir, index_file)
        self.index: List[Dict[str, Any]] = []
        self.load_index()
    
    def load_index(self):
        """Load existing index from file."""
        if os.path.exists(self.index_path):
            try:
                with open(self.index_path, "r", encoding="utf-8") as f:
                    self.index = json.load(f)
                log("historical", f"Loaded {len(self.index)} historical conversations")
            except Exception as e:
                log("historical", f"Error loading index: {e}")
                self.index = []
        else:
            self.index = []
    
    def save_index(self):
        """Save index to file."""
        os.makedirs(self.memory_dir, exist_ok=True)
        with open(self.index_path, "w", encoding="utf-8") as f:
            json.dump(self.index, f, indent=2, ensure_ascii=False)
    
    def index_session(self, session_id: str, session_file: str):
        """
        Index a single session file.
        Extracts query, answer, and metadata.
        """
        if not os.path.exists(session_file):
            return
        
        try:
            with open(session_file, "r", encoding="utf-8") as f:
                items = json.load(f)
            
            # Extract key information
            query = None
            answer = None
            tools_used = []
            entities = []
            timestamp = None
            success = False
            
            for item in items:
                if item.get("type") == "run_metadata" and item.get("user_query"):
                    query = item.get("user_query")
                    timestamp = item.get("timestamp")
                elif item.get("type") == "final_answer":
                    answer = item.get("final_answer") or item.get("text")
                    success = True
                elif item.get("type") == "tool_output":
                    tool_name = item.get("tool_name")
                    if tool_name and tool_name not in tools_used:
                        tools_used.append(tool_name)
                    if item.get("success"):
                        success = True
                if item.get("entities"):
                    entities.extend(item.get("entities", []))
            
            if query:  # Only index if we have a query
                entry = {
                    "session_id": session_id,
                    "query": query,
                    "answer": answer,
                    "tools_used": tools_used,
                    "entities": list(set(entities)),
                    "timestamp": timestamp,
                    "success": success,
                    "indexed_at": time.time()
                }
                
                # Check if already indexed
                existing = next((e for e in self.index if e.get("session_id") == session_id), None)
                if existing:
                    # Update existing
                    idx = self.index.index(existing)
                    self.index[idx] = entry
                else:
                    # Add new
                    self.index.append(entry)
                
                self.save_index()
                log("historical", f"Indexed session {session_id}")
        
        except Exception as e:
            log("historical", f"Error indexing session {session_id}: {e}")
    
    def index_all_sessions(self):
        """
        Scan memory directory and index all session files.
        """
        if not os.path.exists(self.memory_dir):
            return
        
        log("historical", "Scanning memory directory for sessions...")
        indexed_count = 0
        
        # Walk through memory directory structure
        for root, dirs, files in os.walk(self.memory_dir):
            for file in files:
                if file.startswith("session-") and file.endswith(".json"):
                    if file == self.index_file:
                        continue  # Skip index file itself
                    
                    session_file = os.path.join(root, file)
                    # Extract session_id from filename
                    session_id = file.replace("session-", "").replace(".json", "")
                    
                    # Check if already indexed and up-to-date
                    existing = next((e for e in self.index if e.get("session_id") == session_id), None)
                    file_mtime = os.path.getmtime(session_file)
                    
                    if not existing or existing.get("indexed_at", 0) < file_mtime:
                        self.index_session(session_id, session_file)
                        indexed_count += 1
        
        log("historical", f"Indexed {indexed_count} new/updated sessions")
    
    def search_conversations(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Search historical conversations by query text.
        Returns most relevant conversations.
        """
        query_lower = query.lower()
        query_words = set(query_lower.split())
        
        scored = []
        for entry in self.index:
            score = 0
            entry_query = entry.get("query", "").lower()
            entry_answer = entry.get("answer", "").lower() if entry.get("answer") else ""
            
            # Score based on word matches
            entry_words = set(entry_query.split())
            common_words = query_words.intersection(entry_words)
            score += len(common_words) * 2  # Query matches are more important
            
            # Check answer too
            if entry_answer:
                answer_words = set(entry_answer.split())
                common_answer_words = query_words.intersection(answer_words)
                score += len(common_answer_words)
            
            # Boost successful queries
            if entry.get("success"):
                score += 1
            
            # Boost recent queries
            if entry.get("timestamp"):
                age_days = (time.time() - entry.get("timestamp", 0)) / 86400
                if age_days < 7:  # Within last week
                    score += 1
            
            if score > 0:
                scored.append((score, entry))
        
        # Sort by score descending
        scored.sort(key=lambda x: x[0], reverse=True)
        
        # Return top results
        return [entry for _, entry in scored[:limit]]
    
    def get_relevant_context(self, current_query: str, limit: int = 3) -> str:
        """
        Get relevant historical context as formatted string for LLM.
        """
        relevant = self.search_conversations(current_query, limit=limit)
        
        if not relevant:
            return "No relevant historical conversations found."
        
        context_parts = ["📚 Relevant Historical Conversations:"]
        for i, entry in enumerate(relevant, 1):
            query = entry.get("query", "N/A")
            answer = entry.get("answer", "N/A")
            tools = entry.get("tools_used", [])
            
            context_parts.append(f"\n{i}. Query: {query}")
            if answer and answer != "N/A":
                answer_preview = answer[:200] + "..." if len(answer) > 200 else answer
                context_parts.append(f"   Answer: {answer_preview}")
            if tools:
                context_parts.append(f"   Tools used: {', '.join(tools)}")
        
        return "\n".join(context_parts)
    
    def get_all_indexed_sessions(self) -> List[Dict[str, Any]]:
        """Get all indexed sessions."""
        return self.index.copy()


def get_historical_conversation_index() -> HistoricalConversationIndex:
    """Get or create the global historical conversation index."""
    return HistoricalConversationIndex()

