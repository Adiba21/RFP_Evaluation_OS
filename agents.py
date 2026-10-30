import io
import json
import uuid
from typing import List, Dict, Any, Tuple
from pypdf import PdfReader
from pydantic import BaseModel
from google import genai
from google.genai import types

class CriterionScore(BaseModel):
    criterion_id: int
    score: float
    max_score: float
    justification: str
    evidence: str

class SupplierEvaluation(BaseModel):
    supplier_name: str
    criteria: List[CriterionScore]
    overall_summary: str

class DocumentTool:
    @staticmethod
    def extract_text(pdf_file) -> str:
        if isinstance(pdf_file, bytes):
            pdf_file = io.BytesIO(pdf_file)
        reader = PdfReader(pdf_file)
        text = "\n".join([page.extract_text() or "" for page in reader.pages])
        return text.strip()

class ValidationTool:
    @staticmethod
    def normalize_and_validate(raw_data: Dict[str, Any], active_criteria: List[Dict[str, Any]]) -> Tuple[Dict[str, Any], List[str]]:
        warnings = []
        valid_criteria_map = {c["criterion_id"]: c for c in active_criteria}
        normalized_criteria = []
        parsed_criteria = {c.get("criterion_id"): c for c in raw_data.get("criteria", [])}

        for crit_id, crit_def in valid_criteria_map.items():
            if crit_id not in parsed_criteria:
                warnings.append(f"Missing criterion ID {crit_id} ({crit_def['name']}). Injected default score 0.0.")
                normalized_criteria.append({
                    "criterion_id": crit_id,
                    "score": 0.0,
                    "max_score": crit_def["max_score"],
                    "justification": "Criterion was missing in LLM response.",
                    "evidence": "N/A"
                })
            else:
                c_item = parsed_criteria[crit_id]
                score = float(c_item.get("score", 0.0))
                max_s = float(crit_def["max_score"])
                if score < 0.0:
                    score = 0.0
                elif score > max_s:
                    score = max_s
                
                normalized_criteria.append({
                    "criterion_id": crit_id,
                    "score": score,
                    "max_score": max_s,
                    "justification": c_item.get("justification", "No justification provided."),
                    "evidence": c_item.get("evidence", "No evidence extracted.")
                })

        return {
            "supplier_name": raw_data.get("supplier_name", "Unknown Supplier"),
            "criteria": normalized_criteria,
            "overall_summary": raw_data.get("overall_summary", "Evaluation complete.")
        }, warnings

class RankingTool:
    @staticmethod
    def compute_benchmarks_and_ranks(evaluations: List[Dict[str, Any]], active_criteria: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        benchmarks = {}
        for c in active_criteria:
            c_id = c["criterion_id"]
            benchmarks[c_id] = max([
                next(item["score"] for item in e["criteria"] if item["criterion_id"] == c_id)
                for e in evaluations
            ], default=0.0)

        weight_map = {c["criterion_id"]: c["weight"] for c in active_criteria}

        for e in evaluations:
            abs_score = 0.0
            weighted_relative_sum = 0.0
            detailed_breakdown = []

            for c_item in e["criteria"]:
                c_id = c_item["criterion_id"]
                w = weight_map.get(c_id, 0.0)
                score = c_item["score"]
                max_score = c_item["max_score"]

                abs_score += (score / max_score) * w
                bm = benchmarks[c_id]
                gap = score - bm
                rel_pct = (score / bm * 100.0) if bm > 0 else (100.0 if score == 0 else 0.0)
                weighted_relative_sum += rel_pct * w

                detailed_breakdown.append({
                    "criterion_id": c_id,
                    "criterion_name": next(c["name"] for c in active_criteria if c["criterion_id"] == c_id),
                    "score": score,
                    "max_score": max_score,
                    "weight": w,
                    "benchmark": bm,
                    "gap": round(gap, 2),
                    "relative_pct": round(rel_pct, 2),
                    "justification": c_item["justification"],
                    "evidence": c_item["evidence"]
                })

            e["detailed_breakdown"] = detailed_breakdown
            e["absolute_score"] = round(abs_score * 100.0, 2)
            e["ppi"] = round(weighted_relative_sum, 2)

        def sort_key(s):
            return (-s["ppi"], s["submission_date"], -s["experience_rating"], s["supplier_name"])

        sorted_evaluations = sorted(evaluations, key=sort_key)
        for rank, s in enumerate(sorted_evaluations, start=1):
            s["final_rank"] = rank

        return sorted_evaluations

class OrchestratorAgent:
    def __init__(self, api_key: str):
        self.client = genai.Client(api_key=api_key)

    def evaluate_proposal(self, supplier_meta: Dict[str, Any], doc_text: str, active_criteria: List[Dict[str, Any]]) -> Tuple[Dict[str, Any], List[str]]:
        criteria_prompt_part = "\n".join([
            f"- Criterion ID {c['criterion_id']}: {c['name']} (Max Score: {c['max_score']}). Description: {c['description']}"
            for c in active_criteria
        ])

        system_instruction = (
            "You are an impartial RFP Evaluation Agent. Evaluate the supplier document based solely on the text provided. "
            "Score each criterion strictly within [0, max_score]. Ground your evaluation in explicit facts and quotes from the text. "
            "You MUST output valid JSON complying with the requested schema."
        )

        user_content = f"""
Supplier Name: {supplier_meta['supplier_name']}

ACTIVE EVALUATION CRITERIA:
{criteria_prompt_part}

SUPPLIER PROPOSAL DOCUMENT TEXT:
\"\"\"
{doc_text}
\"\"\"

Return a valid JSON object matching the requested schema. Evaluate every single active criterion.
"""

        response = self.client.models.generate_content(
            model='gemini-2.5-flash',
            contents=user_content,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                response_mime_type="application/json",
                response_schema=SupplierEvaluation,
                temperature=0.0
            )
        )

        raw_json = json.loads(response.text)
        validated_result, warnings = ValidationTool.normalize_and_validate(raw_json, active_criteria)
        validated_result["submission_date"] = supplier_meta["submission_date"]
        validated_result["experience_rating"] = supplier_meta["experience_rating"]
        validated_result["warnings"] = warnings
        return validated_result, warnings

    def run_batch_evaluation(self, batch_inputs: List[Dict[str, Any]], active_criteria: List[Dict[str, Any]]) -> Tuple[str, List[Dict[str, Any]]]:
        rfp_run_id = f"RUN-{uuid.uuid4().hex[:8].upper()}"
        evaluated_proposals = []

        for item in batch_inputs:
            text = DocumentTool.extract_text(item["pdf_bytes"])
            eval_res, _ = self.evaluate_proposal(item, text, active_criteria)
            evaluated_proposals.append(eval_res)

        ranked_results = RankingTool.compute_benchmarks_and_ranks(evaluated_proposals, active_criteria)
        return rfp_run_id, ranked_results
