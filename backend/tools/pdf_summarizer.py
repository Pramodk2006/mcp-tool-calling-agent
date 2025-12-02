"""
PDF Summarizer Tool for MCP Agent
Extracts text from PDF files and summarizes using LLM
"""
import json
import logging
import os
from typing import Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import PyPDF2
from io import BytesIO
import openai

logger = logging.getLogger(__name__)

class PDFSummarizerTool:
    """PDF text extraction and summarization tool"""
    
    def __init__(self, openai_api_key: Optional[str] = None):
        self.name = "pdf_summarizer_tool"
        self.description = "Extract text from PDF files and generate summaries"
        self.openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        
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
                    "file_path": {
                        "type": "string",
                        "description": "Path to the PDF file to summarize"
                    },
                    "summary_length": {
                        "type": "string",
                        "enum": ["short", "medium", "long"],
                        "description": "Desired length of summary (default: medium)",
                        "default": "medium"
                    },
                    "focus_area": {
                        "type": "string", 
                        "description": "Optional focus area for summary (e.g., 'key findings', 'methodology', 'conclusions')"
                    }
                },
                "required": ["file_path"]
            },
            "output_schema": {
                "type": "object",
                "properties": {
                    "success": {"type": "boolean"},
                    "summary": {"type": "string"},
                    "key_points": {
                        "type": "array", 
                        "items": {"type": "string"}
                    },
                    "word_count": {"type": "integer"},
                    "page_count": {"type": "integer"},
                    "file_path": {"type": "string"},
                    "timestamp": {"type": "string"},
                    "error": {"type": "string"}
                }
            }
        }
    
    def execute(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the PDF summarizer tool"""
        try:
            file_path = arguments.get("file_path", "").strip()
            summary_length = arguments.get("summary_length", "medium")
            focus_area = arguments.get("focus_area", "")
            
            if not file_path:
                return {
                    "success": False,
                    "error": "file_path parameter is required",
                    "timestamp": datetime.now().isoformat()
                }
            
            if not os.path.exists(file_path):
                return {
                    "success": False,
                    "error": f"File not found: {file_path}",
                    "file_path": file_path,
                    "timestamp": datetime.now().isoformat()
                }
            
            if not file_path.lower().endswith('.pdf'):
                return {
                    "success": False,
                    "error": "File must be a PDF",
                    "file_path": file_path,
                    "timestamp": datetime.now().isoformat()
                }
            
            logger.info(f"Processing PDF file: {file_path}")
            
            # Extract text from PDF
            extracted_text, page_count = self._extract_pdf_text(file_path)
            
            if not extracted_text.strip():
                return {
                    "success": False,
                    "error": "Could not extract text from PDF or PDF is empty",
                    "file_path": file_path,
                    "page_count": page_count,
                    "timestamp": datetime.now().isoformat()
                }
            
            word_count = len(extracted_text.split())
            
            # Generate summary
            if self.openai_api_key:
                summary, key_points = self._generate_llm_summary(
                    extracted_text, summary_length, focus_area
                )
            else:
                summary, key_points = self._generate_simple_summary(
                    extracted_text, summary_length
                )
            
            return {
                "success": True,
                "summary": summary,
                "key_points": key_points,
                "word_count": word_count,
                "page_count": page_count,
                "file_path": file_path,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error processing PDF: {str(e)}")
            return {
                "success": False,
                "error": f"PDF processing error: {str(e)}",
                "file_path": arguments.get("file_path", ""),
                "timestamp": datetime.now().isoformat()
            }
    
    def _extract_pdf_text(self, file_path: str) -> tuple[str, int]:
        """Extract text from PDF file"""
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                page_count = len(pdf_reader.pages)
                
                text_parts = []
                for page_num, page in enumerate(pdf_reader.pages):
                    try:
                        page_text = page.extract_text()
                        if page_text:
                            text_parts.append(f"[Page {page_num + 1}]\n{page_text}\n")
                    except Exception as e:
                        logger.warning(f"Error extracting text from page {page_num + 1}: {str(e)}")
                        continue
                
                return "\n".join(text_parts), page_count
                
        except Exception as e:
            logger.error(f"Error reading PDF file: {str(e)}")
            raise
    
    def _generate_llm_summary(self, text: str, length: str, focus_area: str) -> tuple[str, list[str]]:
        """Generate summary using OpenAI API"""
        try:
            # Determine summary parameters based on length
            length_params = {
                "short": {"max_tokens": 150, "sentences": "2-3"},
                "medium": {"max_tokens": 300, "sentences": "4-6"}, 
                "long": {"max_tokens": 500, "sentences": "7-10"}
            }
            
            params = length_params.get(length, length_params["medium"])
            
            # Build prompt
            focus_instruction = f" Focus specifically on: {focus_area}." if focus_area else ""
            
            summary_prompt = f"""Please provide a {length} summary of the following text in {params['sentences']} sentences.{focus_instruction}

Text to summarize:
{text[:4000]}  # Limit text length for API

Summary:"""

            # Generate summary
            response = openai.Completion.create(
                engine="text-davinci-003",
                prompt=summary_prompt,
                max_tokens=params["max_tokens"],
                temperature=0.7,
                stop=None
            )
            
            summary = response.choices[0].text.strip()
            
            # Generate key points
            key_points_prompt = f"""Extract 3-5 key points from the following text as bullet points:

{text[:4000]}

Key Points:
-"""
            
            key_points_response = openai.Completion.create(
                engine="text-davinci-003", 
                prompt=key_points_prompt,
                max_tokens=200,
                temperature=0.5,
                stop=None
            )
            
            key_points_text = key_points_response.choices[0].text.strip()
            key_points = [point.strip("- ").strip() for point in key_points_text.split("\n") if point.strip()]
            
            return summary, key_points[:5]  # Limit to 5 key points
            
        except Exception as e:
            logger.warning(f"Error generating LLM summary: {str(e)}")
            # Fallback to simple summary
            return self._generate_simple_summary(text, length)
    
    def _generate_simple_summary(self, text: str, length: str) -> tuple[str, list[str]]:
        """Generate simple extractive summary when LLM is not available"""
        sentences = text.replace('\n', ' ').split('. ')
        sentences = [s.strip() + '.' for s in sentences if len(s.strip()) > 20]
        
        # Determine number of sentences based on length
        num_sentences = {
            "short": min(3, len(sentences)),
            "medium": min(5, len(sentences)),
            "long": min(8, len(sentences))
        }.get(length, min(5, len(sentences)))
        
        # Simple extractive summary - take sentences from beginning, middle, end
        if len(sentences) <= num_sentences:
            summary_sentences = sentences
        else:
            # Take some from beginning, some from middle, some from end
            begin_count = num_sentences // 3
            middle_count = num_sentences // 3
            end_count = num_sentences - begin_count - middle_count
            
            begin_sentences = sentences[:begin_count]
            middle_start = len(sentences) // 2 - middle_count // 2
            middle_sentences = sentences[middle_start:middle_start + middle_count]
            end_sentences = sentences[-end_count:] if end_count > 0 else []
            
            summary_sentences = begin_sentences + middle_sentences + end_sentences
        
        summary = ' '.join(summary_sentences)
        
        # Generate simple key points
        key_points = []
        words = text.split()
        
        # Simple keyword extraction (this is very basic)
        important_phrases = []
        for i in range(0, len(words) - 2):
            phrase = ' '.join(words[i:i+3])
            if any(keyword in phrase.lower() for keyword in ['important', 'key', 'significant', 'main', 'primary', 'conclusion', 'result', 'finding']):
                important_phrases.append(phrase)
        
        # Take up to 5 phrases as key points
        key_points = important_phrases[:5]
        
        # If no key phrases found, extract first sentences of paragraphs
        if not key_points:
            paragraphs = text.split('\n\n')
            for para in paragraphs[:5]:
                first_sentence = para.split('.')[0].strip()
                if len(first_sentence) > 10:
                    key_points.append(first_sentence + '.')
        
        return summary, key_points

# Tool instance for registration
pdf_summarizer_tool = PDFSummarizerTool()