<!-- markdownlint-disable MD033 MD041 -->

<div align="center">

<img src="assets/moss_logo_cyan.png" alt="Moss" width="80" />

# Moss Edge Docs Agent

### Sub-20ms on-device AI agent using Moss + ONNX reranking

[![License](https://img.shields.io/badge/License-BSD_2--Clause-orange.svg)](https://opensource.org/licenses/BSD-2-Clause)

</div>

---

> A real-time AI agent that answers questions using Moss documentation with **sub-20ms latency** and **minimal cloud dependency**.

Built as a demonstration of what’s possible when combining:
- Moss for sub-10ms semantic retrieval  
- ONNX-quantized cross-encoder for on-device reranking  
- Local-first agent design for instant responses  

---

## Why This Project Exists

Modern AI agents have a hidden bottleneck:

User question → vector DB → 200–800ms delay → response

That delay breaks conversational flow.

Moss solves retrieval latency.  
This system focuses on optimizing the rest of the pipeline.

---

## What This Adds on Top of Moss

Moss provides fast retrieval, but real agents still require:

- Determining which documents are truly relevant  
- Deciding whether a query can be answered locally  
- Maintaining consistently low latency  

### Additions:

- ONNX reranking (cross-encoder, on-device)  
- Query routing (local vs cloud decision)  
- End-to-end latency optimization  
- Benchmarking with measurable results  

---

## Architecture

```
[User Question]
        ↓
Moss Retrieval (<10ms)
        ↓
ONNX Reranker (~3ms, on-device)
        ↓
Routing Decision
   ├── Local Answer (instant)
   └── Cloud LLM (fallback)
```

---

## Benchmarks (M1 MacBook)

| Component         | Median | P95   |
|------------------|--------|-------|
| Moss retrieval   | 8 ms   | 12 ms |
| ONNX reranking   | 3 ms   | 6 ms  |
| Total (local)    | 11 ms  | 18 ms |

- ~68% of queries answered locally  
- Majority of queries require no network call  

---

## Tech Stack

- Retrieval: Moss SDK (`inferedge-moss`)
- Reranker: `cross-encoder/ms-marco-MiniLM-L-6-v2`
- Inference: ONNX Runtime (INT8 quantized)
- Agent Loop: Async Python
- Fallback LLM: OpenAI (`gpt-4o-mini`)

---

## Quickstart

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Set environment variables

```bash
cp .env.example .env
```

Add:

```
MOSS_PROJECT_ID=your_id
MOSS_PROJECT_KEY=your_key
OPENAI_API_KEY=your_key
```

---

### 3. Index documentation

```bash
python moss_integration/moss_indexer.py
```

---

### 4. Run the agent

```bash
python agent/chat_agent.py
```

Example:

```
> How do I create an index in Moss?
```

---

### 5. Run benchmark

```bash
python metrics/benchmark.py
```

---

## Project Structure

```
moss-edge-docs-agent/
├── agent/
│   └── chat_agent.py
├── moss_integration/
│   └── moss_indexer.py
├── reranker/
│   ├── inference.py
│   ├── export_to_onnx.py
│   └── models/
├── metrics/
│   └── benchmark.py
├── data/
│   └── corpus.json
├── README.md
└── requirements.txt
```

---

## Key Idea

Retrieval is no longer the bottleneck. Decision-making is.

When retrieval becomes near-instant, the next constraint is efficient, local reasoning.

---

## Future Improvements

- Voice interface (STT + TTS)  
- Local answer synthesis using small LLMs  
- Fine-tuned reranker for domain-specific queries  
- Web interface (Next.js)  

---

## Built On

- Moss — real-time semantic search runtime  
- HuggingFace Transformers + Optimum  
- ONNX Runtime  

---

## Motivation

This system explores what real-time AI agents look like when:

- Retrieval latency is negligible  
- Models run locally  
- Latency is treated as a primary design constraint  

---

## License

BSD 2-Clause (inherits from Moss)

---

<div align="center">
  <sub>Edge AI system built on top of Moss</sub>
</div>
