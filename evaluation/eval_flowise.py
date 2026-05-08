"""BLUE and ROUGE scores are heavily rely on
surface-level lexical overlaps, often fail to capture deeper nuances, resulting in poor performance
in tasks like story generation or instructional texts"""

import json
import re
import sys
import time
from collections import defaultdict
from pathlib import Path

import nltk
import requests
from bert_score import BERTScorer
from nltk.translate.bleu_score import SmoothingFunction, sentence_bleu
from openai import APIError, RateLimitError
from rouge_score import rouge_scorer

# Ensure NLTK resources are available
nltk.download("punkt_tab", quiet=True)


current_dir = Path(__file__).parent.resolve()
project_root = current_dir.parent.parent
sys.path.insert(0, str(project_root))

from llm_provider import LLMProvider

API_URL = "http://localhost:3000/api/v1/prediction/616c4ca5-330c-4068-bbd0-1d8fa9889449"

QUERY_MAX_ATTEMPTS = 3
QUERY_BACKOFF_SECONDS = (2, 5, 10)
JUDGE_MAX_ATTEMPTS = 4
JUDGE_BACKOFF_SECONDS = (5, 15, 45, 90)


def query(payload):
    last_error = None
    for attempt in range(QUERY_MAX_ATTEMPTS):
        try:
            response = requests.post(API_URL, json=payload, timeout=120)
            data = response.json()
        except (requests.RequestException, ValueError) as e:
            last_error = {"error": f"request failed: {e}"}
        else:
            if response.status_code < 500 and "text" in data:
                return data
            last_error = data
        if attempt < QUERY_MAX_ATTEMPTS - 1:
            time.sleep(QUERY_BACKOFF_SECONDS[attempt])
    return last_error if isinstance(last_error, dict) else {"error": str(last_error)}


DATASET_PATH = current_dir / "dataset-de.json"
RESULTS_PATH = current_dir / "results/eval_results_test_llama_3.3_70B_instruct_de.json"

_BERT_SCORERS: dict[str, BERTScorer] = {}


def _get_bert_scorer(language: str) -> BERTScorer:
    if language not in _BERT_SCORERS:
        if language == "de":
            _BERT_SCORERS[language] = BERTScorer(lang="de")
        else:
            _BERT_SCORERS[language] = BERTScorer(model_type="roberta-large", lang="en")
    return _BERT_SCORERS[language]


# Load dataset
def load_dataset(path: Path) -> list[dict]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


# Rouge evaluation
def compute_rouge(
    prediction: str,
    reference: str,
) -> dict:
    # see: https://medium.com/@prabhatzade/rouge-score-a-complete-tutorial-for-evaluating-text-summarization-models-a3a146417118
    scorer = rouge_scorer.RougeScorer(["rouge1", "rouge2", "rougeL"], use_stemmer=True)
    scores = scorer.score(reference, prediction)
    return {k: round(v.fmeasure, 4) for k, v in scores.items()}


# BLEU evaluation
def compute_bleu(prediction: str, reference: str) -> float:
    # see: https://www.nltk.org/_modules/nltk/translate/bleu_score.html
    ref_tokens = nltk.word_tokenize(reference, language="german")
    pred_tokens = nltk.word_tokenize(prediction, language="german")
    smoothie = SmoothingFunction().method1
    score = sentence_bleu([ref_tokens], pred_tokens, smoothing_function=smoothie)
    # print(score)
    return round(float(score), 4)


# BERTScore evaluation
def compute_bertscore(prediction: str, reference: str, language: str = "de") -> dict:
    scorer = _get_bert_scorer(language)
    P, R, F1 = scorer.score([prediction], [reference])
    return {
        "precision": round(P.item(), 4),
        "recall": round(R.item(), 4),
        "f1": round(F1.item(), 4),
    }


LLM_JUDGE_PROMPT = """Du bist ein strenger Evaluator für ein RAG-System über ELSTER (deutsches Steuerportal).

Bewerte die generierte Antwort im Vergleich zur Referenzantwort anhand dieser Kriterien:

1. **Korrektheit** (1-5): Ist die Antwort sachlich korrekt im Vergleich zur Referenz?
2. **Vollständigkeit** (1-5): Deckt die Antwort alle wichtigen Punkte der Referenz ab?
3. **Relevanz** (1-5): Ist die Antwort relevant zur gestellten Frage?

Antworte AUSSCHLIESSLICH mit diesem JSON-Format:
{{"correctness": <1-5>, "completeness": <1-5>, "relevance": <1-5>, "reasoning": "<kurze Begründung>"}}

Frage: {question}

Referenzantwort: {reference}"""


JUDGE_MODEL = "google/gemini-3-flash-preview"


def llm_judge(
    llm_provider: LLMProvider, question: str, prediction: str, reference: str
) -> dict:
    prompt = LLM_JUDGE_PROMPT.format(
        question=question, reference=reference, prediction=prediction
    )
    messages = [
        {"role": "system", "content": "Du bist ein Evaluator. Antworte nur mit JSON."},
        {"role": "user", "content": prompt},
    ]

    last_err: Exception | None = None
    for attempt in range(JUDGE_MAX_ATTEMPTS):
        try:
            res = llm_provider.generate_chat_completion(
                model=JUDGE_MODEL,
                messages=messages,
                temperature=0.0,
                max_tokens=512,
            )
            content = res.choices[0].message.content
            try:
                json_str = content[content.find("{") : content.rfind("}") + 1]
                return json.loads(json_str)
            except (json.JSONDecodeError, ValueError):
                return {
                    "correctness": 0,
                    "completeness": 0,
                    "relevance": 0,
                    "reasoning": f"Parse error: {content[:200]}",
                }
        except (RateLimitError, APIError) as e:
            last_err = e
            if attempt < JUDGE_MAX_ATTEMPTS - 1:
                time.sleep(JUDGE_BACKOFF_SECONDS[attempt])

    return {
        "correctness": 0,
        "completeness": 0,
        "relevance": 0,
        "reasoning": f"Judge call failed after {JUDGE_MAX_ATTEMPTS} attempts: {last_err}",
    }


def run_evaluation():
    print("Loading dataset...")
    dataset = load_dataset(DATASET_PATH)
    print(f"Loaded {len(dataset)} evaluation samples")

    print("Initializing RAG pipeline...")
    llm_provider = LLMProvider()

    results = []
    category_scores = defaultdict(lambda: defaultdict(list))

    for i, sample in enumerate(dataset):
        question = sample["question"]
        reference = sample["ground_truth"]
        category = sample.get("category", "Unknown")
        language = sample.get("language", "de")

        print(f"\n[{i + 1}/{len(dataset)}] {question[:80]}...")

        output = query(
            {
                "question": question,
            }
        )

        failed = "text" not in output
        if failed:
            error_msg = str(output)[:300]
            print(f"   FAILED: {error_msg}")
            prediction = ""
        else:
            # r for raw string
            pattern = r".*?(?=<ui)"
            match = re.search(pattern, output["text"], re.DOTALL)
            if match:
                prediction = match.group(0).strip()
            else:
                prediction = output["text"].strip()

        if failed:
            zero_judge = {
                "correctness": 0,
                "completeness": 0,
                "relevance": 0,
                "reasoning": "Pipeline failure — no prediction available",
            }
            zero_bert = {"precision": 0.0, "recall": 0.0, "f1": 0.0}
            result = {
                "question": question,
                "category": category,
                "reference": reference,
                "prediction": "",
                "failed": True,
                "error": error_msg,
                "rouge": {"rouge1": 0, "rouge2": 0, "rougeL": 0},
                "bleu": 0.0,
                "bertscore": zero_bert,
                "llm_judge": zero_judge,
            }
            results.append(result)
            category_scores[category]["failures"].append(1)
            continue

        rouge = compute_rouge(prediction, reference)
        bleu = compute_bleu(prediction, reference)
        judge = llm_judge(llm_provider, question, prediction, reference)
        bertscore = compute_bertscore(prediction, reference, language=language)

        result = {
            "question": question,
            "category": category,
            "reference": reference,
            "prediction": prediction,
            "failed": False,
            "rouge": rouge,
            "bleu": bleu,
            "bertscore": bertscore,
            "llm_judge": judge,
        }
        results.append(result)

        category_scores[category]["failures"].append(0)
        category_scores[category]["rouge1"].append(rouge["rouge1"])
        category_scores[category]["rouge2"].append(rouge["rouge2"])
        category_scores[category]["rougeL"].append(rouge["rougeL"])
        category_scores[category]["bleu"].append(bleu)
        category_scores[category]["bertscore_precision"].append(bertscore["precision"])
        category_scores[category]["bertscore_recall"].append(bertscore["recall"])
        category_scores[category]["bertscore_f1"].append(bertscore["f1"])
        for k in ["correctness", "completeness", "relevance"]:
            category_scores[category][k].append(judge.get(k, 0))

        print(
            f"   ROUGE-1: {rouge['rouge1']}  ROUGE-2: {rouge['rouge2']}  ROUGE-L: {rouge['rougeL']}  BLEU: {bleu}  "
            f"BERTS Precision: {bertscore['precision']}  BERTS Recall: {bertscore['recall']}  BERTS F1: {bertscore['f1']}  "
            f"Judge: C={judge.get('correctness', 0)} V={judge.get('completeness', 0)} R={judge.get('relevance', 0)}"
        )

    # Aggregate
    def avg(lst):
        return round(sum(lst) / len(lst), 4) if lst else 0

    def summarize(scores: dict) -> dict:
        failures = scores.get("failures", [])
        total = len(failures)
        n_failed = sum(failures)
        out = {
            "total": total,
            "failed": n_failed,
            "failure_rate": round(n_failed / total, 4) if total else 0,
        }
        for k, v in scores.items():
            if k == "failures":
                continue
            out[k] = avg(v)
        return out

    all_scores = defaultdict(list)
    for cat_scores in category_scores.values():
        for k, v in cat_scores.items():
            all_scores[k].extend(v)

    total_failed = sum(1 for r in results if r.get("failed"))
    summary = {
        "judge_model": JUDGE_MODEL,
        "total_samples": len(results),
        "failed_samples": total_failed,
        "failure_rate": round(total_failed / len(results), 4) if results else 0,
        "overall": summarize(all_scores),
        "per_category": {
            cat: summarize(scores) for cat, scores in category_scores.items()
        },
    }

    output = {"summary": summary, "results": results}

    with open(RESULTS_PATH, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    # Print summary
    print("\n" + "=" * 60)
    print("EVALUATION SUMMARY")
    print("=" * 60)
    print(f"Samples: {summary['total_samples']}")
    print(
        f"Failed:  {summary['failed_samples']} ({summary['failure_rate'] * 100:.1f}%)"
    )
    print(f"Judge:   {summary['judge_model']}")
    print(f"\nOverall Scores (failures excluded from averages):")
    for k, v in summary["overall"].items():
        print(f"  {k:20s}: {v}")
    print(f"\nPer Category:")
    for cat, scores in summary["per_category"].items():
        print(f"\n  {cat}:")
        for k, v in scores.items():
            print(f"    {k:20s}: {v}")

    print(f"\nResults saved to {RESULTS_PATH}")


if __name__ == "__main__":
    run_evaluation()
