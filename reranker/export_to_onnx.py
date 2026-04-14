import argparse
from pathlib import Path

from optimum.onnxruntime import ORTModelForSequenceClassification, ORTQuantizer
from optimum.onnxruntime.configuration import AutoQuantizationConfig
from transformers import AutoTokenizer

DEFAULT_MODEL_ID = "cross-encoder/ms-marco-MiniLM-L-6-v2"
DEFAULT_RAW_DIR = Path("reranker/models/reranker_onnx")
DEFAULT_QUANT_DIR = Path("reranker/models/reranker_onnx_quantized")


def get_quant_config(target: str):
    if target == "arm64":
        return AutoQuantizationConfig.arm64(is_static=False, per_channel=False)
    return AutoQuantizationConfig.avx2(is_static=False, per_channel=False)


def export_and_quantize(
    source_model: str,
    raw_dir: Path,
    quant_dir: Path,
    quant_target: str,
) -> None:
    raw_dir.mkdir(parents=True, exist_ok=True)

    print("Exporting model to ONNX...")
    model = ORTModelForSequenceClassification.from_pretrained(source_model, export=True)
    tokenizer = AutoTokenizer.from_pretrained(source_model)
    model.save_pretrained(raw_dir)
    tokenizer.save_pretrained(raw_dir)

    print("Quantizing model to INT8...")
    quantizer = ORTQuantizer.from_pretrained(str(raw_dir))
    qconfig = get_quant_config(quant_target)
    quantizer.quantize(save_dir=str(quant_dir), quantization_config=qconfig)
    tokenizer.save_pretrained(quant_dir)

    print(f"ONNX export saved to: {raw_dir}")
    print(f"Quantized model saved to: {quant_dir}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Export and quantize reranker model to ONNX.")
    parser.add_argument(
        "--source-model",
        default=DEFAULT_MODEL_ID,
        help="Source model id or local fine-tuned model path.",
    )
    parser.add_argument(
        "--raw-dir",
        default=str(DEFAULT_RAW_DIR),
        help="Output directory for raw ONNX export.",
    )
    parser.add_argument(
        "--quant-dir",
        default=str(DEFAULT_QUANT_DIR),
        help="Output directory for quantized ONNX model.",
    )
    parser.add_argument(
        "--quant-target",
        choices=["avx2", "arm64"],
        default="avx2",
        help="Quantization preset for your target CPU architecture.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    export_and_quantize(
        source_model=args.source_model,
        raw_dir=Path(args.raw_dir),
        quant_dir=Path(args.quant_dir),
        quant_target=args.quant_target,
    )
