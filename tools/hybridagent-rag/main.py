"""
HybridAgent-RAG: Main Entry Point
Hierarchical Multi-Agent System for Python Dependency Resolution
"""

import argparse
import glob
import json
import time
from pathlib import Path

# Import agents
from agents.analyzer import AnalyzerAgent
from agents.resolver import ResolverAgent
from agents.validator import ValidatorAgent
from agents.learner import LearnerAgent
from agents.coordinator import CoordinatorAgent

# Import RAG and Graph systems
from rag.adaptive_rag import AdaptiveRAG
from graph.conflict_detector import ConflictDetector


def initialize_system(model="gemma2", base_url="http://localhost:11434"):
    """
    Initialize the HybridAgent-RAG system
    """
    print("🚀 Initializing HybridAgent-RAG System...")
    
    # Initialize RAG system
    rag_system = AdaptiveRAG()
    print("✅ RAG system initialized")
    
    # Initialize Graph conflict detector
    graph_detector = ConflictDetector()
    print("✅ Graph conflict detector initialized")
    
    # Initialize agents
    analyzer = AnalyzerAgent(model=model, base_url=base_url)
    resolver = ResolverAgent(
        model=model,
        base_url=base_url,
        rag_system=rag_system,
        graph_detector=graph_detector
    )
    validator = ValidatorAgent(model=model, base_url=base_url)
    learner = LearnerAgent(model=model, base_url=base_url, rag_system=rag_system)
    
    print("✅ All agents initialized")
    
    # Initialize coordinator
    coordinator = CoordinatorAgent(
        analyzer=analyzer,
        resolver=resolver,
        validator=validator,
        learner=learner,
        model=model,
        base_url=base_url,
        max_iterations=5
    )
    
    print("✅ Coordinator initialized")
    print(f"🎯 Using model: {model}")
    print(f"🌐 Ollama URL: {base_url}\n")
    
    return coordinator, rag_system


def process_single_snippet(coordinator, snippet_path, quick_mode=True):
    """
    Process a single Python snippet
    """
    print(f"\n{'='*80}")
    print(f"Processing: {snippet_path}")
    print(f"{'='*80}\n")
    
    # Read snippet
    try:
        with open(snippet_path, 'r', encoding='utf-8') as f:
            code = f.read()
    except Exception as e:
        print(f"❌ Error reading file: {e}")
        return None
    
    # Process
    result = coordinator.process({
        'snippet_path': snippet_path,
        'code': code,
        'quick_mode': quick_mode
    })
    
    # Display result
    print(f"\n{'='*80}")
    if result['success']:
        print("✅ RESOLUTION SUCCESSFUL!")
        solution = result['solution']
        print(f"\nPython Version: {solution.get('python_version')}")
        print(f"Packages:")
        for pkg, ver in solution.get('packages', {}).items():
            print(f"  - {pkg}=={ver}")
        print(f"\nConfidence Score: {solution.get('final_score', 0):.3f}")
    else:
        print("❌ RESOLUTION FAILED")
        if result.get('error_logs'):
            print("\nErrors:")
            for error in result['error_logs'][:3]:  # Show first 3 errors
                print(f"  - {error}")
    
    print(f"\nExecution Time: {result['execution_time']:.2f}s")
    print(f"Iterations Used: {result['iterations_used']}")
    print(f"{'='*80}\n")
    
    return result


def process_batch(coordinator, snippets_dir, output_file, quick_mode=True, max_snippets=None):
    """
    Process multiple snippets in batch
    """
    # Find all snippet files
    snippet_files = glob.glob(f"{snippets_dir}/**/snippet.py", recursive=True)
    
    if max_snippets:
        snippet_files = snippet_files[:max_snippets]
    
    print(f"\n{'='*80}")
    print(f"Batch Processing: {len(snippet_files)} snippets")
    print(f"{'='*80}\n")
    
    # Prepare snippets
    snippets = []
    for path in snippet_files:
        try:
            with open(path, 'r', encoding='utf-8') as f:
                code = f.read()
            snippets.append({'path': path, 'code': code})
        except Exception as e:
            print(f"⚠️ Skipping {path}: {e}")
    
    # Process batch
    results = coordinator.batch_process(
        snippets=snippets,
        quick_mode=quick_mode,
        verbose=True
    )
    
    # Save results
    output_data = {
        'timestamp': time.time(),
        'total_snippets': len(results),
        'successful': sum(1 for r in results if r['success']),
        'failed': sum(1 for r in results if not r['success']),
        'results': results
    }
    
    with open(output_file, 'w') as f:
        json.dump(output_data, f, indent=2)
    
    print(f"\n✅ Results saved to: {output_file}")
    
    return results


def main():
    parser = argparse.ArgumentParser(
        description="HybridAgent-RAG: Python Dependency Resolution System"
    )
    
    parser.add_argument(
        '-f', '--file',
        type=str,
        help='Path to single Python snippet file'
    )
    
    parser.add_argument(
        '-d', '--directory',
        type=str,
        help='Directory containing multiple snippets'
    )
    
    parser.add_argument(
        '-o', '--output',
        type=str,
        default='results.json',
        help='Output file for batch results (default: results.json)'
    )
    
    parser.add_argument(
        '-m', '--model',
        type=str,
        default='gemma2',
        help='LLM model to use (default: gemma2)'
    )
    
    parser.add_argument(
        '-b', '--base-url',
        type=str,
        default='http://localhost:11434',
        help='Ollama base URL (default: http://localhost:11434)'
    )
    
    parser.add_argument(
        '--full-validation',
        action='store_true',
        help='Use full validation (slower but more accurate)'
    )
    
    parser.add_argument(
        '--max-snippets',
        type=int,
        help='Maximum number of snippets to process in batch mode'
    )
    
    args = parser.parse_args()
    
    # Initialize system
    coordinator, rag_system = initialize_system(
        model=args.model,
        base_url=args.base_url
    )
    
    quick_mode = not args.full_validation
    
    # Process
    if args.file:
        # Single file mode
        result = process_single_snippet(coordinator, args.file, quick_mode)
        
    elif args.directory:
        # Batch mode
        results = process_batch(
            coordinator,
            args.directory,
            args.output,
            quick_mode,
            args.max_snippets
        )
        
    else:
        print("❌ Error: Please specify either --file or --directory")
        parser.print_help()
        return 1
    
    # Print final statistics
    stats = coordinator.get_statistics()
    print(f"\n{'='*80}")
    print("📊 System Statistics:")
    print(f"{'='*80}")
    learner_stats = stats['learner_stats']
    print(f"Total Attempts: {learner_stats['total_attempts']}")
    print(f"Successes: {learner_stats['successes']}")
    print(f"Failures: {learner_stats['failures']}")
    print(f"Success Rate: {learner_stats['success_rate']*100:.1f}%")
    print(f"{'='*80}\n")
    
    return 0


if __name__ == "__main__":
    exit(main())
