"""
Tool Manager for MCP Agent
Manages registration, discovery, and execution of all available tools
"""
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

# Import all available tools
from tools.search_tool import search_tool
from tools.calculator_tool import calculator_tool
from tools.pdf_summarizer import pdf_summarizer_tool
from tools.weather_tool import weather_tool
from tools.rag_tool import rag_tool
from tools.system_tool import system_tool

logger = logging.getLogger(__name__)

class ToolManager:
    """Manages all available tools for the MCP agent"""
    
    def __init__(self):
        self.tools = {}
        self._register_tools()
    
    def _register_tools(self):
        """Register all available tools"""
        available_tools = [
            search_tool,
            calculator_tool,
            pdf_summarizer_tool,
            weather_tool,
            rag_tool,
            system_tool
        ]
        
        for tool in available_tools:
            try:
                self.tools[tool.name] = tool
                logger.info(f"Registered tool: {tool.name}")
            except Exception as e:
                logger.error(f"Failed to register tool {tool.name}: {str(e)}")
    
    def get_available_tools(self) -> List[Dict[str, Any]]:
        """Get list of all available tools with their schemas"""
        tools_list = []
        
        for tool_name, tool in self.tools.items():
            try:
                schema = tool.get_schema()
                tools_list.append(schema)
            except Exception as e:
                logger.error(f"Error getting schema for tool {tool_name}: {str(e)}")
                # Add minimal info if schema fails
                tools_list.append({
                    "name": tool_name,
                    "description": getattr(tool, 'description', 'No description available'),
                    "error": f"Schema error: {str(e)}"
                })
        
        return tools_list
    
    def get_tool_by_name(self, tool_name: str) -> Optional[Any]:
        """Get a specific tool by name"""
        return self.tools.get(tool_name)
    
    def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a specific tool with given arguments"""
        try:
            tool = self.get_tool_by_name(tool_name)
            
            if not tool:
                return {
                    "success": False,
                    "error": f"Tool '{tool_name}' not found",
                    "available_tools": list(self.tools.keys()),
                    "timestamp": datetime.now().isoformat()
                }
            
            logger.info(f"Executing tool: {tool_name} with arguments: {arguments}")
            
            # Execute the tool
            result = tool.execute(arguments)
            
            # Add execution metadata
            result["tool_name"] = tool_name
            result["execution_timestamp"] = datetime.now().isoformat()
            
            logger.info(f"Tool {tool_name} execution completed successfully: {result.get('success', False)}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error executing tool {tool_name}: {str(e)}")
            return {
                "success": False,
                "error": f"Tool execution error: {str(e)}",
                "tool_name": tool_name,
                "timestamp": datetime.now().isoformat()
            }
    
    def validate_tool_call(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Validate a tool call before execution"""
        try:
            tool = self.get_tool_by_name(tool_name)
            
            if not tool:
                return {
                    "valid": False,
                    "error": f"Tool '{tool_name}' not found",
                    "available_tools": list(self.tools.keys())
                }
            
            # Get tool schema
            schema = tool.get_schema()
            input_schema = schema.get("input_schema", {})
            required_fields = input_schema.get("required", [])
            
            # Check required fields
            missing_fields = []
            for field in required_fields:
                if field not in arguments:
                    missing_fields.append(field)
            
            if missing_fields:
                return {
                    "valid": False,
                    "error": f"Missing required fields: {missing_fields}",
                    "required_fields": required_fields,
                    "provided_fields": list(arguments.keys())
                }
            
            # Basic type validation could be added here
            return {
                "valid": True,
                "tool_name": tool_name,
                "arguments": arguments
            }
            
        except Exception as e:
            logger.error(f"Error validating tool call: {str(e)}")
            return {
                "valid": False,
                "error": f"Validation error: {str(e)}"
            }
    
    def get_tool_suggestions(self, query: str) -> List[str]:
        """Suggest relevant tools based on query content"""
        query_lower = query.lower()
        suggestions = []
        
        # Simple keyword-based suggestions
        if any(word in query_lower for word in ['search', 'find', 'look up', 'google']):
            suggestions.append('search_tool')
        
        if any(word in query_lower for word in ['calculate', 'math', 'compute', '+', '-', '*', '/', 'equation']):
            suggestions.append('calculator_tool')
        
        if any(word in query_lower for word in ['pdf', 'document', 'summarize', 'summary', 'extract']):
            suggestions.append('pdf_summarizer_tool')
        
        if any(word in query_lower for word in ['weather', 'temperature', 'rain', 'forecast', 'climate']):
            suggestions.append('weather_tool')
        
        if any(word in query_lower for word in ['question', 'answer', 'knowledge', 'document search', 'rag']):
            suggestions.append('rag_tool')
        
        if any(word in query_lower for word in ['file', 'directory', 'system', 'disk', 'folder', 'list']):
            suggestions.append('system_tool')
        
        return suggestions
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about registered tools"""
        return {
            "total_tools": len(self.tools),
            "tool_names": list(self.tools.keys()),
            "timestamp": datetime.now().isoformat()
        }

# Global tool manager instance
tool_manager = ToolManager()