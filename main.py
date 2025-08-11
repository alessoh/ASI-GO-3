"""
ASI-GO: Autonomous System Intelligence - General Optimizer
Main orchestrator for the problem-solving system
"""
import os
import sys
import time
from typing import Optional
from colorama import init, Fore, Style
from dotenv import load_dotenv

# Import our modules
from llm_interface import LLMInterface
from cognition_base import CognitionBase
from researcher import Researcher
from engineer import Engineer
from analyst import Analyst
from utils import setup_logging, save_checkpoint, print_header, print_step

# Initialize colorama for Windows
init(autoreset=True)

class ASIGO:
    """Main orchestrator for the ASI-GO system"""
    
    def __init__(self):
        """Initialize all components"""
        print_header("ASI-GO System Initialization")
        
        # Setup logging
        log_level = os.getenv("LOG_LEVEL", "INFO")
        self.logger = setup_logging(log_level)
        self.logger.info("Starting ASI-GO system")
        
        # Initialize components
        try:
            print_step("1/5", "Initializing LLM Interface...")
            self.llm = LLMInterface()
            provider_info = self.llm.get_provider_info()
            print(f"   {Fore.GREEN}✓ Using {provider_info['provider']} - {provider_info['model']}")
            
            print_step("2/5", "Loading Cognition Base...")
            self.cognition_base = CognitionBase()
            print(f"   {Fore.GREEN}✓ Knowledge base loaded")
            
            print_step("3/5", "Initializing Researcher...")
            self.researcher = Researcher(self.llm, self.cognition_base)
            print(f"   {Fore.GREEN}✓ Researcher ready")
            
            print_step("4/5", "Initializing Engineer...")
            self.engineer = Engineer()
            print(f"   {Fore.GREEN}✓ Engineer ready")
            
            print_step("5/5", "Initializing Analyst...")
            self.analyst = Analyst(self.llm, self.cognition_base)
            print(f"   {Fore.GREEN}✓ Analyst ready")
            
            self.max_iterations = int(os.getenv("MAX_ITERATIONS", "5"))
            print(f"\n{Fore.GREEN}✓ System initialized successfully!")
            print(f"   Max iterations: {self.max_iterations}")
            
        except Exception as e:
            print(f"\n{Fore.RED}✗ Initialization failed: {e}")
            self.logger.error(f"Initialization failed: {e}")
            sys.exit(1)
    
    def warm_up_llm(self):
        """Warm up the LLM connection to prevent initial connection issues"""
        try:
            self.logger.info("Warming up LLM connection...")
            # Make a simple test query
            response = self.llm.query("Respond with 'ready'", max_tokens=10)
            self.logger.info("LLM warm-up successful")
            return True
        except Exception as e:
            self.logger.warning(f"LLM warm-up failed: {e}")
            return False
    
    def solve_problem(self, goal: str) -> bool:
        """Main problem-solving loop"""
        print_header(f"Solving: {goal}")
        self.logger.info(f"Starting to solve: {goal}")
        
        iteration = 0
        previous_attempt = None
        success = False
        
        while iteration < self.max_iterations and not success:
            iteration += 1
            print(f"\n{Fore.CYAN}{'='*60}")
            print(f"{Fore.CYAN}Iteration {iteration}/{self.max_iterations}")
            print(f"{Fore.CYAN}{'='*60}\n")
            
            try:
                # 1. Researcher proposes solution
                print_step("Research", "Generating solution proposal...")
                
                # Handle case where we need to generate a new proposal vs refine
                if iteration == 1:
                    proposal = self.researcher.propose_solution(goal)
                else:
                    # Check if we have a previous proposal to refine
                    if not self.researcher.proposal_history:
                        print(f"   {Fore.YELLOW}⚠ No previous proposal found, generating new one")
                        proposal = self.researcher.propose_solution(goal)
                    else:
                        proposal = self.researcher.refine_proposal(
                            self.researcher.proposal_history[-1], 
                            previous_attempt
                        )
                
                print(f"   {Fore.GREEN}✓ Proposal generated")
                
                # Save checkpoint
                save_checkpoint({
                    "iteration": iteration,
                    "goal": goal,
                    "proposal": proposal
                }, "proposal")
                
                # 2. Engineer tests solution
                print_step("Engineering", "Testing proposed solution...")
                test_result = self.engineer.test_solution(proposal)
                
                if test_result['success']:
                    print(f"   {Fore.GREEN}✓ Solution executed successfully")
                    if test_result['output']:
                        print(f"\n   Output preview:\n   {Fore.WHITE}{test_result['output'][:200]}...")
                else:
                    print(f"   {Fore.RED}✗ Execution failed: {test_result['error']}")
                
                # 3. Validate output
                validation = {}
                if test_result['success'] and test_result['output']:
                    validation = self.engineer.validate_output(test_result['output'], goal)
                    print(f"   Goal validation: {Fore.GREEN if validation['meets_goal'] else Fore.YELLOW}"
                          f"{'✓ Meets goal' if validation['meets_goal'] else '○ Partial success'}")
                
                # 4. Analyst analyzes results
                print_step("Analysis", "Analyzing results...")
                analysis = self.analyst.analyze_results(proposal, test_result, validation)
                print(f"   {Fore.GREEN}✓ Analysis complete")
                
                # Save checkpoint
                save_checkpoint({
                    "iteration": iteration,
                    "test_result": test_result,
                    "analysis": analysis
                }, "results")
                
                # Check for success
                if test_result['success'] and validation.get('meets_goal', False):
                    success = True
                    print(f"\n{Fore.GREEN}✓ Goal achieved successfully!")
                else:
                    previous_attempt = test_result
                    recommendation = self.analyst.recommend_next_action()
                    print(f"\n   {Fore.YELLOW}Recommendation: {recommendation}")
                
            except Exception as e:
                self.logger.error(f"Error in iteration {iteration}: {e}")
                print(f"\n{Fore.RED}✗ Error in iteration: {e}")
                
                # Set up for retry
                previous_attempt = {"error": str(e)}
                
                # For connection errors, wait before retrying
                if "Connection error" in str(e):
                    wait_time = min(5 * iteration, 30)  # Exponential backoff, max 30s
                    print(f"{Fore.YELLOW}⏳ Waiting {wait_time} seconds before retry...")
                    time.sleep(wait_time)
        
        # Generate final report
        print_header("Final Report")
        report = self.analyst.generate_summary_report()
        print(report)
        
        # Save final checkpoint
        save_checkpoint({
            "goal": goal,
            "success": success,
            "total_iterations": iteration,
            "final_report": report
        }, "final")
        
        return success
    
    def interactive_mode(self):
        """Run in interactive mode"""
        print_header("ASI-GO Interactive Mode")
        print("Enter your problem-solving goals. Type 'exit' to quit.\n")
        
        # Warm up the LLM connection
        print("Warming up LLM connection...")
        warm_up_success = self.warm_up_llm()
        if warm_up_success:
            print(f"{Fore.GREEN}✓ LLM connection ready\n")
        else:
            print(f"{Fore.YELLOW}⚠ LLM warm-up failed, but continuing...\n")
            # Add extra delay if warm-up failed
            time.sleep(2)
        
        while True:
            try:
                goal = input(f"{Fore.CYAN}Enter your goal: {Style.RESET_ALL}").strip()
                
                if goal.lower() in ['exit', 'quit', 'q']:
                    print(f"\n{Fore.YELLOW}Thank you for using ASI-GO!")
                    break
                
                if not goal:
                    print(f"{Fore.RED}Please enter a valid goal.")
                    continue
                
                # Add a small delay to ensure everything is ready
                time.sleep(0.5)
                
                # Solve the problem
                success = self.solve_problem(goal)
                
                # Ask if user wants to continue
                print(f"\n{Fore.CYAN}{'='*60}")
                continue_choice = input(f"{Fore.CYAN}Solve another problem? (y/n): {Style.RESET_ALL}")
                
                if continue_choice.lower() != 'y':
                    print(f"\n{Fore.YELLOW}Thank you for using ASI-GO!")
                    break
                    
            except KeyboardInterrupt:
                print(f"\n\n{Fore.YELLOW}Interrupted by user. Exiting...")
                break
            except Exception as e:
                print(f"\n{Fore.RED}Error: {e}")
                self.logger.error(f"Interactive mode error: {e}")
                
                # Ask if user wants to continue after error
                try:
                    retry_choice = input(f"\n{Fore.CYAN}Try again? (y/n): {Style.RESET_ALL}")
                    if retry_choice.lower() != 'y':
                        break
                except:
                    break

def main():
    """Main entry point"""
    # Load environment variables
    load_dotenv()
    
    # Print welcome message
    print(f"{Fore.CYAN}{'='*60}")
    print(f"{Fore.CYAN}{'ASI-GO: Autonomous System Intelligence'.center(60)}")
    print(f"{Fore.CYAN}{'General Optimizer v1.0'.center(60)}")
    print(f"{Fore.CYAN}{'='*60}\n")
    
    # Create ASI-GO instance
    asi_go = ASIGO()
    
    # Check if goal provided as command line argument
    if len(sys.argv) > 1:
        goal = ' '.join(sys.argv[1:])
        asi_go.solve_problem(goal)
    else:
        # Run in interactive mode
        asi_go.interactive_mode()

if __name__ == "__main__":
    main()