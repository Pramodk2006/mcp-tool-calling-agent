"""
Test configuration and fixtures for MCP Agent tests
"""
import pytest
import asyncio
from unittest.mock import Mock, patch
import tempfile
import os
from typing import Dict, Any

@pytest.fixture
def sample_query():
    """Sample query for testing"""
    return "Calculate 2 + 2"

@pytest.fixture
def sample_agent_response():
    """Sample agent response for testing"""
    return {
        "query": "Calculate 2 + 2",
        "final_answer": "The calculation result is 4.",
        "tools_used": ["calculator_tool"],
        "steps": [
            "Retrieved available tools",
            "Selected 1 tool(s): calculator_tool",
            "Executing calculator_tool with arguments: {'expression': '2 + 2'}",
            "✓ calculator_tool completed successfully",
            "✓ Query processing completed successfully"
        ],
        "raw_outputs": [
            {
                "success": True,
                "result": 4,
                "expression": "2 + 2",
                "formatted_result": "4",
                "tool_name": "calculator_tool",
                "timestamp": "2024-12-02T10:30:00Z"
            }
        ],
        "execution_time_seconds": 1.23,
        "success": True,
        "timestamp": "2024-12-02T10:30:00Z",
        "context": {}
    }

@pytest.fixture
def mock_openai_response():
    """Mock OpenAI API response"""
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].text = "The result is 4."
    mock_response.choices[0].message.content = "The result is 4."
    return mock_response

@pytest.fixture
def temp_upload_dir():
    """Temporary directory for file uploads"""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir

@pytest.fixture
def sample_pdf_path(temp_upload_dir):
    """Create a sample PDF file for testing"""
    # This would create a real PDF file for testing
    # For now, we'll just return a path
    pdf_path = os.path.join(temp_upload_dir, "sample.pdf")
    # In a real test, you'd create an actual PDF file here
    return pdf_path

@pytest.fixture
def mock_tool_manager():
    """Mock tool manager for testing"""
    mock_manager = Mock()
    mock_manager.get_available_tools.return_value = [
        {
            "name": "calculator_tool",
            "description": "Execute mathematical calculations",
            "input_schema": {"type": "object", "required": ["expression"]},
            "output_schema": {"type": "object"}
        }
    ]
    mock_manager.validate_tool_call.return_value = {"valid": True}
    mock_manager.execute_tool.return_value = {
        "success": True,
        "result": 4,
        "tool_name": "calculator_tool"
    }
    return mock_manager

@pytest.fixture
def mock_llm_interface():
    """Mock LLM interface for testing"""
    mock_llm = Mock()
    mock_llm.llm_available = False  # Test fallback behavior
    mock_llm.select_tools.return_value = [
        {
            "tool": "calculator_tool",
            "arguments": {"expression": "2 + 2"}
        }
    ]
    mock_llm.generate_final_answer.return_value = "The calculation result is 4."
    return mock_llm

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

# Helper functions for testing
def create_mock_tool_result(success: bool = True, tool_name: str = "test_tool", **kwargs) -> Dict[str, Any]:
    """Create a mock tool result for testing"""
    base_result = {
        "success": success,
        "tool_name": tool_name,
        "timestamp": "2024-12-02T10:30:00Z"
    }
    base_result.update(kwargs)
    
    if not success and "error" not in kwargs:
        base_result["error"] = "Mock error for testing"
    
    return base_result

def assert_valid_agent_response(response: Dict[str, Any]):
    """Assert that a response has valid agent response structure"""
    required_fields = [
        "query", "final_answer", "tools_used", "steps", 
        "raw_outputs", "execution_time_seconds", "success", "timestamp"
    ]
    
    for field in required_fields:
        assert field in response, f"Missing required field: {field}"
    
    assert isinstance(response["success"], bool)
    assert isinstance(response["tools_used"], list)
    assert isinstance(response["steps"], list)
    assert isinstance(response["raw_outputs"], list)
    assert isinstance(response["execution_time_seconds"], (int, float))
    assert response["execution_time_seconds"] >= 0