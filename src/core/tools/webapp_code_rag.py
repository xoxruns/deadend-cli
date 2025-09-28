from pydantic_ai import RunContext

from core.utils.structures import RagDeps



async def webapp_code_rag(context: RunContext[RagDeps], search_query: str) -> str:
    res = ""
    if len(context.deps.target) > 1:
        search_query += '\n The target supplied is: ' + context.deps.target
    
    embedding = await context.deps.openai.embeddings.create(
        input=search_query, 
        model='text-embedding-3-small'
    ) 

    assert len(embedding.data) == 1, (
        f'Expected 1 embedding, got {len(embedding.data)}, doc query: {search_query!r}'
    )
    embedding = embedding.data[0].embedding

    results = await context.deps.rag.similarity_search_code_chunk(
        query_embedding=embedding, 
        limit=5
    )
    for chunk, similarity in results: 
        res = res + '\n' + chunk.code_content
    
    return res
