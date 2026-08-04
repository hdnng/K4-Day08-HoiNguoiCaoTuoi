"""Run a reproducible RAGAS evaluation for the group RAG pipeline.

Usage:
    python -m group_project.evaluation.eval_pipeline

Set one provider in ``.env`` before running:
    GEMINI_API_KEY=...       # also install langchain-google-genai
    OPENAI_API_KEY=...
    OPENROUTER_API_KEY=...   # OpenAI-compatible endpoint

The script evaluates two retrieval configurations on the same golden dataset:
``hybrid_rerank`` (RRF + reranking) and ``hybrid_no_rerank`` (RRF only).
"""

import json
import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

GOLDEN_DATASET_PATH = Path(__file__).parent / "golden_dataset.json"
RESULTS_PATH = Path(__file__).parent / "results.md"
METRIC_NAMES = ("faithfulness", "answer_relevancy", "context_recall", "context_precision")


@dataclass(frozen=True)
class EvaluationConfig:
    """One intentionally comparable retrieval configuration."""

    key: str
    label: str
    use_reranking: bool
    description: str


CONFIGS = (
    EvaluationConfig(
        "hybrid_rerank",
        "Config A — Hybrid + RRF rerank",
        True,
        "Semantic retrieval và BM25 được gộp bằng RRF, sau đó rerank.",
    ),
    EvaluationConfig(
        "hybrid_no_rerank",
        "Config B — Hybrid không rerank",
        False,
        "Semantic retrieval và BM25 được gộp bằng RRF, không áp dụng bước rerank.",
    ),
)


def load_golden_dataset() -> list[dict]:
    """Load and validate the golden dataset contract used by RAGAS."""
    dataset = json.loads(GOLDEN_DATASET_PATH.read_text(encoding="utf-8"))
    required = {"question", "expected_answer", "expected_context"}
    if len(dataset) < 15:
        raise ValueError("golden_dataset.json must contain at least 15 test cases.")
    for index, item in enumerate(dataset, start=1):
        missing = required - item.keys()
        if missing:
            raise ValueError(f"Golden case {index} is missing: {', '.join(sorted(missing))}")
    return dataset


def _build_ragas_clients():
    """Return RAGAS LLM and embeddings wrappers for the configured provider."""
    from ragas.embeddings import LangchainEmbeddingsWrapper
    from ragas.llms import LangchainLLMWrapper

    openai_key = os.getenv("OPENAI_API_KEY")
    openrouter_key = os.getenv("OPENROUTER_API_KEY")
    gemini_key = os.getenv("GEMINI_API_KEY")

    if openai_key:
        from langchain_openai import ChatOpenAI, OpenAIEmbeddings

        model = os.getenv("EVAL_LLM_MODEL", "gpt-4o-mini")
        embedding_model = os.getenv("EVAL_EMBEDDING_MODEL", "text-embedding-3-small")
        return (
            LangchainLLMWrapper(ChatOpenAI(model=model, api_key=openai_key, temperature=0)),
            LangchainEmbeddingsWrapper(OpenAIEmbeddings(model=embedding_model, api_key=openai_key)),
        )

    if openrouter_key:
        from langchain_openai import ChatOpenAI, OpenAIEmbeddings

        base_url = "https://openrouter.ai/api/v1"
        model = os.getenv("EVAL_LLM_MODEL", "openai/gpt-4o-mini")
        embedding_model = os.getenv("EVAL_EMBEDDING_MODEL", "openai/text-embedding-3-small")
        return (
            LangchainLLMWrapper(
                ChatOpenAI(model=model, api_key=openrouter_key, base_url=base_url, temperature=0)
            ),
            LangchainEmbeddingsWrapper(
                OpenAIEmbeddings(model=embedding_model, api_key=openrouter_key, base_url=base_url)
            ),
        )

    if gemini_key:
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
        except ImportError as error:
            raise RuntimeError(
                "GEMINI_API_KEY is set, but langchain-google-genai is missing. "
                "Run: pip install langchain-google-genai"
            ) from error

        model = os.getenv("EVAL_LLM_MODEL", "gemini-2.5-flash")
        embedding_model = os.getenv("EVAL_EMBEDDING_MODEL", "models/gemini-embedding-001")
        return (
            LangchainLLMWrapper(
                ChatGoogleGenerativeAI(model=model, google_api_key=gemini_key, temperature=0)
            ),
            LangchainEmbeddingsWrapper(
                GoogleGenerativeAIEmbeddings(model=embedding_model, google_api_key=gemini_key)
            ),
        )

    raise RuntimeError(
        "Missing evaluator credentials. Set GEMINI_API_KEY, OPENAI_API_KEY, or OPENROUTER_API_KEY in .env."
    )


def _generate_records(golden_dataset: list[dict], config: EvaluationConfig) -> list[dict]:
    """Run the project generation pipeline once for every golden question."""
    from src.task10_generation import generate_with_citation

    records = []
    for index, item in enumerate(golden_dataset, start=1):
        print(f"[{config.key}] {index}/{len(golden_dataset)}: {item['question']}")
        response = generate_with_citation(item["question"], use_reranking=config.use_reranking)
        answer = response.get("answer", "")
        if answer.startswith("Error:"):
            raise RuntimeError(answer)
        contexts = [chunk.get("content", "") for chunk in response.get("sources", [])]
        records.append(
            {
                "id": item.get("id", f"GD-{index:02d}"),
                "question": item["question"],
                "answer": answer,
                "contexts": contexts,
                "ground_truth": item["expected_answer"],
                "expected_context": item["expected_context"],
                "retrieval_source": response.get("retrieval_source", "none"),
            }
        )
    return records


def evaluate_with_ragas(records: list[dict], llm, embeddings) -> tuple[dict, list[dict]]:
    """Evaluate generated records with the four required RAGAS metrics."""
    from datasets import Dataset
    from ragas import evaluate
    from ragas.metrics import answer_relevancy, context_precision, context_recall, faithfulness

    dataset = Dataset.from_list(
        [
            {
                "question": record["question"],
                "answer": record["answer"],
                "contexts": record["contexts"],
                "ground_truth": record["ground_truth"],
            }
            for record in records
        ]
    )
    evaluation = evaluate(
        dataset,
        metrics=[faithfulness, answer_relevancy, context_recall, context_precision],
        llm=llm,
        embeddings=embeddings,
        raise_exceptions=True,
    )
    frame = evaluation.to_pandas()
    metric_columns = {name: name for name in METRIC_NAMES if name in frame.columns}
    scores = {name: round(float(frame[name].mean()), 4) for name in metric_columns}
    rows = []
    for row_number, record in enumerate(records):
        row = {"id": record["id"], "question": record["question"]}
        row.update({name: round(float(frame.iloc[row_number][name]), 4) for name in metric_columns})
        row["retrieval_source"] = record["retrieval_source"]
        rows.append(row)
    return scores, rows


def _average(scores: dict) -> float:
    return round(sum(scores.get(name, 0.0) for name in METRIC_NAMES) / len(METRIC_NAMES), 4)


def export_results(results: dict) -> None:
    """Write a human-readable, evidence-based CP5 report to results.md."""
    config_a, config_b = CONFIGS
    scores_a = results[config_a.key]["scores"]
    scores_b = results[config_b.key]["scores"]
    avg_a, avg_b = _average(scores_a), _average(scores_b)
    lines = [
        "# RAG Evaluation Results",
        "",
        "## Framework và phạm vi",
        "",
        "- Framework: **RAGAS 0.1.21**",
        f"- Golden dataset: **{results['golden_count']}** câu hỏi bám theo 9 tài liệu trong corpus.",
        "- Metrics: Faithfulness, Answer Relevance, Context Recall, Context Precision.",
        "",
        "## Overall Scores",
        "",
        "| Metric | Config A: Hybrid + rerank | Config B: Hybrid không rerank | Δ (A - B) |",
        "|---|---:|---:|---:|",
    ]
    labels = {
        "faithfulness": "Faithfulness",
        "answer_relevancy": "Answer Relevance",
        "context_recall": "Context Recall",
        "context_precision": "Context Precision",
    }
    for name in METRIC_NAMES:
        a, b = scores_a.get(name, 0.0), scores_b.get(name, 0.0)
        lines.append(f"| {labels[name]} | {a:.4f} | {b:.4f} | {a - b:+.4f} |")
    lines.append(f"| **Average** | **{avg_a:.4f}** | **{avg_b:.4f}** | **{avg_a - avg_b:+.4f}** |")

    winner = config_a.label if avg_a >= avg_b else config_b.label
    lines += [
        "",
        "## A/B Comparison Analysis",
        "",
        f"- **{config_a.label}:** {config_a.description}",
        f"- **{config_b.label}:** {config_b.description}",
        f"- **Kết luận:** {winner} có điểm trung bình cao hơn trong lần chạy này. Chênh lệch cần được đọc cùng bottom-3 để xác định lỗi retrieval hay generation.",
        "",
        "## Worst Performers (Bottom 3)",
        "",
        "| # | Config | Question | Faithfulness | Relevance | Recall | Precision | Failure stage |",
        "|---:|---|---|---:|---:|---:|---:|---|",
    ]
    all_rows = []
    for config in CONFIGS:
        for row in results[config.key]["rows"]:
            quality = sum(row.get(name, 0.0) for name in METRIC_NAMES) / len(METRIC_NAMES)
            all_rows.append((quality, config.label, row))
    for rank, (_, label, row) in enumerate(sorted(all_rows, key=lambda item: item[0])[:3], start=1):
        stage = "retrieval" if row.get("context_recall", 1.0) < row.get("faithfulness", 1.0) else "generation"
        question = row["question"].replace("|", "\\|")
        lines.append(
            f"| {rank} | {label} | {question} | {row.get('faithfulness', 0):.4f} | "
            f"{row.get('answer_relevancy', 0):.4f} | {row.get('context_recall', 0):.4f} | "
            f"{row.get('context_precision', 0):.4f} | {stage} |"
        )
    lines += [
        "",
        "## Recommendations",
        "",
        "1. **Calibrate retrieval threshold:** dùng các câu có Context Recall thấp để điều chỉnh `SCORE_THRESHOLD` và `top_k`.",
        "2. **Cải thiện metadata/chunking:** tách rõ tiêu đề chính sách và điều khoản thời hạn để tăng Context Precision.",
        "3. **Củng cố prompt citation:** kiểm tra các câu có Faithfulness thấp và yêu cầu LLM chỉ khẳng định thông tin hiện diện trong context.",
        "",
        "## Reproduce",
        "",
        "```powershell",
        "python -m group_project.evaluation.eval_pipeline",
        "```",
    ]
    RESULTS_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    golden_dataset = load_golden_dataset()
    print(f"Loaded {len(golden_dataset)} golden test cases")
    llm, embeddings = _build_ragas_clients()
    results = {"golden_count": len(golden_dataset)}
    for config in CONFIGS:
        records = _generate_records(golden_dataset, config)
        scores, rows = evaluate_with_ragas(records, llm, embeddings)
        results[config.key] = {"scores": scores, "rows": rows}
        print(f"{config.key}: {scores}")
    export_results(results)
    print(f"Saved report: {RESULTS_PATH}")


if __name__ == "__main__":
    main()
