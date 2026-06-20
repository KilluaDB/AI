"""
RAG Tool for the Multi-Agent Database Design System.

RAG here is a *dynamic few-shot retriever*: it finds the requirements most similar to the
current one and returns their worked relational schemas, so the design agents can use them as
few-shot examples. There is a single tool, `get_similar_examples`, registered in `RAG_TOOLS`.
"""

from typing_extensions import Annotated

from .fewshot_retriever import get_retriever


async def get_similar_examples(
    requirement: Annotated[
        str, "The requirement / NLP text to find similar worked examples for"
    ],
    top_k: Annotated[
        int, "How many similar examples to return (2-3 recommended)"
    ] = 3,
) -> str:
    """
    Retrieve the most similar past requirements together with their relational schemas.

    Use this at the start of a design task: pass the requirement text and you will get back the
    2-3 most similar examples (requirement -> tables with primary/foreign keys) to use as
    few-shot references for structuring entities, keys, and relationships.
    """
    try:
        retriever = get_retriever()
        results = retriever.search(requirement, top_k=top_k)
        if not results:
            return (
                "No similar examples found for this requirement. "
                "Proceed using general database design principles."
            )
        return retriever.format_as_fewshot(results)
    except Exception as e:
        return f"Error retrieving similar examples: {str(e)}"


# The few-shot retrieval tool group. The combined RAG_TOOLS list (few-shot + domain knowledge)
# is assembled in rag/__init__.py.
FEWSHOT_TOOLS = [get_similar_examples]
