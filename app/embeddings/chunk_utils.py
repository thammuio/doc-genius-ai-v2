from sentence_transformers import SentenceTransformer
import os
from app.utils.constants import EMBEDDING_MODEL_REPO
import app.embeddings.embeddings_utils as model_embedding
from pymilvus import connections, Collection

# Get embeddings for a user question and query Milvus vector DB for nearest knowledge base chunk
def get_nearest_chunk_from_milvus_vectordb(vector_db_collection, question):
    # Generate embedding for user question
    question_embedding = model_embedding.get_embeddings(question)

    # Connect to the Milvus collection
    collection = Collection(name="retail_kb")
    
    # Define search attributes for Milvus vector DB
    vector_db_search_params = {"metric_type": "IP", "params": {"nprobe": 10}}
    
    # Execute search and get nearest vector
    nearest_vectors = collection.search(
        data=[question_embedding],
        anns_field="embedding",
        param=vector_db_search_params,
        limit=1,
        expr=None, 
        output_fields=['content'],  # Retrieve the content directly from Milvus
        consistency_level="Strong"
    )

    # Return the content directly from Milvus
    response = ""
    for f in nearest_vectors[0]:
        response += f.entity.get('content')  # Directly accessing the content field
    
    return response



# Get embeddings for a user question and query Pinecone vector DB for nearest knowledge base chunk
def get_nearest_chunk_from_pinecone_vectordb(index, question):
    # Generate embedding for user question with embedding model
    retriever = SentenceTransformer(EMBEDDING_MODEL_REPO)
    xq = retriever.encode([question]).tolist()
    xc = index.query(xq, top_k=5,
                 include_metadata=True)
    
    matching_files = []
    for match in xc['matches']:
        # extract the 'file_path' within 'metadata'
        file_path = match['metadata']['file_path']
        matching_files.append(file_path)

    # Return text of the nearest knowledge base chunk 
    # Note that this ONLY uses the first matching document for semantic search. matching_files holds the top results so you can increase this if desired.
    response = load_context_chunk_from_data(matching_files[0])
    return response
  
# Return the Knowledge Base doc based on Knowledge Base ID (relative file path)
def load_context_chunk_from_data(id_path):
    try:
        with open(id_path, "r") as f: # Open file in read mode
            return f.read()
    except FileNotFoundError:
        return f"Error: The file {id_path} was not found."