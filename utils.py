"""
Utility functions for ASI-GO system
"""
import os
import json
import datetime
import logging
from typing import Dict, Any, List
from colorama import init, Fore, Style

# Initialize colorama for Windows
init(autoreset=True)

def setup_logging(log_level: str = "INFO") -> logging.Logger:
    """Setup logging configuration"""
    logging.basicConfig(
        level=getattr(logging, log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(f'asi_go_{datetime.datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger("ASI-GO")

def save_checkpoint(data: Dict[str, Any], checkpoint_name: str) -> None:
    """Save checkpoint data to JSON file"""
    checkpoint_dir = "checkpoints"
    os.makedirs(checkpoint_dir, exist_ok=True)
    
    filepath = os.path.join(checkpoint_dir, f"{checkpoint_name}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)
    
    print(f"{Fore.GREEN}✓ Checkpoint saved: {filepath}")

def load_latest_checkpoint(checkpoint_name: str) -> Dict[str, Any]:
    """Load the most recent checkpoint"""
    checkpoint_dir = "checkpoints"
    if not os.path.exists(checkpoint_dir):
        return {}
    
    files = [f for f in os.listdir(checkpoint_dir) if f.startswith(checkpoint_name)]
    if not files:
        return {}
    
    latest_file = sorted(files)[-1]
    filepath = os.path.join(checkpoint_dir, latest_file)
    
    with open(filepath, 'r') as f:
        return json.load(f)

def print_header(title: str) -> None:
    """Print a formatted header"""
    print(f"\n{Fore.CYAN}{'='*60}")
    print(f"{Fore.CYAN}{title.center(60)}")
    print(f"{Fore.CYAN}{'='*60}\n")

def print_step(step: str, description: str) -> None:
    """Print a formatted step"""
    print(f"{Fore.YELLOW}▶ {step}: {Fore.WHITE}{description}")

def validate_solution(solution: str, goal: str) -> Dict[str, Any]:
    """Basic validation of solution against goal"""
    validation_result = {
        "is_valid": False,
        "errors": [],
        "warnings": []
    }
    
    # Check if solution contains code
    if "```" in solution or "def " in solution or "import " in solution:
        validation_result["has_code"] = True
    else:
        validation_result["warnings"].append("No code blocks detected in solution")
    
    # Check if solution is not empty
    if len(solution.strip()) < 50:
        validation_result["errors"].append("Solution appears too short")
    else:
        validation_result["is_valid"] = True
    
    return validation_result