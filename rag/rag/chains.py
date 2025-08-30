from __future__ import annotations
import os
from typing import Dict, Any

from dotenv import load_dotenv
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
from langchain_core.output_parsers import StrOutputParser
from langchain.prompts import ChatPromptTemplate

from rag.utils import format_docs_for_context, parse_json_safe, get_few_shot_examples
from rag.retrieval import get_hybrid_retriever, rerank_docs
from rag.prompts import QA_SYSTEM, QA_USER, CLASSIFY_SYSTEM, CLASSIFY_USER

# --- LLM: Groq ---
from langchain_groq import ChatGroq

load_dotenv()

# Use GROQ_* vars; fall back to your previous OLLAMA_TEMPERATURE if present
def _chat(json_mode: bool = False):
    kwargs = {
        "model": os.getenv("GROQ_MODEL", "llama-3.1-8b-instant"),
        "temperature": float(os.getenv("GROQ_TEMPERATURE", os.getenv("OLLAMA_TEMPERATURE", "0.2"))),
        # "max_tokens": 2048,  # uncomment/tune if needed
    }
    if json_mode:
        # Strongly nudge strict JSON on Groq (OpenAI-compatible param)
        kwargs["model_kwargs"] = {"response_format": {"type": "json_object"}}
    return ChatGroq(**kwargs)

# ---------- QA CHAIN ----------
def make_qa_chain(k: int = 5, mmr: bool = False, regions: list[str] | None = None):
    """Input: a plain string question. Optionally filter retrieval by regions."""
    retriever = get_hybrid_retriever(k=k, mmr=mmr, regions=regions)
    prompt = ChatPromptTemplate.from_messages([
        ("system", QA_SYSTEM),
        ("user", QA_USER),
    ])
    llm = _chat(json_mode=False)
    parser = StrOutputParser()

    def _gather(inputs: Dict[str, Any]) -> Dict[str, Any]:
        q = inputs["question"]
        docs = retriever.invoke(q)
        try:
            docs = rerank_docs(q, docs, top_k=k)
        except Exception:
            pass
        return {"question": q, "context": format_docs_for_context(docs)}

    chain = (
        {"question": RunnablePassthrough()}
        | RunnableLambda(_gather)
        | prompt
        | llm
        | parser
    )
    return chain

# ---------- CLASSIFY CHAIN ----------
def make_classify_chain(k: int = 5, mmr: bool = False, regions: list[str] | None = None, use_few_shot: bool = True, max_positive: int = 1, max_negative: int = 1):
    """Input: dict with keys: feature_text (str), rule_hits (list[str]). Optionally filter retrieval by regions."""
    retriever = get_hybrid_retriever(k=k, mmr=mmr, regions=regions)
    
    # Get few-shot examples text with both positive and negative examples
    examples_text = get_few_shot_examples(
        max_positive=max_positive,
        max_negative=max_negative,
        format_as_text=True
    ) if use_few_shot else ""
    
    print(examples_text)  # Debug: show examples text

    prompt = ChatPromptTemplate.from_messages([
        ("system", CLASSIFY_SYSTEM),
        ("user", CLASSIFY_USER),
    ])
    llm = _chat(json_mode=True)  # JSON mode ON for strict output
    parser = StrOutputParser()

    def _prep(inputs: Dict[str, Any]) -> Dict[str, Any]:
        ft = inputs["feature_text"]
        rh = inputs.get("rule_hits", [])
        docs = retriever.invoke(ft)
        try:
            docs = rerank_docs(ft, docs, top_k=k)
        except Exception:
            pass
        ctx = format_docs_for_context(docs)
        return {"feature_text": ft, "rule_hits": rh, "context": ctx, "examples": examples_text}

    chain = (
        RunnableLambda(lambda x: x)  # passthrough
        | RunnableLambda(_prep)
        | prompt
        | llm
        | parser
        | parse_json_safe
    )
    return chain
