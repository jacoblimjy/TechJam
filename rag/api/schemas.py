# api/schemas.py
from __future__ import annotations
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

# ---- Ask (QA) ----
class AskRequest(BaseModel):
    question: str = Field(..., min_length=2)
    k: int = 5
    mmr: bool = False

class AskResponse(BaseModel):
    answer: str

# ---- Search (raw retrieval) ----
class SearchRequest(BaseModel):
    query: str
    k: int = 5
    mmr: bool = False

class SearchDoc(BaseModel):
    content: str
    metadata: Dict[str, Any]

class SearchResponse(BaseModel):
    docs: List[SearchDoc]

# ---- Classify (single) ----
class ClassifyRequest(BaseModel):
    feature_text: str = Field(..., min_length=2)
    rule_hits: List[str] = []
    k: int = 5
    mmr: bool = False
    regions: Optional[List[str]] = None  # optional override of inferred regions

class LawRef(BaseModel):
    name: str
    region: Optional[str] = None
    article_or_section: Optional[str] = None
    source: Optional[str] = None

class ClassifyResponse(BaseModel):
    needs_geo_logic: str  # yes|no|unclear
    reasoning: str
    laws: List[LawRef]
    confidence: float
    provenance: Dict[str, Any]

# ---- Classify (auto-rules) ----
class ClassifyAutoRequest(BaseModel):
    feature_text: str = Field(..., min_length=2)
    k: int = 5
    mmr: bool = False
    regions: Optional[List[str]] = None

# ---- Batch classify (auto) ----
class ArtifactTextOnly(BaseModel):
    feature_text: str

class BatchClassifyAutoRequest(BaseModel):
    rows: List[ArtifactTextOnly]
    k: int = 5
    mmr: bool = False
    csv: bool = False
    regions: Optional[List[str]] = None  # optional global override

# ---- Batch classify ----
class ArtifactItem(BaseModel):
    feature_text: str
    rule_hits: List[str] = []

class BatchClassifyRequest(BaseModel):
    rows: List[ArtifactItem]
    k: int = 5
    mmr: bool = False
    csv: bool = False  # if true, return CSV string too
    regions: Optional[List[str]] = None  # optional override applied to all rows

class BatchClassifyRow(BaseModel):
    feature_text: str
    needs_geo_logic: str
    reasoning: str
    laws: List[LawRef]
    confidence: float
    rule_hits: List[str]

class BatchClassifyResponse(BaseModel):
    rows: List[BatchClassifyRow]
    csv: Optional[str] = None

# ---- Feedback (review + logging) ----
class FeedbackRequest(BaseModel):
    # Link to a specific classification run (preferred)
    request_id: Optional[str] = None
    # Minimal reference if request_id is missing
    feature_text: Optional[str] = None
    verdict: Optional[str] = Field(default=None, description="Model's needs_geo_logic at time of review")
    vote: str = Field(..., description="'up' if correct, 'down' if incorrect")
    correction_needs_geo_logic: Optional[str] = Field(default=None, description="yes|no|unclear if proposing a correction")
    correction_reasoning: Optional[str] = None
    notes: Optional[str] = None
    rules_input: Optional[List[str]] = None
    regions: Optional[List[str]] = None

class FeedbackResponse(BaseModel):
    ok: bool
    saved_path: Optional[str] = None
