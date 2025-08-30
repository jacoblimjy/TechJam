from __future__ import annotations
import json, re, os
from typing import List, Dict, Any, Union
from datetime import datetime
from langchain_core.documents import Document

def format_docs_for_context(docs: List[Document]) -> str:
    lines = []
    for i, d in enumerate(docs, 1):
        m = d.metadata
        title = m.get("h3") or m.get("h2") or m.get("h1") or m.get("law_name") or "Untitled"
        cite = []
        if m.get("law_name"): cite.append(m["law_name"])
        if m.get("region"): cite.append(m["region"])
        if m.get("article_or_section"): cite.append(m["article_or_section"])
        lines.append(f"[{i}] {title} — {' | '.join([c for c in cite if c])}".strip(" —"))
        lines.append(d.page_content.strip())
        lines.append("")  # blank line
    return "\n".join(lines).strip()

def extract_json_block(text: str) -> str:
    # try to grab first {...} JSON block
    m = re.search(r"\{.*\}", text, flags=re.S)
    return m.group(0) if m else "{}"

def parse_json_safe(text: str) -> dict:
    try:
        return json.loads(text)
    except Exception:
        return json.loads(extract_json_block(text) or "{}")

def get_few_shot_examples(
    feedback_file: str = "data/feedback.jsonl", 
    classify_file: str = "data/classify_log.jsonl", 
    max_positive: int = 2,
    max_negative: int = 1,
    format_as_text: bool = False
) -> Union[List[Dict[str, Any]], str]:
    """Extract few-shot examples from feedback data, prioritizing latest and most relevant examples.
    Efficiently stops once required number of examples are found.
    
    Args:
        feedback_file: Path to feedback JSONL file
        classify_file: Path to classify log JSONL file  
        max_positive: Maximum number of positive examples (upvoted)
        max_negative: Maximum number of negative examples (downvoted)
        format_as_text: If True, return formatted text for prompt insertion; if False, return raw examples
        
    Returns:
        List of example dictionaries if format_as_text=False, formatted string if format_as_text=True
    """
    positive_examples = []
    negative_examples = []
    
    try:
        # Get the project root directory (go up from rag/rag/ to project root)
        current_dir = os.path.dirname(os.path.dirname(__file__))
        feedback_path = os.path.join(current_dir, feedback_file)
        classify_path = os.path.join(current_dir, classify_file)
        
        if not os.path.exists(feedback_path) or not os.path.exists(classify_path):
            return "" if format_as_text else []
        
        # Early exit if no examples needed
        if max_positive == 0 and max_negative == 0:
            return "" if format_as_text else []
        
        # Read feedback in reverse order to get latest feedback first
        positive_requests = {}  # request_id -> feedback_data (latest feedback first)
        negative_requests = {}  # request_id -> feedback_data (latest feedback first)
        
        with open(feedback_path, 'r', encoding='utf-8') as f:
            feedback_lines = f.readlines()
        
        # Process feedback from latest to oldest (reverse order)
        for line in reversed(feedback_lines):
            if not line.strip():
                continue
                
            feedback = json.loads(line)
            request_id = feedback.get("request_id")
            vote = feedback.get("vote")
            
            # Only add if we haven't seen this request_id yet (keeping latest feedback)
            if vote == "up" and request_id not in positive_requests:
                positive_requests[request_id] = feedback
            elif vote == "down" and request_id not in negative_requests:
                negative_requests[request_id] = feedback
            
            # Early exit if we have enough feedback entries to potentially satisfy our quota
            # (We estimate we might not find all in classify_log, so we get a bit more)
            if len(positive_requests) >= max_positive * 2 and len(negative_requests) >= max_negative * 2:
                break
        
        # Early exit if no feedback available after processing
        if not positive_requests and not negative_requests:
            return "" if format_as_text else []
        
        # Now find corresponding classify examples - process all since we need to match request IDs
        seen_rule_combinations = set()
        
        with open(classify_path, 'r', encoding='utf-8') as f:
            classify_lines = f.readlines()
        
            # Process classify log from latest to oldest (reverse order)
            for line in reversed(classify_lines):
                if not line.strip():
                    continue
                    
                # Check if we have enough examples - early termination
                if len(positive_examples) >= max_positive and len(negative_examples) >= max_negative:
                    break
                    
                log_entry = json.loads(line)
                request_id = log_entry.get("request_id")
                rule_hits = tuple(sorted(log_entry.get("rule_hits", [])))  # Normalize rule order
                
                # Skip if we already have a similar rule combination for diversity
                if rule_hits in seen_rule_combinations:
                    continue
                
                # Check for positive examples (prioritize latest feedback with diverse rule combinations)
                if request_id in positive_requests and len(positive_examples) < max_positive:
                    confidence = log_entry.get("response", {}).get("confidence", 0.0)
                    
                    # Filter response to only include essential fields for few-shot learning
                    full_response = log_entry.get("response", {})
                    filtered_response = {
                        "needs_geo_logic": full_response.get("needs_geo_logic"),
                        "reasoning": full_response.get("reasoning"),
                        "confidence": full_response.get("confidence"),
                        "laws": full_response.get("laws", [])[:2]  # Limit to first 2 laws to keep concise
                    }
                    
                    example = {
                        "type": "positive",
                        "feature_text": log_entry.get("feature_text", ""),
                        "rule_hits": log_entry.get("rule_hits", []),
                        "response": filtered_response,
                        "feedback_note": "GOOD classification (upvoted by user) should increase confidence",
                        "confidence": confidence,
                        "timestamp": log_entry.get("ts", "")
                    }
                    positive_examples.append(example)
                    seen_rule_combinations.add(rule_hits)
                
                # Check for negative examples (prioritize latest feedback with diverse rule combinations)
                elif request_id in negative_requests and len(negative_examples) < max_negative:
                    confidence = log_entry.get("response", {}).get("confidence", 0.0)
                    
                    # Filter response to only include essential fields for few-shot learning
                    full_response = log_entry.get("response", {})
                    filtered_response = {
                        "needs_geo_logic": full_response.get("needs_geo_logic"),
                        "reasoning": full_response.get("reasoning"),
                        "confidence": full_response.get("confidence"),
                        "laws": full_response.get("laws", [])[:2]  # Limit to first 2 laws to keep concise
                    }
                    
                    example = {
                        "type": "negative", 
                        "feature_text": log_entry.get("feature_text", ""),
                        "rule_hits": log_entry.get("rule_hits", []),
                        "response": filtered_response,
                        "feedback_note": "Poor classification (downvoted by user) should decrease confidence",
                        "confidence": confidence,
                        "timestamp": log_entry.get("ts", "")
                    }
                    negative_examples.append(example)
                    seen_rule_combinations.add(rule_hits)
    
    except Exception as e:
        # Silently fail and return appropriate empty value
        return "" if format_as_text else []
    
    # Combine examples (positive first, then negative) - already latest first due to reverse processing
    all_examples = positive_examples + negative_examples
    
    # Return raw examples if not formatting as text
    if not format_as_text:
        return all_examples
    
    # Format as text for prompt insertion
    if not all_examples:
        return ""
    
    examples_text = "\n\nHere are examples of classification patterns (latest feedback first):\n"
    
    for i, example in enumerate(all_examples, 1):
        feature_preview = example.get('feature_text', '')[:200]
        if len(example.get('feature_text', '')) > 200:
            feature_preview += "..."
        
        # Add type indicator and feedback note
        type_indicator = "GOOD" if example["type"] == "positive" else "AVOID"
        confidence = example.get('confidence', 0.0)
        
        examples_text += f"\nExample {i} ({type_indicator} - Confidence: {confidence:.2f}):\n"
        examples_text += f"Feature: {feature_preview}\n"
        examples_text += f"Rules: {example.get('rule_hits', [])}\n"
        examples_text += f"Output: {json.dumps(example.get('response', {}), indent=2)}\n"
        examples_text += f"Note: {example.get('feedback_note', '')}\n"
    
    return examples_text
