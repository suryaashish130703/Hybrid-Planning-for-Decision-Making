# modules/heuristics.py

"""
Heuristics module for processing queries and results.
Applies 10 different heuristics to clean, filter, and enhance queries/results.
"""

import re
from typing import List, Dict, Any, Optional

# Banned words list - words that should be removed from queries/results
BANNED_WORDS = [
    "hack", "exploit", "crack", "bypass", "illegal", "unauthorized",
    "malware", "virus", "trojan", "phishing", "spam", "scam",
    "porn", "xxx", "nsfw", "explicit", "adult content",
    "violence", "gore", "torture", "kill", "murder",
    "drug", "cocaine", "heroin", "meth", "weed",
    "terrorism", "bomb", "weapon", "gun", "ammo"
]

# Profanity filter (common profanities)
PROFANITY_PATTERNS = [
    r'\b(fuck|shit|damn|hell|ass|bitch|bastard)\w*\b',
    r'\b(crap|piss|dick|pussy|cock)\w*\b',
]

# Sensitive information patterns
SENSITIVE_PATTERNS = [
    r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b',  # Credit card
    r'\b\d{3}-\d{2}-\d{4}\b',  # SSN
    r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',  # Email (optional - may want to keep)
    r'\b\d{10,}\b',  # Long numbers (potential sensitive IDs)
]

def heuristic_1_remove_banned_words(text: str) -> str:
    """
    Heuristic 1: Remove banned words from query/result.
    Replaces banned words with [REDACTED] to maintain context.
    """
    words = text.split()
    cleaned = []
    for word in words:
        word_lower = word.lower().strip('.,!?;:()[]{}"\'')
        if word_lower in BANNED_WORDS:
            cleaned.append("[REDACTED]")
        else:
            cleaned.append(word)
    return " ".join(cleaned)


def heuristic_2_remove_profanity(text: str) -> str:
    """
    Heuristic 2: Remove profanity using regex patterns.
    """
    cleaned = text
    for pattern in PROFANITY_PATTERNS:
        cleaned = re.sub(pattern, "[REDACTED]", cleaned, flags=re.IGNORECASE)
    return cleaned


def heuristic_3_redact_sensitive_info(text: str) -> str:
    """
    Heuristic 3: Redact sensitive information (credit cards, SSN, etc.).
    """
    cleaned = text
    # Redact credit cards
    cleaned = re.sub(r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b', '[REDACTED_CARD]', cleaned)
    # Redact SSN
    cleaned = re.sub(r'\b\d{3}-\d{2}-\d{4}\b', '[REDACTED_SSN]', cleaned)
    # Redact long numeric IDs (potential sensitive data)
    cleaned = re.sub(r'\b\d{12,}\b', '[REDACTED_ID]', cleaned)
    return cleaned


def heuristic_4_normalize_whitespace(text: str) -> str:
    """
    Heuristic 4: Normalize excessive whitespace.
    Removes multiple spaces, tabs, newlines.
    """
    # Replace multiple spaces with single space
    cleaned = re.sub(r' +', ' ', text)
    # Replace multiple newlines with single newline
    cleaned = re.sub(r'\n\s*\n+', '\n\n', cleaned)
    # Replace tabs with spaces
    cleaned = cleaned.replace('\t', ' ')
    return cleaned.strip()


def heuristic_5_remove_special_chars(text: str, keep_basic: bool = True) -> str:
    """
    Heuristic 5: Remove excessive special characters.
    Keeps basic punctuation if keep_basic=True.
    """
    if keep_basic:
        # Keep basic punctuation: . , ! ? : ; - ( ) [ ] { } " '
        cleaned = re.sub(r'[^\w\s\.\,\!\?\:\;\-\(\)\[\]\{\}\"\']+', '', text)
    else:
        # Remove all non-alphanumeric except spaces
        cleaned = re.sub(r'[^\w\s]+', '', text)
    return cleaned


def heuristic_6_limit_length(text: str, max_length: int = 5000) -> str:
    """
    Heuristic 6: Limit text length to prevent token overflow.
    Truncates and adds indicator if truncated.
    """
    if len(text) <= max_length:
        return text
    return text[:max_length] + "... [TRUNCATED]"


def heuristic_7_extract_key_entities(text: str) -> List[str]:
    """
    Heuristic 7: Extract key entities (numbers, capitalized words, quoted strings).
    Returns list of entities found.
    """
    entities = []
    # Extract numbers
    numbers = re.findall(r'\b\d+\.?\d*\b', text)
    entities.extend(numbers)
    # Extract capitalized words (potential proper nouns)
    capitalized = re.findall(r'\b[A-Z][a-z]+\b', text)
    entities.extend(capitalized)
    # Extract quoted strings
    quoted = re.findall(r'"([^"]*)"', text)
    entities.extend(quoted)
    return list(set(entities))  # Remove duplicates


def heuristic_8_validate_query_structure(query: str) -> Dict[str, Any]:
    """
    Heuristic 8: Validate query structure and return metadata.
    Checks for question marks, imperative verbs, etc.
    """
    metadata = {
        "is_question": "?" in query,
        "is_imperative": query.strip().split()[0].lower() in ["find", "get", "show", "calculate", "search", "list", "tell"],
        "has_entities": len(heuristic_7_extract_key_entities(query)) > 0,
        "word_count": len(query.split()),
        "is_valid": len(query.strip()) > 0
    }
    return metadata


def heuristic_9_sanitize_result(result: str) -> str:
    """
    Heuristic 9: Comprehensive sanitization of results.
    Applies multiple cleaning heuristics in sequence.
    """
    cleaned = result
    # Remove banned words
    cleaned = heuristic_1_remove_banned_words(cleaned)
    # Remove profanity
    cleaned = heuristic_2_remove_profanity(cleaned)
    # Redact sensitive info
    cleaned = heuristic_3_redact_sensitive_info(cleaned)
    # Normalize whitespace
    cleaned = heuristic_4_normalize_whitespace(cleaned)
    # Limit length
    cleaned = heuristic_6_limit_length(cleaned)
    return cleaned


def heuristic_10_enhance_query_with_context(query: str, context: Optional[Dict[str, Any]] = None) -> str:
    """
    Heuristic 10: Enhance query with context from previous interactions.
    Adds relevant context if available.
    """
    if not context:
        return query
    
    enhanced = query
    # Add relevant previous queries if available
    if "previous_queries" in context and context["previous_queries"]:
        recent = context["previous_queries"][-1] if isinstance(context["previous_queries"], list) else ""
        if recent and recent.lower() not in query.lower():
            enhanced = f"{query} [Context: Related to previous query about {recent[:50]}...]"
    
    # Add entity hints if available
    if "entities" in context and context["entities"]:
        entities_str = ", ".join(context["entities"][:3])
        enhanced = f"{enhanced} [Entities: {entities_str}]"
    
    return enhanced


def apply_all_heuristics_to_query(query: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Apply all heuristics to a query and return processed query + metadata.
    """
    # Validate structure
    validation = heuristic_8_validate_query_structure(query)
    
    # Extract entities
    entities = heuristic_7_extract_key_entities(query)
    
    # Remove banned words
    cleaned_query = heuristic_1_remove_banned_words(query)
    
    # Remove profanity
    cleaned_query = heuristic_2_remove_profanity(cleaned_query)
    
    # Normalize whitespace
    cleaned_query = heuristic_4_normalize_whitespace(cleaned_query)
    
    # Enhance with context
    enhanced_query = heuristic_10_enhance_query_with_context(cleaned_query, context)
    
    return {
        "original_query": query,
        "processed_query": enhanced_query,
        "entities": entities,
        "validation": validation,
        "was_modified": query != enhanced_query
    }


def apply_all_heuristics_to_result(result: str) -> str:
    """
    Apply all heuristics to a result and return sanitized result.
    """
    return heuristic_9_sanitize_result(result)

