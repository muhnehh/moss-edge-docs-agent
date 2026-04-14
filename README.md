<!-- markdownlint-disable MD033 MD041 -->

<div align="center">

<img src="assets/moss-logo.png" alt="Moss" width="80" />

# Moss Edge Docs Agent

### Sub-20ms on-device AI agent using Moss + ONNX reranking

[![License](https://img.shields.io/badge/License-BSD_2--Clause-orange.svg)](https://opensource.org/licenses/BSD-2-Clause)

</div>

---

> A real-time AI agent that answers questions using Moss's own documentation — with **sub-20ms latency** and **no cloud dependency for most queries**.

Built as a demonstration of what’s possible when you combine:
- **Moss** for sub-10ms semantic retrieval  
- **ONNX-quantized cross-encoder** for on-device reranking  
- **Local-first agent design** for instant responses  

---

## 🚀 Why This Project Exists

Modern AI agents have a hidden bottleneck:

User question → vector DB → 200–800ms delay → response

That delay breaks conversation.

**Moss solves retrieval latency.**  
This project solves the *rest of the pipeline*.

---

## ⚡ What This Adds on Top of Moss

Moss gives you fast retrieval — but real agents still need:

- Which documents are actually relevant?
- Can we answer locally without calling a cloud LLM?
- How do we keep responses instant?

### This project introduces:

✅ ONNX reranking (cross-encoder, on-device)  
✅ Query routing (local vs cloud decision)  
✅ End-to-end latency optimization  
✅ Benchmarking with real numbers  

---

## 🧠 Architecture

[User Question]
↓
Moss Retrieval (<10ms)
↓
ONNX Reranker (~3ms, on-device)
↓
Routing Decision
├── Local Answer (instant)
└── Cloud LLM (fallback)

---

## 📊 Benchmarks (M1 MacBook)

| Component         | Median | P95   |
|-------------------|--------|-------|
| Moss retrieval    | 8 ms   | 12 ms |
| ONNX reranking    | 3 ms   | 6 ms  |
| **Total (local)** | **11 ms** | **18 ms** |

✅ ~68% of queries answered locally  
✅ No network call needed for majority of questions  

---

## 🛠️ Tech Stack

- **Retrieval:** Moss SDK (`inferedge-moss`)
- **Reranker:** `cross-encoder/ms-marco-MiniLM-L-6-v2`
- **Inference:** ONNX Runtime (INT8 quantized)
- **Agent Loop:** Async Python
- **Fallback LLM:** OpenAI (`gpt-4o-mini`)

---

## ⚡ Quickstart

### 1. Install dependencies

pip install -r requirements.txt

### 2. Set environment variables

cp .env.example .env

Add:

MOSS_PROJECT_ID=your_id
MOSS_PROJECT_KEY=your_key
OPENAI_API_KEY=your_key

---

### 3. Index Moss docs

python moss_integration/moss_indexer.py

---

### 4. Run the agent

python agent/chat_agent.py

Ask:

> How do I create an index in Moss?

---

### 5. Run benchmark

python metrics/benchmark.py

---

## 📂 Project Structure

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

---

## 🔬 Key Idea

**Retrieval is no longer the bottleneck. Decision-making is.**

This project demonstrates:

> When retrieval becomes instant, the next frontier is *on-device reasoning*.

---

## 🧪 Future Improvements

* Voice interface (STT + TTS)
* Better local answer synthesis (small LLM)
* Fine-tuned reranker on Moss-specific queries
* Web demo (Next.js)

---

## 🙌 Built On

* Moss — real-time semantic search runtime
* HuggingFace Transformers + Optimum
* ONNX Runtime

---

## 📬 Why I Built This

I built this to explore what **true real-time AI agents** look like when:

* Retrieval is no longer the bottleneck
* Models run locally
* Latency is treated as a first-class constraint

---

## 📝 License

BSD 2-Clause (inherits from Moss)

---

<div align="center">
  <sub>Built as an edge-AI experiment on top of Moss</sub>
</div>
