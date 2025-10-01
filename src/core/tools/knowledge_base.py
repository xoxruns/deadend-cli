from pydantic_ai import RunContext
from core.utils.structures import RagDeps


async def knowledge_rag(
        context: RunContext[RagDeps],
        search_query: str
        ) -> str:
    res = ""
    embedding = await context.deps.openai.embeddings.create(
        input=search_query,
        model='text-embedding-3-small'
    ) 
    assert len(embedding.data) == 1, (
        f'Expected 1 embedding, got {len(embedding.data)}, doc query: {search_query!r}'
    )
    embedding = embedding.data[0].embedding

    results = await context.deps.rag.similarity_search_knowledge_base(
        query_embedding=embedding, 
        limit=10
    )
    for chunk, similarity in results: 
        res = res + '\n' + chunk.content
    
    return res