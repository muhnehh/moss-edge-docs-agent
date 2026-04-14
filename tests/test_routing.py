from agent.chat_agent import MossEdgeAgent
from reranker.inference import ONNXReranker


def test_should_use_cloud_llm_threshold() -> None:
    assert ONNXReranker.should_use_cloud_llm(0.2, threshold=0.3)
    assert not ONNXReranker.should_use_cloud_llm(0.7, threshold=0.3)


def test_extract_local_answer_empty_docs() -> None:
    answer = MossEdgeAgent._extract_local_answer([])
    assert "could not find relevant information" in answer.lower()
