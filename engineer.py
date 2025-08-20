import logging
import traceback
import subprocess
import tempfile
import os
from typing import Dict, Any, Optional
import re

logger = logging.getLogger("ASI-GO.Engineer")

class Engineer:
    """Tests and validates proposed solutions"""
    
    def __init__(self):
        self.test_results = []
        
    def extract_code(self, solution: str) -> Optional[str]:
        """Extract Python code from the solution text"""
        # Look for code blocks
        code_pattern = r'```python\n(.*?)```'
        matches = re.findall(code_pattern, solution, re.DOTALL)
        
        if matches:
            # Return the longest code block (likely the complete solution)
            return max(matches, key=len)
        
        # Look for code block without python tag
        code_pattern2 = r'```\n(.*?)```'
        matches = re.findall(code_pattern2, solution, re.DOTALL)
        
        if matches:
            code = max(matches, key=len)
            # Check if it looks like Python code
            if 'def ' in code or 'import ' in code or 'print' in code:
                return code
        
        # Try to extract code by looking for function definitions
        lines = solution.split('\n')
        code_lines = []
        in_code = False
        
        for line in lines:
            # Start collecting when we see imports or function definitions
            if line.strip().startswith(('import ', 'from ', 'def ', 'class ')):
                in_code = True
            
            if in_code:
                # Stop if we hit natural language again
                if line.strip() and not any(line.strip().startswith(x) for x in 
                    ['#', 'import', 'from', 'def', 'class', 'if', 'for', 'while', 
                     'return', 'print', 'try', 'except', ' ', '\t']):
                    if not line.strip().endswith(':'):
                        break
                code_lines.append(line)
        
        if code_lines:
            return '\n'.join(code_lines)
        
        return None
    
    def test_solution(self, proposal: Dict[str, Any]) -> Dict[str, Any]:
        """Test the proposed solution"""
        logger.info(f"Testing solution for: {proposal['goal']}")
        
        result = {
            "success": False,
            "output": None,
            "error": None,
            "issues": [],
            "execution_time": None
        }
        
        # Extract code from solution
        code = self.extract_code(proposal['solution'])
        
        if not code:
            result["error"] = "No executable code found in solution"
            result["issues"].append("Solution must include Python code")
            return result
        
        # Check if code already has a main execution block
        has_main = "__main__" in code or "print(" in code
        
        if not has_main:
            # Try to identify the main function based on the goal
            goal_lower = proposal['goal'].lower()
            
            # Look for functions that might be the main entry point
            function_pattern = r'def\s+(\w+)\s*\([^)]*\):'
            functions = re.findall(function_pattern, code)
            
            main_func = None
            if functions:
                # Priority: look for functions with relevant names
                for func in functions:
                    if any(keyword in func.lower() for keyword in ['main', 'find', 'get', 'calculate', 'solve']):
                        main_func = func
                        break
                
                # If no relevant function found, use the last defined function
                if not main_func and functions:
                    main_func = functions[-1]
            
            # Add appropriate main block based on the goal
            if main_func:
                if "prime" in goal_lower and "40" in goal_lower:
                    code += f"\n\nif __name__ == '__main__':\n    result = {main_func}(40)\n    print(result)"
                elif "prime" in goal_lower and any(str(i) in goal_lower for i in range(1, 100)):
                    # Extract number from goal (use module-level `re`)
                    numbers = re.findall(r'\d+', goal_lower)
                    if numbers:
                        n = numbers[0]
                        code += f"\n\nif __name__ == '__main__':\n    result = {main_func}({n})\n    print(result)"
                else:
                    # Generic execution
                    code += f"\n\nif __name__ == '__main__':\n    result = {main_func}()\n    print(result)"
        
        # Test the code in a temporary file
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(code)
                temp_file = f.name
            
            logger.debug(f"Testing code:\n{code}")
            
            # Run the code with a timeout
            process = subprocess.run(
                ['python', temp_file],
                capture_output=True,
                text=True,
                timeout=30  # 30 second timeout
            )
            
            if process.returncode == 0:
                result["success"] = True
                result["output"] = process.stdout
                logger.info("Solution executed successfully")
            else:
                result["error"] = process.stderr
                result["issues"].append("Code execution failed")
                logger.error(f"Execution error: {process.stderr}")
                
        except subprocess.TimeoutExpired:
            result["error"] = "Code execution timed out (30 seconds)"
            result["issues"].append("Solution may have infinite loop or be too slow")
            
        except Exception as e:
            result["error"] = str(e)
            result["issues"].append(f"Unexpected error: {type(e).__name__}")
            logger.error(f"Unexpected error: {e}")
            
        finally:
            # Clean up temp file
            if 'temp_file' in locals() and os.path.exists(temp_file):
                os.unlink(temp_file)
        
        self.test_results.append(result)
        return result
    
    def validate_output(self, output: str, goal: str) -> Dict[str, Any]:
        """Validate if the output meets the goal requirements"""
        validation = {
            "meets_goal": False,
            "confidence": 0.0,
            "notes": []
        }
        
        if not output:
            validation["notes"].append("No output produced")
            return validation
        
        # Basic validation based on goal keywords
        goal_lower = goal.lower()
        
        if "prime" in goal_lower and ("first" in goal_lower or "40" in goal_lower):
            # Check if output contains numbers
            numbers = re.findall(r'\d+', output)
            if numbers:
                validation["notes"].append(f"Found {len(numbers)} numbers in output")
                
                # Check if we have around 40 numbers
                if 35 <= len(numbers) <= 45:
                    # Basic prime check for first few
                    first_primes = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29]
                    output_numbers = [int(n) for n in numbers[:10]]
                    
                    if all(p in output_numbers for p in first_primes[:5]):
                        validation["meets_goal"] = True
                        validation["confidence"] = 0.9
                        validation["notes"].append("Output contains correct prime numbers")
                    else:
                        validation["confidence"] = 0.3
                        validation["notes"].append("Numbers found but may not all be primes")
                        
        elif "fibonacci" in goal_lower:
            numbers = re.findall(r'\d+', output)
            if len(numbers) >= 5:
                # Check if it follows Fibonacci pattern
                validation["notes"].append(f"Found {len(numbers)} numbers")
                try:
                    nums = [int(n) for n in numbers[:10]]
                    # Check first few Fibonacci numbers
                    if nums[:5] == [0, 1, 1, 2, 3] or nums[:5] == [1, 1, 2, 3, 5]:
                        validation["meets_goal"] = True
                        validation["confidence"] = 0.9
                except:
                    pass
                    
        else:
            # Generic validation - check if there's meaningful output
            if len(output.strip()) > 10:
                validation["meets_goal"] = True
                validation["confidence"] = 0.5
                validation["notes"].append("Output generated")
        
        return validation
    
    def generate_test_cases(self, goal: str) -> list:
        """Generate test cases based on the goal"""
        test_cases = []
        
        if "prime" in goal.lower():
            test_cases = [
                {"input": 10, "expected": "contains 2, 3, 5, 7"},
                {"input": 1, "expected": "handles edge case"},
            ]
        elif "fibonacci" in goal.lower():
            test_cases = [
                {"input": 5, "expected": "0, 1, 1, 2, 3"},
                {"input": 1, "expected": "0 or [0]"},
            ]
            
        return test_cases