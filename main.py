"""
Main execution script for Local SOP Identifier
"""

import argparse
import json
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from src.local_sop_identifier import LocalSOPIdentifier


def main():
    """
    Main execution flow:
    1. Initialize the local SOP identifier
    2. Build or load the index
    3. Process sample incident
    4. Display results
    """
    
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description='Local SOP Identifier - Lightweight Offline Solution')
    parser.add_argument('--build-index-only', action='store_true',
                        help='Build the search index and exit (useful for Docker builds)')
    parser.add_argument('--query', type=str,
                        help='Run a single query and exit (non-interactive mode)')
    parser.add_argument('--no-examples', action='store_true',
                        help='Skip example queries and go directly to interactive mode')
    parser.add_argument('--model-name', type=str, default='all-MiniLM-L6-v2',
                        help='Sentence transformer model name')
    parser.add_argument('--cache-dir', type=str, default='./models',
                        help='Directory to cache the model')
    parser.add_argument('--index-path', type=str, default='./data/sop_index.pkl',
                        help='Path to the index file')
    parser.add_argument('--sop-file', type=str, default='./data/structured_sops.txt',
                        help='Path to the SOP file')
    
    args = parser.parse_args()
    
    print("=" * 80)
    print("Local SOP Identifier - Lightweight Offline Solution")
    print("=" * 80)
    print()
    
    # Initialize identifier
    identifier = LocalSOPIdentifier(
        model_name=args.model_name,
        cache_dir=args.cache_dir
    )
    
    # Check if index exists
    index_path = args.index_path
    sop_file_path = args.sop_file
    
    if not os.path.exists(sop_file_path):
        print(f"ERROR: SOP file not found at {sop_file_path}")
        print("Please ensure structured_sops.txt is in the data directory")
        return 1
    
    if os.path.exists(index_path):
        print("Loading existing index...")
        identifier.load_index(index_path)
    else:
        print("Building new index...")
        identifier.build_index(sop_file_path, index_path)
    
    # If build-index-only mode, exit now
    if args.build_index_only:
        print()
        print("=" * 80)
        print("Index built successfully. Exiting.")
        print("=" * 80)
        return 0
    
    # If single query mode, process and exit
    if args.query:
        print()
        print("=" * 80)
        print(f"Processing Query: {args.query}")
        print("=" * 80)
        
        incident = {
            'incident_details': {
                'description': args.query
            }
        }
        
        result = identifier.process_incident(incident)
        print()
        print_result(result, show_alternatives=True)
        return 0
    
    print()
    print("=" * 80)
    print("Index ready. You can now query for SOPs.")
    print("=" * 80)
    print()
    
    # Run example queries unless --no-examples flag is set
    if not args.no_examples:
        run_example_queries(identifier)
    
    # Interactive mode
    run_interactive_mode(identifier)
    
    return 0


def run_example_queries(identifier):
    """Run the predefined example queries"""
    # Example 1: Database outage
    print("\n" + "=" * 80)
    print("EXAMPLE 1: Database Service Outage")
    print("=" * 80)
    
    incident_1 = {
        'incident_details': {
            'short_description': 'Production database is completely unavailable',
            'description': 'All database connections are timing out. Applications showing 503 errors. Monitoring shows 0% database availability.'
        },
        'log_insights': {
            'full_analysis': 'Connection refused errors on port 5432. Database process appears stopped.'
        }
    }
    
    result_1 = identifier.process_incident(incident_1)
    print_result(result_1)
    
    # Example 2: API Performance issue
    print("\n" + "=" * 80)
    print("EXAMPLE 2: API Performance Degradation")
    print("=" * 80)
    
    incident_2 = {
        'incident_details': {
            'short_description': 'API response times extremely slow',
            'description': 'Users reporting very slow API responses. Response times increased from 200ms to 5000ms. No errors, just slow.'
        },
        'log_insights': {
            'full_analysis': 'High CPU usage on API servers. Thread pool exhaustion detected.'
        }
    }
    
    result_2 = identifier.process_incident(incident_2)
    print_result(result_2)
    
    # Example 3: Authentication failure
    print("\n" + "=" * 80)
    print("EXAMPLE 3: Authentication Service Failure")
    print("=" * 80)
    
    incident_3 = {
        'incident_details': {
            'short_description': 'Users cannot log in to the application',
            'description': 'Multiple users reporting authentication failures. Login page returns 401 errors.'
        },
        'log_insights': {
            'full_analysis': 'OAuth service returning invalid token errors. Token validation failing.'
        }
    }
    
    result_3 = identifier.process_incident(incident_3)
    print_result(result_3)


def run_interactive_mode(identifier):
    """Run the interactive CLI mode"""
    print("\n" + "=" * 80)
    print("INTERACTIVE MODE")
    print("=" * 80)
    print("Enter incident descriptions to find matching SOPs (or 'quit' to exit)")
    print()
    
    while True:
        try:
            query = input("\nIncident description: ").strip()
            
            if query.lower() in ['quit', 'exit', 'q']:
                print("Exiting...")
                break
            
            if not query:
                continue
            
            # Process as simple query
            incident = {
                'incident_details': {
                    'description': query
                }
            }
            
            result = identifier.process_incident(incident)
            print()
            print_result(result, show_alternatives=True)
            
        except KeyboardInterrupt:
            print("\n\nExiting...")
            break
        except Exception as e:
            print(f"Error: {e}")


def print_result(result: dict, show_alternatives: bool = False):
    """
    Pretty print the SOP selection result
    
    Args:
        result: Result dictionary from select_best_sop
        show_alternatives: Whether to show alternative SOPs
    """
    print()
    print("SELECTED SOP:")
    print("-" * 80)
    
    if result['selected_sop_id']:
        print(f"  ID:          {result['selected_sop_id']}")
        print(f"  Number:      SOP-{result['selected_sop_number']:03d}")
        print(f"  Title:       {result['selected_sop_title']}")
        print(f"  Confidence:  {result['confidence_score']:.4f} ({result['confidence_level']})")
        print(f"  Semantic:    {result['semantic_score']:.4f}")
        print(f"  BM25:        {result['bm25_score']:.4f}")
        print()
        print(f"  Recommendation: {result['recommendation']}")
        print(f"  Reason: {result['reason']}")
    else:
        print(f"  No SOP found")
        print(f"  Reason: {result['reason']}")
    
    if show_alternatives and result.get('alternative_sops'):
        print()
        print("ALTERNATIVE SOPs:")
        print("-" * 80)
        for i, sop in enumerate(result['alternative_sops'], 1):
            print(f"  {i}. {sop['title']}")
            print(f"     Confidence: {sop['confidence_score']:.4f} ({sop['confidence_level']})")
    
    print()


if __name__ == '__main__':
    sys.exit(main())
