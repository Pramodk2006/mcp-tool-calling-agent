"""
Tests for the Calculator Tool
"""
import pytest
from tools.calculator_tool import calculator_tool

class TestCalculatorTool:
    """Test cases for calculator tool"""
    
    def test_simple_addition(self):
        """Test simple addition"""
        result = calculator_tool.execute({"expression": "2 + 2"})
        
        assert result["success"] is True
        assert result["result"] == 4
        assert "2 + 2" in result["expression"]
    
    def test_complex_expression(self):
        """Test complex mathematical expression"""
        result = calculator_tool.execute({"expression": "sqrt(16) + 2 * 3"})
        
        assert result["success"] is True
        assert result["result"] == 10  # 4 + 6
    
    def test_precision_formatting(self):
        """Test precision formatting"""
        result = calculator_tool.execute({
            "expression": "10 / 3", 
            "precision": 2
        })
        
        assert result["success"] is True
        assert result["formatted_result"] == "3.33"
    
    def test_division_by_zero(self):
        """Test division by zero error handling"""
        result = calculator_tool.execute({"expression": "5 / 0"})
        
        assert result["success"] is False
        assert "Division by zero" in result["error"]
    
    def test_invalid_expression(self):
        """Test invalid mathematical expression"""
        result = calculator_tool.execute({"expression": "invalid_expression"})
        
        assert result["success"] is False
        assert "error" in result
    
    def test_empty_expression(self):
        """Test empty expression"""
        result = calculator_tool.execute({"expression": ""})
        
        assert result["success"] is False
        assert "required" in result["error"].lower()
    
    def test_schema_structure(self):
        """Test tool schema structure"""
        schema = calculator_tool.get_schema()
        
        assert schema["name"] == "calculator_tool"
        assert "input_schema" in schema
        assert "output_schema" in schema
        assert "expression" in schema["input_schema"]["properties"]
        assert "expression" in schema["input_schema"]["required"]

if __name__ == "__main__":
    pytest.main([__file__])