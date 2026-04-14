import argparse
import json
import math
import random
from pathlib import Path

from sentence_transformers import CrossEncoder, InputExample
from sentence_transformers.cross_encoder.evaluation import CEBinaryClassificationEvaluator
from torch.utils.data import DataLoader


def load_jsonl_examples(path: Path) -> list[InputExample]:
    examples: list[InputExample] = []

    with path.open("r", encoding="utf-8") as handle:
        for line_no, raw in enumerate(handle, start=1):
            line = raw.strip()
            if not line:
                continue

            row = json.loads(line)
            query = (row.get("query") or "").strip()
            positives = row.get("positive") or row.get("positives") or []
            negatives = row.get("negatives") or []

            if isinstance(positives, str):
                positives = [positives]
            if isinstance(negatives, str):
                negatives = [negatives]

            if not query or not positives:
                raise ValueError(
                    f"Invalid row at line {line_no}. Each row must have query + positive(s)."
                )

            for pos in positives:
                text = (pos or "").strip()
                if text:
                    examples.append(InputExample(texts=[query, text], label=1.0))

            for neg in negatives:
                text = (neg or "").strip()
                if text:
                    examples.append(InputExample(texts=[query, text], label=0.0))

    if not examples:
        raise RuntimeError("No training examples found in dataset.")

    return examples


def split_examples(examples: list[InputExample], eval_ratio: float) -> tuple[list[InputExample], list[InputExample]]:
    random.shuffle(examples)
    eval_size = max(1, int(len(examples) * eval_ratio))
    eval_examples = examples[:eval_size]
    train_examples = examples[eval_size:]

    if not train_examples:
        train_examples = eval_examples

    return train_examples, eval_examples


def train(args: argparse.Namespace) -> None:
    data_path = Path(args.data_path)
    output_dir = Path(args.output_dir)

    if not data_path.exists():
        raise FileNotFoundError(f"Training dataset not found: {data_path}")

    all_examples = load_jsonl_examples(data_path)
    train_examples, eval_examples = split_examples(all_examples, args.eval_ratio)

    print(f"Loaded {len(all_examples)} labeled pairs")
    print(f"Train pairs: {len(train_examples)} | Eval pairs: {len(eval_examples)}")

    model = CrossEncoder(args.model_id, num_labels=1, max_length=args.max_length)
    train_loader = DataLoader(train_examples, shuffle=True, batch_size=args.batch_size)

    warmup_steps = math.ceil(len(train_loader) * args.epochs * 0.1)
    output_dir.mkdir(parents=True, exist_ok=True)

    if len(eval_examples) >= 2:
        evaluator = CEBinaryClassificationEvaluator.from_input_examples(
            eval_examples,
            name="dev",
        )
        model.fit(
            train_dataloader=train_loader,
            evaluator=evaluator,
            epochs=args.epochs,
            warmup_steps=warmup_steps,
            evaluation_steps=max(25, len(train_loader)),
            output_path=str(output_dir),
            use_amp=args.use_amp,
        )
    else:
        model.fit(
            train_dataloader=train_loader,
            epochs=args.epochs,
            warmup_steps=warmup_steps,
            output_path=str(output_dir),
            use_amp=args.use_amp,
        )

    print(f"Fine-tuned model saved to: {output_dir}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fine-tune a cross-encoder reranker.")
    parser.add_argument(
        "--data-path",
        default="data/train_pairs.sample.jsonl",
        help="Path to JSONL training data.",
    )
    parser.add_argument(
        "--model-id",
        default="cross-encoder/ms-marco-MiniLM-L-6-v2",
        help="Base cross-encoder model id or local path.",
    )
    parser.add_argument(
        "--output-dir",
        default="reranker/models/reranker_finetuned",
        help="Output directory for fine-tuned model.",
    )
    parser.add_argument("--epochs", type=int, default=2)
    parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument("--max-length", type=int, default=512)
    parser.add_argument("--eval-ratio", type=float, default=0.15)
    parser.add_argument(
        "--use-amp",
        action="store_true",
        help="Enable mixed precision training if supported by hardware.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    train(parse_args())
