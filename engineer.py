"""
Engineer - Implements and tests proposed solutions
"""
import logging
import subprocess
import tempfile
import time
import os
from typing import Dict, Any, Optional
import re

logger = logging.getLogger("ASI-GO.Engineer")


def _is_prime(n: int) -> bool:
    if n < 2:
        return False
    if n in (2, 3):
        return True
    if n % 2 == 0 or n % 3 == 0:
        return False
    f = 5
    step = 2
    while f * f <= n:
        if n % f == 0:
            return False
        f += step
        step = 6 - step
    return True


def _first_n_primes(n: int):
    primes = []
    x = 2
    while len(primes) < n:
        if _is_prime(x):
            primes.append(x)
        x += 1
    return primes


class Engineer:
    """Tests and validates proposed solutions"""

    def __init__(self):
        self.test_results = []

    def extract_code(self, solution: str) -> Optional[str]:
        """Extract Python code from the solution text"""
        # Prefer fenced code blocks with language tag
        code_pattern = r"```python\n(.*?)```"
        matches = re.findall(code_pattern, solution, re.DOTALL)
        if matches:
            return max(matches, key=len)

        # Fallback: generic fenced blocks
        code_pattern2 = r"```\n(.*?)```"
        matches = re.findall(code_pattern2, solution, re.DOTALL)
        if matches:
            code = max(matches, key=len)
            if "def " in code or "import " in code or "print" in code:
                return code

        # Heuristic: collect lines that look like Python
        lines = solution.split("\n")
        code_lines = []
        in_code = False
        for line in lines:
            stripped = line.strip()
            if stripped.startswith(("import ", "from ", "def ", "class ")):
                in_code = True
            if in_code:
                # Stop if we clearly re-enter prose
                if stripped and not any(
                    stripped.startswith(x)
                    for x in [
                        "#",
                        "import",
                        "from",
                        "def",
                        "class",
                        "if",
                        "for",
                        "while",
                        "return",
                        "print",
                        "try",
                        "except",
                        "elif",
                        "else",
                    ]
                ):
                    if not stripped.endswith(":"):
                        break
                code_lines.append(line)
        if code_lines:
            return "\n".join(code_lines)
        return None

    def test_solution(self, proposal: Dict[str, Any]) -> Dict[str, Any]:
        """Run the proposed code in a sandboxed process with a timeout."""
        logger.info(f"Testing solution for: {proposal['goal']}")

        result: Dict[str, Any] = {
            "success": False,
            "output": None,
            "error": None,
            "issues": [],
            "execution_time": None,
        }

        code = self.extract_code(proposal["solution"])
        if not code:
            result["error"] = "No executable code found in solution"
            result["issues"].append("Solution must include Python code")
            return result

        # Add a main shim if missing
        has_main = "__main__" in code or "print(" in code
        selected_main_func = None

        if not has_main:
            goal_lower = proposal["goal"].lower()
            # find function candidates
            function_pattern = r"def\s+(\w+)\s*\([^)]*\):"
            functions = re.findall(function_pattern, code)
            if functions:
                for func in functions:
                    if any(k in func.lower() for k in ["main", "find", "get", "calculate", "solve"]):
                        selected_main_func = func
                        break
                if not selected_main_func:
                    selected_main_func = functions[-1]

            if selected_main_func:
                numbers = re.findall(r"\d+", goal_lower)
                if "prime" in goal_lower and numbers:
                    n = numbers[0]
                    code += (
                        f'\n\nif __name__ == "__main__":\n'
                        f"    result = {selected_main_func}({n})\n"
                        f"    print(result)\n"
                    )
                elif "prime" in goal_lower and "first" in goal_lower:
                    code += (
                        f'\n\nif __name__ == "__main__":\n'
                        f"    result = {selected_main_func}(40)\n"
                        f"    print(result)\n"
                    )
                else:
                    code += (
                        f'\n\nif __name__ == "__main__":\n'
                        f"    result = {selected_main_func}()\n"
                        f"    print(result)\n"
                    )

        # Execute
        temp_file = None
        try:
            with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
                f.write(code)
                temp_file = f.name

            logger.debug(f"Testing code:\n{code}")

            start = time.perf_counter()
            process = subprocess.run(
                ["python", temp_file],
                capture_output=True,
                text=True,
                timeout=int(os.getenv("ENGINEER_TIMEOUT", "30")),
            )
            elapsed = time.perf_counter() - start
            result["execution_time"] = elapsed

            if process.returncode == 0:
                result["success"] = True
                result["output"] = process.stdout
                logger.info(f"Solution executed successfully in {elapsed:.3f}s")
            else:
                result["error"] = process.stderr
                result["issues"].append("Code execution failed")
                logger.error(f"Execution error: {process.stderr}")

        except subprocess.TimeoutExpired:
            result["error"] = "Code execution timed out"
            result["issues"].append("TimeoutExpired")
        except Exception as e:
            result["error"] = str(e)
            result["issues"].append(f"Unexpected error: {type(e).__name__}")
            logger.error(f"Unexpected error while testing: {e}")
        finally:
            if temp_file and os.path.exists(temp_file):
                try:
                    os.unlink(temp_file)
                except Exception:
                    pass

        self.test_results.append(result)
        return result

    def validate_output(self, output: str, goal: str) -> Dict[str, Any]:
        """Semantic validation of output against the goal."""
        validation: Dict[str, Any] = {
            "meets_goal": False,
            "confidence": 0.0,
            "notes": [],
        }

        if not output or not output.strip():
            validation["notes"].append("No output produced")
            return validation

        goal_lower = goal.lower()

        if "prime" in goal_lower:
            # Pull all integers from the output (in order)
            numbers = [int(n) for n in re.findall(r"-?\d+", output)]
            if not numbers:
                validation["notes"].append("No numbers detected in output")
                return validation

            # Parse target N if present
            target_n = None
            nums_in_goal = re.findall(r"\d+", goal_lower)
            if nums_in_goal:
                try:
                    target_n = int(nums_in_goal[0])
                except Exception:
                    target_n = None

            # If user asked for "first N primes", require exact prefix match
            if "first" in goal_lower and target_n:
                expected = _first_n_primes(target_n)
                candidate = numbers[:target_n]
                if candidate == expected:
                    validation["meets_goal"] = True
                    validation["confidence"] = 0.98
                    validation["notes"].append(f"Output matches first {target_n} primes exactly")
                else:
                    validation["confidence"] = 0.2
                    validation["notes"].append(
                        f"First {target_n} numbers do not match expected prime sequence"
                    )
            else:
                # Heuristic: check presence of initial primes
                first_primes = [2, 3, 5, 7, 11, 13, 17, 19]
                if all(p in numbers[: max(10, len(numbers))] for p in first_primes[:5]):
                    validation["meets_goal"] = True
                    validation["confidence"] = 0.8
                    validation["notes"].append("Output contains several correct small primes")
                else:
                    validation["confidence"] = 0.3
                    validation["notes"].append("Numbers found but may not all be primes")

        elif "fibonacci" in goal_lower:
            numbers = [int(n) for n in re.findall(r"-?\d+", output)]
            if len(numbers) >= 5:
                fib5a = [0, 1, 1, 2, 3]
                fib5b = [1, 1, 2, 3, 5]
                if numbers[:5] in (fib5a, fib5b):
                    validation["meets_goal"] = True
                    validation["confidence"] = 0.9
                    validation["notes"].append("Output begins with a valid Fibonacci prefix")
                else:
                    validation["confidence"] = 0.4
                    validation["notes"].append("Numbers present but Fibonacci pattern unclear")
            else:
                validation["notes"].append("Too few numbers found for Fibonacci validation")
        else:
            # Generic fallback: any nontrivial output counts as partial success
            if len(output.strip()) > 10:
                validation["meets_goal"] = True
                validation["confidence"] = 0.5
                validation["notes"].append("Produced nontrivial output")

        return validation

    def generate_test_cases(self, goal: str) -> list:
        """Return suggested edge-case/scaled test ideas for the given goal."""
        tests = []
        gl = goal.lower()
        if "prime" in gl:
            tests = [
                {"input": 1, "expected": "[] or [2] depending on definition"},
                {"input": 10, "expected": "[2,3,5,7]"},
                {"input": 100, "expected": "ends with 541"},
            ]
        elif "fibonacci" in gl:
            tests = [
                {"input": 1, "expected": "[0] or [1]"},
                {"input": 5, "expected": "[0,1,1,2,3]"},
                {"input": 10, "expected": "ends with 34 or 55"},
            ]
        return tests
