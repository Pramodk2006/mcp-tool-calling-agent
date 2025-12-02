"""
LLM Interface for MCP Agent
Handles communication with Language Models for tool selection and answer generation
"""
import json
import logging
import os
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
import openai
import re

logger = logging.getLogger(__name__)

class LLMInterface:
    """Interface for Language Model operations"""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-3.5-turbo"):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model
        
        if self.api_key:
            openai.api_key = self.api_key
            self.llm_available = True
        else:
            self.llm_available = False
            logger.warning("No OpenAI API key provided. Using fallback logic for tool selection.")
    
    def select_tools(self, query: str, available_tools: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Select appropriate tools for a given query"""
        if self.llm_available:
            return self._llm_tool_selection(query, available_tools)
        else:
            return self._fallback_tool_selection(query, available_tools)
    
    def generate_final_answer(self, query: str, tool_results: List[Dict[str, Any]], steps: List[str]) -> str:
        """Generate final answer based on query and tool results"""
        if self.llm_available:
            return self._llm_generate_answer(query, tool_results, steps)
        else:
            return self._fallback_generate_answer(query, tool_results, steps)
    
    def _llm_tool_selection(self, query: str, available_tools: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Use LLM to select appropriate tools"""
        try:
            # Create tool descriptions for the prompt
            tool_descriptions = []
            for tool in available_tools:
                desc = f"- {tool['name']}: {tool['description']}"
                if 'input_schema' in tool:
                    required_fields = tool['input_schema'].get('required', [])
                    if required_fields:
                        desc += f" (requires: {', '.join(required_fields)})"
                tool_descriptions.append(desc)
            
            tools_text = "\n".join(tool_descriptions)
            
            prompt = f"""You are an AI agent that selects appropriate tools to answer user queries.

Available tools:
{tools_text}

User query: "{query}"

Based on the query, select the most appropriate tools and provide the arguments for each tool.
You can select multiple tools if the query requires multiple steps.

Respond with a JSON array of tool calls in this exact format:
[
    {{
        "tool": "tool_name",
        "arguments": {{
            "arg1": "value1",
            "arg2": "value2"
        }}
    }}
]

If the query asks for multiple things (like "search for AI news and tell me the weather"), include multiple tool calls.
Make sure to extract specific parameters from the query (like location for weather, search terms, etc.).

Tool calls:"""

            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful AI assistant that selects appropriate tools based on user queries."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=1000
            )
            
            response_text = response.choices[0].message.content.strip()
            
            # Parse JSON response
            try:
                # Extract JSON from response (handle cases where there's extra text)
                json_match = re.search(r'\[.*\]', response_text, re.DOTALL)
                if json_match:
                    json_text = json_match.group(0)
                else:
                    json_text = response_text
                
                tool_calls = json.loads(json_text)
                
                # Validate tool calls
                validated_calls = []
                for call in tool_calls:
                    if isinstance(call, dict) and 'tool' in call and 'arguments' in call:
                        validated_calls.append(call)
                
                logger.info(f"LLM selected {len(validated_calls)} tools: {[call['tool'] for call in validated_calls]}")
                return validated_calls
                
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse LLM tool selection response: {str(e)}")
                logger.error(f"Response was: {response_text}")
                return self._fallback_tool_selection(query, available_tools)
                
        except Exception as e:
            logger.error(f"Error in LLM tool selection: {str(e)}")
            return self._fallback_tool_selection(query, available_tools)
    
    def _fallback_tool_selection(self, query: str, available_tools: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Fallback tool selection using simple keyword matching"""
        query_lower = query.lower()
        selected_tools = []
        
        # Create a map of tool names to tool info
        tool_map = {tool['name']: tool for tool in available_tools}
        
        # Simple keyword-based selection
        if any(word in query_lower for word in ['search', 'find', 'look up', 'google', 'web']):
            if 'search_tool' in tool_map:
                # Extract search query
                search_query = query
                # Remove common prefixes
                for prefix in ['search for', 'find', 'look up', 'google']:
                    if query_lower.startswith(prefix):
                        search_query = query[len(prefix):].strip()
                        break
                
                selected_tools.append({
                    "tool": "search_tool",
                    "arguments": {"query": search_query}
                })
        
        if any(word in query_lower for word in ['calculate', 'math', 'compute', '+', '-', '*', '/', 'equation', 'solve']):
            if 'calculator_tool' in tool_map:
                # Try to extract mathematical expression
                # Look for mathematical patterns
                math_pattern = r'[\d+\-*/().\s]+'
                matches = re.findall(math_pattern, query)
                expression = query
                
                # If we found a clear mathematical expression, use it
                if matches:
                    # Take the longest match
                    expression = max(matches, key=len).strip()
                
                selected_tools.append({
                    "tool": "calculator_tool", 
                    "arguments": {"expression": expression}
                })
        
        if any(word in query_lower for word in ['weather', 'temperature', 'rain', 'forecast', 'climate']):
            if 'weather_tool' in tool_map:
                # Extract location
                location = "New York"  # Default location
                
                # Simple location extraction
                location_indicators = ['in', 'at', 'for', 'weather in', 'weather for']
                for indicator in location_indicators:
                    if indicator in query_lower:
                        parts = query_lower.split(indicator)
                        if len(parts) > 1:
                            location = parts[1].split()[0:3]  # Take up to 3 words
                            location = ' '.join(location).strip()
                            break
                
                selected_tools.append({
                    "tool": "weather_tool",
                    "arguments": {"location": location}
                })
        
        if any(word in query_lower for word in ['summarize', 'summary', 'pdf']):
            if 'pdf_summarizer_tool' in tool_map:
                # This would need a file path - use a default or ask for upload
                selected_tools.append({
                    "tool": "pdf_summarizer_tool",
                    "arguments": {"file_path": "/path/to/document.pdf"}  # Placeholder
                })
        
        if any(word in query_lower for word in ['files', 'directory', 'system', 'disk', 'folder', 'list files']):
            if 'system_tool' in tool_map:
                operation = "list_directory"
                if 'system info' in query_lower:
                    operation = "system_info"
                elif 'disk usage' in query_lower or 'disk space' in query_lower:
                    operation = "disk_usage"
                
                selected_tools.append({
                    "tool": "system_tool",
                    "arguments": {"operation": operation}
                })
        
        if any(word in query_lower for word in ['question', 'answer', 'knowledge', 'document search']) or '?' in query:
            if 'rag_tool' in tool_map:
                selected_tools.append({
                    "tool": "rag_tool",
                    "arguments": {"question": query}
                })
        
        # If no tools were selected, default to search
        if not selected_tools and 'search_tool' in tool_map:
            selected_tools.append({
                "tool": "search_tool", 
                "arguments": {"query": query}
            })
        
        logger.info(f"Fallback selected {len(selected_tools)} tools: {[call['tool'] for call in selected_tools]}")
        return selected_tools
    
    def _llm_generate_answer(self, query: str, tool_results: List[Dict[str, Any]], steps: List[str]) -> str:
        """Use LLM to generate final answer"""
        try:
            # Prepare context from tool results
            context_parts = []
            for i, result in enumerate(tool_results):
                tool_name = result.get('tool_name', f'Tool {i+1}')
                success = result.get('success', False)
                
                if success:
                    # Extract key information from result
                    result_summary = self._summarize_tool_result(result)
                    context_parts.append(f"{tool_name}: {result_summary}")
                else:
                    error = result.get('error', 'Unknown error')
                    context_parts.append(f"{tool_name}: Failed - {error}")
            
            context = "\n".join(context_parts)
            steps_text = "\n".join([f"{i+1}. {step}" for i, step in enumerate(steps)])
            
            prompt = f"""You are a helpful AI assistant. Based on the tool execution results below, provide a comprehensive and natural answer to the user's question.

User Question: {query}

Execution Steps:
{steps_text}

Tool Results:
{context}

Please provide a natural, conversational response that directly answers the user's question using the information from the tool results. If any tools failed, mention it briefly but focus on the successful results.

Answer:"""

            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful AI assistant that provides clear, concise answers based on tool execution results."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1000
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"Error generating LLM answer: {str(e)}")
            return self._fallback_generate_answer(query, tool_results, steps)
    
    def _fallback_generate_answer(self, query: str, tool_results: List[Dict[str, Any]], steps: List[str]) -> str:
        """Fallback answer generation without LLM"""
        if not tool_results:
            return "I wasn't able to execute any tools to answer your question. Please try rephrasing your query."
        
        successful_results = [r for r in tool_results if r.get('success', False)]
        
        if not successful_results:
            errors = [r.get('error', 'Unknown error') for r in tool_results]
            return f"I encountered errors while processing your request: {'; '.join(errors)}"
        
        # Generate simple answer based on results
        answer_parts = []
        
        for result in successful_results:
            tool_name = result.get('tool_name', 'Unknown tool')
            summary = self._summarize_tool_result(result)
            answer_parts.append(f"From {tool_name}: {summary}")
        
        return "Here's what I found:\n\n" + "\n\n".join(answer_parts)
    
    def _summarize_tool_result(self, result: Dict[str, Any]) -> str:
        """Summarize a tool result for answer generation"""
        tool_name = result.get('tool_name', '')
        
        if tool_name == 'search_tool':
            results = result.get('results', [])
            if results:
                return f"Found {len(results)} search results. Top result: {results[0].get('title', '')} - {results[0].get('snippet', '')[:100]}..."
            return "No search results found."
        
        elif tool_name == 'calculator_tool':
            formatted_result = result.get('formatted_result', '')
            expression = result.get('expression', '')
            return f"Calculation result for '{expression}': {formatted_result}"
        
        elif tool_name == 'weather_tool':
            current = result.get('current_weather', {})
            location = result.get('location', 'Unknown location')
            temp = current.get('temperature', 'N/A')
            desc = current.get('description', 'N/A')
            return f"Weather in {location}: {temp}°, {desc}"
        
        elif tool_name == 'pdf_summarizer_tool':
            summary = result.get('summary', '')
            return f"PDF summary: {summary[:200]}..." if len(summary) > 200 else f"PDF summary: {summary}"
        
        elif tool_name == 'rag_tool':
            answer = result.get('answer', '')
            return answer[:200] + "..." if len(answer) > 200 else answer
        
        elif tool_name == 'system_tool':
            operation = result.get('operation', '')
            if operation == 'system_info':
                return "Retrieved system information"
            elif operation == 'list_directory':
                result_data = result.get('result', {})
                total = result_data.get('total_entries', 0)
                return f"Listed directory contents: {total} items found"
            return f"Completed {operation} operation"
        
        else:
            # Generic summary
            if 'error' in result:
                return f"Error: {result['error']}"
            return "Operation completed successfully"

# Global LLM interface instance
llm_interface = LLMInterface()