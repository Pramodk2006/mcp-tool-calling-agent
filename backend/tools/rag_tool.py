"""
RAG (Retrieval-Augmented Generation) Tool for MCP Agent
Connects with vector database to perform document retrieval and answer generation
"""
import json
import logging
import os
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime
import numpy as np
from sentence_transformers import SentenceTransformer
import faiss
import pickle
import openai

logger = logging.getLogger(__name__)

@dataclass
class Document:
    id: str
    content: str
    metadata: Dict[str, Any]
    embedding: Optional[np.ndarray] = None

class RAGTool:
    """Retrieval-Augmented Generation tool with vector search"""
    
    def __init__(self, openai_api_key: Optional[str] = None, index_path: str = "rag_index"):
        self.name = "rag_tool"
        self.description = "Search documents and generate answers using retrieval-augmented generation"
        self.openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        self.index_path = index_path
        
        # Initialize sentence transformer for embeddings
        self.encoder = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Initialize FAISS index
        self.dimension = 384  # Dimension of all-MiniLM-L6-v2 embeddings
        self.index = faiss.IndexFlatIP(self.dimension)  # Inner Product (cosine similarity)
        self.documents = []
        
        # Load existing index if available
        self._load_index()
        
        if self.openai_api_key:
            openai.api_key = self.openai_api_key
        
    def get_schema(self) -> Dict[str, Any]:
        """Return the JSON schema for this tool"""
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": {
                "type": "object",
                "properties": {
                    "question": {
                        "type": "string",
                        "description": "The question to search for and answer"
                    },
                    "top_k": {
                        "type": "integer",
                        "description": "Number of relevant documents to retrieve (default: 3)",
                        "default": 3,
                        "minimum": 1,
                        "maximum": 10
                    },
                    "min_score": {
                        "type": "number",
                        "description": "Minimum similarity score for retrieved documents (default: 0.3)",
                        "default": 0.3,
                        "minimum": 0.0,
                        "maximum": 1.0
                    },
                    "generate_answer": {
                        "type": "boolean",
                        "description": "Whether to generate an answer using LLM (default: true)",
                        "default": True
                    }
                },
                "required": ["question"]
            },
            "output_schema": {
                "type": "object",
                "properties": {
                    "success": {"type": "boolean"},
                    "answer": {"type": "string"},
                    "retrieved_documents": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "id": {"type": "string"},
                                "content": {"type": "string"},
                                "score": {"type": "number"},
                                "metadata": {"type": "object"}
                            }
                        }
                    },
                    "total_documents": {"type": "integer"},
                    "question": {"type": "string"},
                    "timestamp": {"type": "string"},
                    "error": {"type": "string"}
                }
            }
        }
    
    def execute(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the RAG tool"""
        try:
            question = arguments.get("question", "").strip()
            top_k = arguments.get("top_k", 3)
            min_score = arguments.get("min_score", 0.3)
            generate_answer = arguments.get("generate_answer", True)
            
            if not question:
                return {
                    "success": False,
                    "error": "Question parameter is required",
                    "timestamp": datetime.now().isoformat()
                }
            
            if self.index.ntotal == 0:
                # If no documents in index, add some sample documents
                self._add_sample_documents()
            
            logger.info(f"RAG search for question: {question}")
            
            # Retrieve relevant documents
            retrieved_docs = self._retrieve_documents(question, top_k, min_score)
            
            # Generate answer if requested and LLM is available
            answer = ""
            if generate_answer:
                if self.openai_api_key and retrieved_docs:
                    answer = self._generate_answer(question, retrieved_docs)
                else:
                    answer = self._generate_simple_answer(question, retrieved_docs)
            
            return {
                "success": True,
                "answer": answer,
                "retrieved_documents": [
                    {
                        "id": doc["id"],
                        "content": doc["content"][:500] + "..." if len(doc["content"]) > 500 else doc["content"],
                        "score": doc["score"],
                        "metadata": doc["metadata"]
                    }
                    for doc in retrieved_docs
                ],
                "total_documents": self.index.ntotal,
                "question": question,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in RAG execution: {str(e)}")
            return {
                "success": False,
                "error": f"RAG execution error: {str(e)}",
                "question": arguments.get("question", ""),
                "timestamp": datetime.now().isoformat()
            }
    
    def _retrieve_documents(self, query: str, top_k: int, min_score: float) -> List[Dict[str, Any]]:
        """Retrieve relevant documents using vector similarity search"""
        try:
            # Generate query embedding
            query_embedding = self.encoder.encode([query], normalize_embeddings=True)
            
            # Search in FAISS index
            scores, indices = self.index.search(query_embedding, min(top_k, self.index.ntotal))
            
            retrieved = []
            for i, (score, idx) in enumerate(zip(scores[0], indices[0])):
                if score >= min_score and idx < len(self.documents):
                    doc = self.documents[idx]
                    retrieved.append({
                        "id": doc.id,
                        "content": doc.content,
                        "score": float(score),
                        "metadata": doc.metadata
                    })
            
            return retrieved
            
        except Exception as e:
            logger.error(f"Error retrieving documents: {str(e)}")
            return []
    
    def _generate_answer(self, question: str, retrieved_docs: List[Dict[str, Any]]) -> str:
        """Generate answer using OpenAI API and retrieved context"""
        try:
            if not retrieved_docs:
                return "No relevant documents found to answer the question."
            
            # Prepare context from retrieved documents
            context_parts = []
            for doc in retrieved_docs[:3]:  # Use top 3 documents
                context_parts.append(f"Document {doc['id']}: {doc['content']}")
            
            context = "\n\n".join(context_parts)
            
            prompt = f"""Based on the following documents, please answer the question. If the answer cannot be found in the documents, say so clearly.

Context Documents:
{context}

Question: {question}

Answer:"""

            response = openai.Completion.create(
                engine="text-davinci-003",
                prompt=prompt,
                max_tokens=300,
                temperature=0.7,
                stop=None
            )
            
            return response.choices[0].text.strip()
            
        except Exception as e:
            logger.warning(f"Error generating LLM answer: {str(e)}")
            return self._generate_simple_answer(question, retrieved_docs)
    
    def _generate_simple_answer(self, question: str, retrieved_docs: List[Dict[str, Any]]) -> str:
        """Generate simple extractive answer when LLM is not available"""
        if not retrieved_docs:
            return "No relevant documents found to answer the question."
        
        # Simple extractive approach - return most relevant document snippet
        best_doc = retrieved_docs[0]
        
        # Try to find the most relevant sentence
        sentences = best_doc["content"].split('. ')
        question_words = set(question.lower().split())
        
        best_sentence = ""
        best_overlap = 0
        
        for sentence in sentences:
            sentence_words = set(sentence.lower().split())
            overlap = len(question_words.intersection(sentence_words))
            if overlap > best_overlap:
                best_overlap = overlap
                best_sentence = sentence
        
        if best_sentence:
            return f"Based on the retrieved documents: {best_sentence}..."
        else:
            # Fallback to first few sentences of best document
            first_sentences = '. '.join(sentences[:2])
            return f"Based on the retrieved documents: {first_sentences}..."
    
    def _add_sample_documents(self):
        """Add sample documents to demonstrate RAG functionality"""
        sample_docs = [
            Document(
                id="doc_1",
                content="Artificial Intelligence (AI) is a branch of computer science that aims to create intelligent machines that work and react like humans. AI systems can perform tasks such as visual perception, speech recognition, decision-making, and language translation.",
                metadata={"source": "AI_basics.txt", "category": "technology"}
            ),
            Document(
                id="doc_2", 
                content="Machine Learning is a subset of AI that provides systems the ability to automatically learn and improve from experience without being explicitly programmed. It focuses on the development of computer programs that can access data and use it to learn for themselves.",
                metadata={"source": "ML_overview.txt", "category": "technology"}
            ),
            Document(
                id="doc_3",
                content="Climate change refers to long-term shifts in global temperatures and weather patterns. While climate variations are natural, scientific evidence shows that human activities have been the main driver of climate change since the 1800s.",
                metadata={"source": "climate_info.txt", "category": "environment"}
            ),
            Document(
                id="doc_4",
                content="Renewable energy comes from natural sources that are constantly replenished, such as sunlight, wind, rain, tides, waves, and geothermal heat. These energy sources are sustainable and help reduce greenhouse gas emissions.",
                metadata={"source": "renewable_energy.txt", "category": "environment"}
            ),
            Document(
                id="doc_5",
                content="Python is a high-level, interpreted programming language known for its simplicity and readability. It supports multiple programming paradigms and has a comprehensive standard library, making it popular for web development, data science, and automation.",
                metadata={"source": "python_guide.txt", "category": "programming"}
            )
        ]
        
        logger.info("Adding sample documents to RAG index")
        
        for doc in sample_docs:
            # Generate embedding
            embedding = self.encoder.encode([doc.content], normalize_embeddings=True)
            doc.embedding = embedding[0]
            
            # Add to index
            self.index.add(embedding)
            self.documents.append(doc)
        
        # Save the index
        self._save_index()
    
    def add_document(self, doc_id: str, content: str, metadata: Dict[str, Any] = None) -> bool:
        """Add a new document to the RAG index"""
        try:
            if metadata is None:
                metadata = {}
            
            doc = Document(
                id=doc_id,
                content=content,
                metadata=metadata
            )
            
            # Generate embedding
            embedding = self.encoder.encode([content], normalize_embeddings=True)
            doc.embedding = embedding[0]
            
            # Add to index
            self.index.add(embedding)
            self.documents.append(doc)
            
            # Save updated index
            self._save_index()
            
            logger.info(f"Added document {doc_id} to RAG index")
            return True
            
        except Exception as e:
            logger.error(f"Error adding document to RAG index: {str(e)}")
            return False
    
    def _save_index(self):
        """Save FAISS index and documents to disk"""
        try:
            os.makedirs(self.index_path, exist_ok=True)
            
            # Save FAISS index
            faiss.write_index(self.index, os.path.join(self.index_path, "faiss.index"))
            
            # Save documents
            with open(os.path.join(self.index_path, "documents.pkl"), 'wb') as f:
                pickle.dump(self.documents, f)
                
            logger.info(f"Saved RAG index to {self.index_path}")
            
        except Exception as e:
            logger.error(f"Error saving RAG index: {str(e)}")
    
    def _load_index(self):
        """Load FAISS index and documents from disk"""
        try:
            index_file = os.path.join(self.index_path, "faiss.index")
            docs_file = os.path.join(self.index_path, "documents.pkl")
            
            if os.path.exists(index_file) and os.path.exists(docs_file):
                # Load FAISS index
                self.index = faiss.read_index(index_file)
                
                # Load documents
                with open(docs_file, 'rb') as f:
                    self.documents = pickle.load(f)
                
                logger.info(f"Loaded RAG index from {self.index_path} with {len(self.documents)} documents")
            
        except Exception as e:
            logger.warning(f"Could not load existing RAG index: {str(e)}")
            # Reset to empty index
            self.index = faiss.IndexFlatIP(self.dimension)
            self.documents = []

# Tool instance for registration
rag_tool = RAGTool()