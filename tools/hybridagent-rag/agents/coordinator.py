"""
Coordinator Agent: Orchestrates the entire resolution workflow
"""

import time
from typing import Dict, List, Any, Optional
from .base_agent import BaseAgent
from .analyzer import AnalyzerAgent
from .resolver import ResolverAgent
from .validator import ValidatorAgent
from .learner import LearnerAgent


class CoordinatorAgent(BaseAgent):
    """
    Coordinates all agents to resolve Python dependency conflicts
    """
    
    def __init__(
        self,
        analyzer: AnalyzerAgent,
        resolver: ResolverAgent,
        validator: ValidatorAgent,
        learner: LearnerAgent,
        max_iterations: int = 5,
        **kwargs
    ):
        super().__init__(name="Coordinator", **kwargs)
        
        self.analyzer = analyzer
        self.resolver = resolver
        self.validator = validator
        self.learner = learner
        self.max_iterations = max_iterations
        
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Coordinate the full resolution workflow
        
        Args:
            input_data: {
                'snippet_path': str - Path to Python snippet
                'code': str - Python code to resolve
                'quick_mode': bool - Use quick validation (default: True)
            }
            
        Returns:
            {
                'success': bool - Whether resolution succeeded
                'solution': Dict - Final solution (if successful)
                'analysis': Dict - Code analysis results
                'attempts': List[Dict] - All attempts made
                'execution_time': float - Total time taken
                'error_logs': List[str] - Error messages (if failed)
            }
        """
        snippet_path = input_data.get('snippet_path', 'unknown')
        code = input_data.get('code', '')
        quick_mode = input_data.get('quick_mode', True)
        
        self.log(f"Starting resolution for: {snippet_path}")
        start_time = time.time()
        
        # Initialize context
        context = {
            'snippet_path': snippet_path,
            'code': code,
            'attempts': [],
            'error_logs': [],
            'iteration': 0
        }
        
        try:
            # Step 1: Analyze code
            self.log("Step 1: Analyzing code...")
            analysis = self.analyzer.process({
                'code': code,
                'snippet_path': snippet_path
            })
            context['analysis'] = analysis
            
            # Step 2: Iterative resolution with feedback
            solution = None
            for iteration in range(self.max_iterations):
                context['iteration'] = iteration + 1
                self.log(f"Step 2: Resolution attempt {iteration + 1}/{self.max_iterations}")
                
                # Generate candidate solutions
                resolver_input = {
                    'analysis': analysis,
                    'code': code,
                    'context': context
                }
                resolution = self.resolver.process(resolver_input)
                
                # Validate candidates
                self.log("Step 3: Validating candidates...")
                validator_input = {
                    'candidates': resolution.get('candidates', []),
                    'code': code,
                    'quick_mode': quick_mode
                }
                validation = self.validator.process(validator_input)
                
                # Get best candidate
                best_candidate = validation.get('best_candidate')
                
                if best_candidate:
                    final_score = best_candidate.get('final_score', 0)
                    self.log(f"Best candidate score: {final_score:.3f}")
                    
                    # Check if solution is good enough
                    if final_score >= 0.7:  # Threshold for acceptance
                        solution = best_candidate
                        self.log("✅ Solution found!")
                        break
                    else:
                        # Record attempt and continue
                        context['attempts'].append({
                            'iteration': iteration + 1,
                            'candidate': best_candidate,
                            'score': final_score
                        })
                        
                        # Update context with feedback
                        validation_issues = best_candidate.get('validation', {}).get('issues', [])
                        context['error_logs'].extend(validation_issues)
                        
                        self.log(f"Score too low ({final_score:.3f}), trying again...")
                else:
                    self.log("No valid candidates generated", "WARNING")
                    break
            
            # Determine success
            success = solution is not None and solution.get('final_score', 0) >= 0.7
            
            # Step 4: Learn from result
            self.log("Step 4: Learning from result...")
            learner_input = {
                'snippet_path': snippet_path,
                'code': code,
                'analysis': analysis,
                'solution': solution,
                'success': success,
                'error_logs': context['error_logs'],
                'attempted_solutions': context['attempts']
            }
            learning_result = self.learner.process(learner_input)
            
            execution_time = time.time() - start_time
            
            # Prepare final result
            result = {
                'success': success,
                'solution': solution,
                'analysis': analysis,
                'attempts': context['attempts'],
                'execution_time': execution_time,
                'error_logs': context['error_logs'],
                'learning': learning_result,
                'iterations_used': context['iteration']
            }
            
            if success:
                self.log(f"✅ SUCCESS in {execution_time:.2f}s ({context['iteration']} iterations)")
            else:
                self.log(f"❌ FAILED after {execution_time:.2f}s ({context['iteration']} iterations)")
            
            return result
            
        except Exception as e:
            self.log(f"Critical error: {e}", "ERROR")
            execution_time = time.time() - start_time
            
            return {
                'success': False,
                'solution': None,
                'analysis': context.get('analysis'),
                'attempts': context.get('attempts', []),
                'execution_time': execution_time,
                'error_logs': context.get('error_logs', []) + [str(e)],
                'iterations_used': context.get('iteration', 0)
            }
    
    def batch_process(
        self,
        snippets: List[Dict[str, str]],
        quick_mode: bool = True,
        verbose: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Process multiple snippets in batch
        
        Args:
            snippets: List of {'path': str, 'code': str}
            quick_mode: Use quick validation
            verbose: Print detailed progress
            
        Returns:
            List of resolution results
        """
        results = []
        total = len(snippets)
        
        self.log(f"Starting batch processing of {total} snippets")
        batch_start = time.time()
        
        for i, snippet in enumerate(snippets, 1):
            if verbose:
                print(f"\n{'='*80}")
                print(f"Processing {i}/{total}: {snippet.get('path', 'unknown')}")
                print(f"{'='*80}")
            
            result = self.process({
                'snippet_path': snippet.get('path', f'snippet_{i}'),
                'code': snippet.get('code', ''),
                'quick_mode': quick_mode
            })
            
            results.append(result)
            
            # Progress update
            if verbose or i % 10 == 0:
                successes = sum(1 for r in results if r.get('success', False))
                success_rate = successes / len(results) * 100
                avg_time = sum(r.get('execution_time', 0) for r in results) / len(results)
                
                self.log(f"Progress: {i}/{total} | Success rate: {success_rate:.1f}% | Avg time: {avg_time:.2f}s")
        
        batch_time = time.time() - batch_start
        
        # Final statistics
        successes = sum(1 for r in results if r.get('success', False))
        success_rate = successes / total * 100
        avg_time = sum(r.get('execution_time', 0) for r in results) / total
        
        self.log(f"\n{'='*80}")
        self.log(f"Batch processing complete!")
        self.log(f"Total: {total} snippets")
        self.log(f"Successes: {successes} ({success_rate:.1f}%)")
        self.log(f"Failures: {total - successes}")
        self.log(f"Avg time per snippet: {avg_time:.2f}s")
        self.log(f"Total time: {batch_time:.2f}s")
        self.log(f"{'='*80}\n")
        
        return results
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get overall statistics from all agents
        """
        return {
            'learner_stats': self.learner.get_statistics(),
            'max_iterations': self.max_iterations
        }
