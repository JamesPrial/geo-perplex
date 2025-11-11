"""
Analysis and comparison script for search results
Query and compare Perplexity search results across models and time
"""
import sys
import os
import argparse
from datetime import datetime
from typing import Dict, List
from src.utils.storage import (
    get_results_by_query,
    get_results_by_model,
    compare_models_for_query,
    get_recent_results,
    get_unique_queries,
    get_unique_models
)
from src.utils.json_export import export_database_to_json


def format_timestamp(timestamp_str: str) -> str:
    """Format timestamp for display"""
    if timestamp_str is None:
        return "N/A"
    try:
        dt = datetime.fromisoformat(timestamp_str)
        return dt.strftime('%Y-%m-%d %H:%M:%S')
    except:
        return str(timestamp_str) if timestamp_str else "N/A"


def print_result(result: Dict, show_full_answer: bool = False) -> None:
    """Print a single result in formatted way"""
    print(f"\n{'='*80}")
    print(f"ID: {result.get('id', 'N/A')}")
    print(f"Query: {result.get('query', 'N/A')}")
    print(f"Model: {result.get('model') or 'default'}")
    print(f"Timestamp: {format_timestamp(result.get('timestamp'))}")
    exec_time = result.get('execution_time_seconds') or 0
    print(f"Execution Time: {exec_time:.2f}s")
    print(f"Success: {'✓' if result.get('success', True) else '✗'}")

    if not result.get('success', True) and result.get('error_message'):
        print(f"Error: {result['error_message']}")

    if result.get('screenshot_path'):
        print(f"Screenshot: {result['screenshot_path']}")

    answer_text = result.get('answer_text') or ''
    print(f"\nAnswer ({len(answer_text)} chars):")
    print("-" * 80)
    if show_full_answer:
        print(answer_text)
    else:
        # Show first 500 chars
        answer_preview = answer_text[:500]
        if len(answer_text) > 500:
            answer_preview += '...'
        print(answer_preview)

    sources = result.get('sources', [])
    if sources and isinstance(sources, list):
        print(f"\nSources ({len(sources)}):")
        print("-" * 80)
        for i, source in enumerate(sources[:5], 1):
            if isinstance(source, dict):
                print(f"{i}. {source.get('text', 'N/A')}")
                print(f"   {source.get('url', 'N/A')}")


def list_queries(args) -> None:
    """List all unique queries in database"""
    queries = get_unique_queries()
    print(f"\n📋 Found {len(queries)} unique queries:\n")
    for i, query in enumerate(queries, 1):
        print(f"{i}. {query}")


def list_models(args) -> None:
    """List all unique models in database"""
    models = get_unique_models()
    print(f"\n🤖 Found {len(models)} unique models:\n")
    for i, model in enumerate(models, 1):
        print(f"{i}. {model}")


def show_recent(args) -> None:
    """Show recent search results"""
    limit = args.limit or 10
    results = get_recent_results(limit=limit)

    print(f"\n📊 Most recent {len(results)} search results:\n")
    for result in results:
        print_result(result, show_full_answer=args.full)


def show_by_query(args) -> None:
    """Show all results for a specific query"""
    if not args.query:
        print("❌ Error: --query is required")
        return

    results = get_results_by_query(args.query, model=args.model)

    print(f"\n📊 Found {len(results)} results for query: \"{args.query}\"")
    if args.model:
        print(f"   Filtered by model: {args.model}")
    print()

    for result in results:
        print_result(result, show_full_answer=args.full)


def show_by_model(args) -> None:
    """Show all results for a specific model"""
    if not args.model:
        print("❌ Error: --model is required")
        return

    limit = args.limit or 50
    results = get_results_by_model(args.model, limit=limit)

    print(f"\n📊 Found {len(results)} results for model: {args.model}\n")

    for result in results:
        print_result(result, show_full_answer=args.full)


def compare_models(args) -> None:
    """Compare results across models for a specific query"""
    if not args.query:
        print("❌ Error: --query is required")
        return

    results_by_model = compare_models_for_query(args.query)

    if not results_by_model:
        print(f"❌ No results found for query: \"{args.query}\"")
        return

    print(f"\n📊 COMPARISON: \"{args.query}\"")
    print(f"{'='*80}\n")
    print(f"Found results from {len(results_by_model)} model(s):\n")

    for model, results in sorted(results_by_model.items()):
        print(f"\n{'='*80}")
        print(f"MODEL: {model}")
        print(f"{'='*80}")
        print(f"Number of results: {len(results)}\n")

        # Show most recent result for this model
        if results:
            latest = results[0]
            print(f"Latest result:")
            print(f"  Timestamp: {format_timestamp(latest['timestamp'])}")
            latest_exec_time = latest.get('execution_time_seconds') or 0
            print(f"  Execution Time: {latest_exec_time:.2f}s")
            print(f"  Answer Length: {len(latest['answer_text'])} chars")
            print(f"  Sources: {len(latest['sources'])}")

            if args.full:
                print(f"\n  Answer:")
                print(f"  {'-'*76}")
                for line in latest['answer_text'].split('\n'):
                    print(f"  {line}")
            else:
                print(f"\n  Answer Preview (first 300 chars):")
                print(f"  {'-'*76}")
                preview = latest['answer_text'][:300]
                if len(latest['answer_text']) > 300:
                    preview += '...'
                for line in preview.split('\n'):
                    print(f"  {line}")


def export_results(args) -> None:
    """Export search results to JSON file"""
    if not args.output:
        print("❌ Error: --output is required")
        return

    try:
        summary = export_database_to_json(
            output_path=args.output,
            query_filter=args.query,
            model_filter=args.model,
            limit=args.limit
        )
        print(f"\n✅ Export Complete!")
        print(f"Records exported: {summary['records_exported']}")
        print(f"File size: {summary['file_size_bytes']:,} bytes")
        print(f"Output path: {summary['output_path']}")
    except ValueError as e:
        print(f"❌ Error: {e}")
    except IOError as e:
        print(f"❌ File error: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description='Analyze and compare Perplexity search results',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # List all queries
  python -m src.analyze list-queries

  # List all models
  python -m src.analyze list-models

  # Show recent results
  python -m src.analyze recent --limit 20

  # Show all results for a specific query
  python -m src.analyze query --query "What is Python?"

  # Show results for a specific query and model
  python -m src.analyze query --query "What is Python?" --model gpt-4

  # Show all results for a specific model
  python -m src.analyze model --model claude-3

  # Compare models for a specific query
  python -m src.analyze compare --query "What is Python?" --full

  # Export all recent results to JSON
  python -m src.analyze export --output results.json

  # Export results for a specific query
  python -m src.analyze export --output query_results.json --query "What is Python?"

  # Export results for a specific model
  python -m src.analyze export --output gpt4_results.json --model gpt-4

  # Export with limit
  python -m src.analyze export --output recent.json --limit 100
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='Command to execute')

    # list-queries command
    parser_queries = subparsers.add_parser('list-queries', help='List all unique queries')
    parser_queries.set_defaults(func=list_queries)

    # list-models command
    parser_models = subparsers.add_parser('list-models', help='List all unique models')
    parser_models.set_defaults(func=list_models)

    # recent command
    parser_recent = subparsers.add_parser('recent', help='Show recent search results')
    parser_recent.add_argument('--limit', type=int, help='Number of results to show (default: 10)')
    parser_recent.add_argument('--full', action='store_true', help='Show full answer text')
    parser_recent.set_defaults(func=show_recent)

    # query command
    parser_query = subparsers.add_parser('query', help='Show results for a specific query')
    parser_query.add_argument('--query', required=True, help='Query to search for')
    parser_query.add_argument('--model', help='Filter by model')
    parser_query.add_argument('--full', action='store_true', help='Show full answer text')
    parser_query.set_defaults(func=show_by_query)

    # model command
    parser_model = subparsers.add_parser('model', help='Show results for a specific model')
    parser_model.add_argument('--model', required=True, help='Model to filter by')
    parser_model.add_argument('--limit', type=int, help='Number of results to show (default: 50)')
    parser_model.add_argument('--full', action='store_true', help='Show full answer text')
    parser_model.set_defaults(func=show_by_model)

    # compare command
    parser_compare = subparsers.add_parser('compare', help='Compare models for a specific query')
    parser_compare.add_argument('--query', required=True, help='Query to compare')
    parser_compare.add_argument('--full', action='store_true', help='Show full answer text')
    parser_compare.set_defaults(func=compare_models)

    # export command
    parser_export = subparsers.add_parser('export', help='Export search results to JSON')
    parser_export.add_argument('--output', '-o', required=True,
                               help='Output JSON file path')
    parser_export.add_argument('--query', help='Filter by query text')
    parser_export.add_argument('--model', help='Filter by model name')
    parser_export.add_argument('--limit', type=int, help='Limit number of results')
    parser_export.set_defaults(func=export_results)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    # Execute the command
    args.func(args)


if __name__ == '__main__':
    main()
