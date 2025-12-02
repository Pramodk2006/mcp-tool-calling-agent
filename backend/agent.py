"""
Main Agent Logic for MCP Tool-Calling Agent
Orchestrates tool selection, execution, and answer generation
"""
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import asyncio
import time

from tool_manager import tool_manager
from llm import llm_interface

logger = logging.getLogger(__name__)

class MCPAgent:
    """Main MCP (Model Context Protocol) Agent for tool-calling operations"""
    
    def __init__(self):
        self.tool_manager = tool_manager
        self.llm = llm_interface
        self.max_retries = 3
        self.retry_delay = 1.0  # seconds
        
    async def process_query(self, query: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Process a user query and return structured response"""
        start_time = time.time()
        
        try:
            logger.info(f"Processing query: {query}")
            
            # Initialize response structure
            response = {
                "query": query,
                "final_answer": "",
                "tools_used": [],
                "steps": [],
                "raw_outputs": [],
                "execution_time_seconds": 0,
                "success": True,
                "timestamp": datetime.now().isoformat(),
                "context": context or {}
            }
            
            # Step 1: Get available tools
            available_tools = self.tool_manager.get_available_tools()
            response["steps"].append("Retrieved available tools")
            
            if not available_tools:
                response["success"] = False
                response["final_answer"] = "No tools are available to process your request."
                response["execution_time_seconds"] = time.time() - start_time
                return response
            
            # Step 2: Select appropriate tools using LLM
            response["steps"].append("Analyzing query to select appropriate tools")
            selected_tools = self.llm.select_tools(query, available_tools)
            
            if not selected_tools:
                response["success"] = False
                response["final_answer"] = "I couldn't determine which tools to use for your query. Please try rephrasing your request."
                response["execution_time_seconds"] = time.time() - start_time
                return response
            
            response["steps"].append(f"Selected {len(selected_tools)} tool(s): {[tool['tool'] for tool in selected_tools]}")
            
            # Step 3: Execute tools
            tool_results = []
            for i, tool_call in enumerate(selected_tools):
                tool_name = tool_call.get("tool", "")
                arguments = tool_call.get("arguments", {})
                
                response["steps"].append(f"Executing {tool_name} with arguments: {arguments}")
                
                # Execute tool with retry logic
                result = await self._execute_tool_with_retry(tool_name, arguments)
                tool_results.append(result)
                response["raw_outputs"].append(result)
                response["tools_used"].append(tool_name)
                
                # Log result
                if result.get("success", False):
                    response["steps"].append(f"✓ {tool_name} completed successfully")
                else:
                    error = result.get("error", "Unknown error")
                    response["steps"].append(f"✗ {tool_name} failed: {error}")
            
            # Step 4: Check if we have any successful results
            successful_results = [r for r in tool_results if r.get("success", False)]
            
            if not successful_results:
                response["success"] = False
                response["final_answer"] = "All tool executions failed. Please check your request and try again."
                response["execution_time_seconds"] = time.time() - start_time
                return response
            
            # Step 5: Generate final answer
            response["steps"].append("Generating final answer based on tool results")
            final_answer = self.llm.generate_final_answer(query, tool_results, response["steps"])
            response["final_answer"] = final_answer
            
            response["steps"].append("✓ Query processing completed successfully")
            response["execution_time_seconds"] = time.time() - start_time
            
            logger.info(f"Query processed successfully in {response['execution_time_seconds']:.2f}s")
            return response
            
        except Exception as e:
            logger.error(f"Error processing query: {str(e)}")
            response["success"] = False
            response["final_answer"] = f"An error occurred while processing your query: {str(e)}"
            response["execution_time_seconds"] = time.time() - start_time
            return response
    
    async def _execute_tool_with_retry(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool with retry logic"""
        last_error = None
        
        for attempt in range(self.max_retries):
            try:
                # Validate tool call first
                validation = self.tool_manager.validate_tool_call(tool_name, arguments)
                
                if not validation.get("valid", False):
                    return {
                        "success": False,
                        "error": f"Tool validation failed: {validation.get('error', 'Unknown validation error')}",
                        "tool_name": tool_name,
                        "attempt": attempt + 1,
                        "timestamp": datetime.now().isoformat()
                    }
                
                # Execute tool
                result = self.tool_manager.execute_tool(tool_name, arguments)
                
                # If successful, return result
                if result.get("success", False):
                    result["attempt"] = attempt + 1
                    return result
                
                # If failed, prepare for retry
                last_error = result.get("error", "Unknown error")
                logger.warning(f"Tool {tool_name} failed on attempt {attempt + 1}: {last_error}")
                
                # Wait before retry (except on last attempt)
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay)
                
            except Exception as e:
                last_error = str(e)
                logger.error(f"Exception executing tool {tool_name} on attempt {attempt + 1}: {str(e)}")
                
                # Wait before retry (except on last attempt)
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay)
        
        # All retries failed
        return {
            "success": False,
            "error": f"Tool execution failed after {self.max_retries} attempts. Last error: {last_error}",
            "tool_name": tool_name,
            "attempts": self.max_retries,
            "timestamp": datetime.now().isoformat()
        }
    
    def process_multi_step_query(self, query: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Handle complex multi-step queries (synchronous version)"""
        return asyncio.run(self.process_query(query, context))
    
    def get_tool_suggestions(self, query: str) -> List[str]:
        """Get suggested tools for a query"""
        return self.tool_manager.get_tool_suggestions(query)
    
    def get_available_tools(self) -> List[Dict[str, Any]]:
        """Get list of available tools"""
        return self.tool_manager.get_available_tools()
    
    def health_check(self) -> Dict[str, Any]:
        """Perform health check on the agent and its components"""
        try:
            health_status = {
                "agent_status": "healthy",
                "llm_available": self.llm.llm_available,
                "tools_available": len(self.tool_manager.tools),
                "tool_list": list(self.tool_manager.tools.keys()),
                "timestamp": datetime.now().isoformat()
            }
            
            # Test tool manager
            try:
                tools = self.tool_manager.get_available_tools()
                health_status["tool_manager_status"] = "healthy"
                health_status["tools_count"] = len(tools)
            except Exception as e:
                health_status["tool_manager_status"] = f"error: {str(e)}"
            
            # Test LLM interface
            if self.llm.llm_available:
                health_status["llm_status"] = "available"
            else:
                health_status["llm_status"] = "unavailable (using fallback mode)"
            
            return health_status
            
        except Exception as e:
            return {
                "agent_status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def get_agent_info(self) -> Dict[str, Any]:
        """Get information about the agent"""
        return {
            "name": "MCP Tool-Calling Agent",
            "version": "1.0.0",
            "description": "AI Agent with tool calling capabilities using Model Context Protocol style",
            "capabilities": [
                "Web search",
                "Mathematical calculations", 
                "PDF summarization",
                "Weather information",
                "Document Q&A (RAG)",
                "System information"
            ],
            "max_retries": self.max_retries,
            "retry_delay_seconds": self.retry_delay,
            "llm_available": self.llm.llm_available,
            "total_tools": len(self.tool_manager.tools),
            "timestamp": datetime.now().isoformat()
        }

# Global agent instance
mcp_agent = MCPAgent()