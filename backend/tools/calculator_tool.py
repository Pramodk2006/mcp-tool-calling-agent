"""
Calculator Tool for MCP Agent
Executes safe mathematical expressions and returns results
"""
import json
import logging
import ast
import operator
from typing import Dict, Any, Union
from dataclasses import dataclass
from datetime import datetime
import re
import math

logger = logging.getLogger(__name__)

class CalculatorTool:
    """Safe calculator tool for mathematical expressions"""
    
    # Supported operations
    _operators = {
        ast.Add: operator.add,
        ast.Sub: operator.sub, 
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.Pow: operator.pow,
        ast.BitXor: operator.xor,
        ast.USub: operator.neg,
    }
    
    # Supported functions
    _functions = {
        'abs': abs,
        'round': round,
        'max': max,
        'min': min,
        'sum': sum,
        'sqrt': math.sqrt,
        'sin': math.sin,
        'cos': math.cos,
        'tan': math.tan,
        'log': math.log,
        'log10': math.log10,
        'exp': math.exp,
        'ceil': math.ceil,
        'floor': math.floor,
        'pi': math.pi,
        'e': math.e,
    }
    
    def __init__(self):
        self.name = "calculator_tool"
        self.description = "Execute safe mathematical calculations and return results"
        
    def get_schema(self) -> Dict[str, Any]:
        """Return the JSON schema for this tool"""
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": {
                "type": "object", 
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "Mathematical expression to evaluate (e.g., '2 + 2', 'sqrt(16)', '10 * (5 + 3)')"
                    },
                    "precision": {
                        "type": "integer",
                        "description": "Number of decimal places to round result to (default: None)",
                        "minimum": 0,
                        "maximum": 10
                    }
                },
                "required": ["expression"]
            },
            "output_schema": {
                "type": "object",
                "properties": {
                    "success": {"type": "boolean"},
                    "result": {"type": ["number", "null"]},
                    "expression": {"type": "string"},
                    "formatted_result": {"type": "string"},
                    "timestamp": {"type": "string"},
                    "error": {"type": "string"}
                }
            }
        }
    
    def execute(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the calculator tool"""
        try:
            expression = arguments.get("expression", "").strip()
            precision = arguments.get("precision")
            
            if not expression:
                return {
                    "success": False,
                    "error": "Expression parameter is required",
                    "timestamp": datetime.now().isoformat()
                }
            
            logger.info(f"Calculating expression: {expression}")
            
            # Clean and validate expression
            cleaned_expr = self._clean_expression(expression)
            
            if not self._is_safe_expression(cleaned_expr):
                return {
                    "success": False,
                    "error": "Expression contains unsafe operations or characters",
                    "expression": expression,
                    "timestamp": datetime.now().isoformat()
                }
            
            # Parse and evaluate
            result = self._evaluate_expression(cleaned_expr)
            
            # Format result
            formatted_result = str(result)
            if precision is not None and isinstance(result, float):
                result = round(result, precision)
                formatted_result = f"{result:.{precision}f}"
            
            return {
                "success": True,
                "result": result,
                "expression": expression,
                "formatted_result": formatted_result,
                "timestamp": datetime.now().isoformat()
            }
            
        except ZeroDivisionError:
            return {
                "success": False,
                "error": "Division by zero",
                "expression": arguments.get("expression", ""),
                "timestamp": datetime.now().isoformat()
            }
        except ValueError as e:
            return {
                "success": False, 
                "error": f"Invalid value: {str(e)}",
                "expression": arguments.get("expression", ""),
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error calculating expression: {str(e)}")
            return {
                "success": False,
                "error": f"Calculation error: {str(e)}",
                "expression": arguments.get("expression", ""),
                "timestamp": datetime.now().isoformat()
            }
    
    def _clean_expression(self, expression: str) -> str:
        """Clean and normalize the mathematical expression"""
        # Remove extra spaces
        expression = re.sub(r'\s+', ' ', expression.strip())
        
        # Replace common function names
        replacements = {
            'π': 'pi',
            'e': 'e',
        }
        
        for old, new in replacements.items():
            expression = expression.replace(old, new)
        
        return expression
    
    def _is_safe_expression(self, expression: str) -> bool:
        """Check if expression is safe to evaluate"""
        # Disallow dangerous patterns
        dangerous_patterns = [
            '__', 'import', 'exec', 'eval', 'open', 'file', 'input', 'raw_input',
            'compile', 'globals', 'locals', 'vars', 'dir', 'delattr', 'getattr',
            'setattr', 'hasattr', 'callable', 'isinstance', 'issubclass', 'iter',
            'next', 'range', 'xrange', 'type', 'super', 'property', 'staticmethod',
            'classmethod'
        ]
        
        expression_lower = expression.lower()
        for pattern in dangerous_patterns:
            if pattern in expression_lower:
                return False
        
        # Only allow alphanumeric, operators, parentheses, and dots
        allowed_chars = set('0123456789+-*/()^. abcdefghijklmnopqrstuvwxyz_')
        if not all(c.lower() in allowed_chars for c in expression):
            return False
        
        return True
    
    def _evaluate_expression(self, expression: str) -> Union[int, float]:
        """Safely evaluate mathematical expression using AST"""
        try:
            # Parse the expression into an AST
            node = ast.parse(expression, mode='eval')
            return self._eval_node(node.body)
        except Exception as e:
            raise ValueError(f"Invalid expression: {str(e)}")
    
    def _eval_node(self, node) -> Union[int, float]:
        """Recursively evaluate AST nodes"""
        if isinstance(node, ast.Constant):  # Python 3.8+
            return node.value
        elif isinstance(node, ast.Num):  # Python < 3.8
            return node.n
        elif isinstance(node, ast.BinOp):
            left = self._eval_node(node.left)
            right = self._eval_node(node.right) 
            op = self._operators.get(type(node.op))
            if op is None:
                raise ValueError(f"Unsupported operation: {type(node.op).__name__}")
            return op(left, right)
        elif isinstance(node, ast.UnaryOp):
            operand = self._eval_node(node.operand)
            op = self._operators.get(type(node.op))
            if op is None:
                raise ValueError(f"Unsupported unary operation: {type(node.op).__name__}")
            return op(operand)
        elif isinstance(node, ast.Call):
            func_name = node.func.id
            if func_name not in self._functions:
                raise ValueError(f"Unsupported function: {func_name}")
            
            args = [self._eval_node(arg) for arg in node.args]
            func = self._functions[func_name]
            
            # Handle special cases
            if func_name in ['pi', 'e']:
                return func
            
            return func(*args)
        elif isinstance(node, ast.Name):
            # Handle constants like pi, e
            if node.id in self._functions:
                return self._functions[node.id]
            else:
                raise ValueError(f"Unknown variable: {node.id}")
        else:
            raise ValueError(f"Unsupported node type: {type(node).__name__}")

# Tool instance for registration
calculator_tool = CalculatorTool()