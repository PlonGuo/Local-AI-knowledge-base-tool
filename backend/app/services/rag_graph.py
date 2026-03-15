"""LangGraph RAG StateGraph — 3-way pre-retrieval routing → retrieve → [rerank →] build_prompt → generate → END."""
from __future__ import annotations

from typing import Any, Literal, TypedDict

from langgraph.graph import END, StateGraph

from app.config import AppConfig
from app.services.hyde_service import generate_hypothetical_doc
from app.services.rag_service import RAGService


class RAGState(TypedDict, total=False):
    """State flowing through the RAG graph."""

    question: str
    k: int
    pre_retrieval_strategy: str  # "none" | "hyde" | "multi_query"
    use_reranker: bool
    hypothetical_doc: str
    pack_id: str
    chunks: list[dict[str, Any]]
    sources: list[str]
    messages: list[dict[str, str]]
    answer: str


def _pre_retrieval_route(state: RAGState) -> Literal["hyde", "multi_query", "retrieve"]:
    """Route based on pre_retrieval_strategy: hyde, multi_query, or retrieve (default)."""
    strategy = state.get("pre_retrieval_strategy", "none")
    if strategy == "hyde":
        return "hyde"
    if strategy == "multi_query":
        return "multi_query"
    return "retrieve"


def _post_retrieve_route(state: RAGState) -> Literal["rerank", "build_prompt"]:
    """Route after retrieve: rerank if use_reranker is True, else build_prompt."""
    if state.get("use_reranker", False):
        return "rerank"
    return "build_prompt"


def create_rag_graph(rag_service: RAGService, config: AppConfig, reranker_service=None):
    """Build and compile the RAG StateGraph.

    Nodes: [hyde|multi_query →] retrieve → [rerank →] build_prompt → generate → END
    Routing determined by pre_retrieval_strategy and use_reranker in input state.
    """

    async def hyde(state: RAGState) -> dict:
        hypothetical = await generate_hypothetical_doc(state["question"], config)
        return {"hypothetical_doc": hypothetical}

    async def multi_query(state: RAGState) -> dict:
        # Placeholder — will be implemented in Task 127
        return {}

    async def retrieve(state: RAGState) -> dict:
        k = state.get("k", 5)
        query = state.get("hypothetical_doc", state["question"])
        pack_id = state.get("pack_id")
        retrieve_kwargs: dict[str, Any] = {"k": k}
        if pack_id:
            retrieve_kwargs["where"] = {"pack_id": pack_id}
        chunks = rag_service.retrieve(query, **retrieve_kwargs)
        sources = rag_service.extract_sources(chunks)
        return {"chunks": chunks, "sources": sources}

    async def rerank(state: RAGState) -> dict:
        if reranker_service is None:
            return {}
        reranked = reranker_service.rerank(state["question"], state["chunks"])
        sources = rag_service.extract_sources(reranked)
        return {"chunks": reranked, "sources": sources}

    async def build_prompt(state: RAGState) -> dict:
        messages = rag_service.build_prompt(state["question"], state["chunks"])
        return {"messages": messages}

    async def generate(state: RAGState) -> dict:
        answer = await rag_service.call_llm(state["messages"], config)
        return {"answer": answer}

    graph = StateGraph(RAGState)
    graph.add_node("hyde", hyde)
    graph.add_node("multi_query", multi_query)
    graph.add_node("retrieve", retrieve)
    graph.add_node("rerank", rerank)
    graph.add_node("build_prompt", build_prompt)
    graph.add_node("generate", generate)

    graph.add_conditional_edges(
        "__start__",
        _pre_retrieval_route,
        {"hyde": "hyde", "multi_query": "multi_query", "retrieve": "retrieve"},
    )
    graph.add_edge("hyde", "retrieve")
    graph.add_edge("multi_query", "retrieve")
    graph.add_conditional_edges(
        "retrieve",
        _post_retrieve_route,
        {"rerank": "rerank", "build_prompt": "build_prompt"},
    )
    graph.add_edge("rerank", "build_prompt")
    graph.add_edge("build_prompt", "generate")
    graph.add_edge("generate", END)

    return graph.compile()


def create_rag_prep_graph(rag_service: RAGService, config: AppConfig | None = None, reranker_service=None):
    """Build a prep-only graph: [hyde|multi_query →] retrieve → [rerank →] build_prompt → END.

    Returns chunks, sources, and messages without calling the LLM.
    Use this for streaming chat where LLM tokens are streamed separately.
    Config is required when pre_retrieval_strategy is 'hyde'.
    """

    async def hyde(state: RAGState) -> dict:
        hypothetical = await generate_hypothetical_doc(state["question"], config)
        return {"hypothetical_doc": hypothetical}

    async def multi_query(state: RAGState) -> dict:
        # Placeholder — will be implemented in Task 127
        return {}

    async def retrieve(state: RAGState) -> dict:
        k = state.get("k", 5)
        query = state.get("hypothetical_doc", state["question"])
        pack_id = state.get("pack_id")
        retrieve_kwargs: dict[str, Any] = {"k": k}
        if pack_id:
            retrieve_kwargs["where"] = {"pack_id": pack_id}
        chunks = rag_service.retrieve(query, **retrieve_kwargs)
        sources = rag_service.extract_sources(chunks)
        return {"chunks": chunks, "sources": sources}

    async def rerank(state: RAGState) -> dict:
        if reranker_service is None:
            return {}
        reranked = reranker_service.rerank(state["question"], state["chunks"])
        sources = rag_service.extract_sources(reranked)
        return {"chunks": reranked, "sources": sources}

    async def build_prompt(state: RAGState) -> dict:
        messages = rag_service.build_prompt(state["question"], state["chunks"])
        return {"messages": messages}

    graph = StateGraph(RAGState)
    graph.add_node("hyde", hyde)
    graph.add_node("multi_query", multi_query)
    graph.add_node("retrieve", retrieve)
    graph.add_node("rerank", rerank)
    graph.add_node("build_prompt", build_prompt)

    graph.add_conditional_edges(
        "__start__",
        _pre_retrieval_route,
        {"hyde": "hyde", "multi_query": "multi_query", "retrieve": "retrieve"},
    )
    graph.add_edge("hyde", "retrieve")
    graph.add_edge("multi_query", "retrieve")
    graph.add_conditional_edges(
        "retrieve",
        _post_retrieve_route,
        {"rerank": "rerank", "build_prompt": "build_prompt"},
    )
    graph.add_edge("rerank", "build_prompt")
    graph.add_edge("build_prompt", END)

    return graph.compile()
