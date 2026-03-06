#!/usr/bin/env python3
"""
Query usage statistics and quota from new-api deployment.
Usage: uv run python query_usage.py --key sk-xxxxx [--limit 10] [--json] [--by-model]
"""

import argparse
import json
import sys
from collections import defaultdict
from datetime import datetime
from urllib.request import Request, urlopen

BASE_URL = "BASE_URL"
QUOTA_ENDPOINT = "/api/usage/token/"
LOG_ENDPOINT = "/api/log/token"


def query_quota(api_key: str) -> dict:
    """Query quota/balance data from new-api."""
    url = f"{BASE_URL}{QUOTA_ENDPOINT}"
    headers = {"Authorization": f"Bearer {api_key}"}

    req = Request(url, headers=headers, method="GET")
    with urlopen(req) as response:
        return json.loads(response.read().decode("utf-8"))


def query_usage(api_key: str) -> dict:
    """Query usage logs from new-api."""
    url = f"{BASE_URL}{LOG_ENDPOINT}?key={api_key}"
    headers = {"Authorization": f"Bearer {api_key}"}

    req = Request(url, headers=headers, method="GET")
    with urlopen(req) as response:
        return json.loads(response.read().decode("utf-8"))


def format_timestamp(ts: int) -> str:
    """Convert Unix timestamp to readable format."""
    if ts == 0:
        return "Never"
    return datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")


def format_quota(quota: int) -> str:
    """Format quota with thousands separator."""
    return f"{quota:,}"


def quota_to_usd(quota: int) -> str:
    """Convert quota to USD (500000 quota = $1)."""
    usd = quota / 500000
    return f"${usd:.3f}"


def print_by_model(records: list):
    """Print usage statistics grouped by model."""
    model_stats = defaultdict(lambda: {
        "count": 0,
        "quota": 0,
        "prompt_tokens": 0,
        "completion_tokens": 0
    })

    for r in records:
        model = r["model_name"]
        model_stats[model]["count"] += 1
        model_stats[model]["quota"] += r["quota"]
        model_stats[model]["prompt_tokens"] += r["prompt_tokens"]
        model_stats[model]["completion_tokens"] += r["completion_tokens"]

    # Sort by quota descending
    sorted_models = sorted(model_stats.items(), key=lambda x: x[1]["quota"], reverse=True)

    print(f"\n{'='*80}")
    print(f"  Usage by Model")
    print(f"{'='*80}")
    print(f"{'Model':<30} {'Calls':>8} {'Quota (USD)':>12} {'Input':>12} {'Output':>10}")
    print("-" * 80)

    total_quota = 0
    for model, stats in sorted_models:
        usd = quota_to_usd(stats["quota"])
        total_quota += stats["quota"]
        print(f"{model:<30} {stats['count']:>8} {usd:>12} {format_quota(stats['prompt_tokens']):>12} {format_quota(stats['completion_tokens']):>10}")

    print("-" * 80)
    print(f"{'TOTAL':<30} {len(records):>8} {quota_to_usd(total_quota):>12}")
    print(f"{'='*80}\n")


def print_summary(quota_data: dict, usage_data: dict, limit: int):
    """Print formatted summary with quota and usage."""
    if not quota_data.get("code"):
        print(f"Error: {quota_data.get('message', 'Unknown error')}")
        return

    q = quota_data.get("data", {})

    # Print quota/balance section
    print(f"\n{'='*60}")
    print(f"  Token Info")
    print(f"{'='*60}")
    print(f"  Name:       {q.get('name', 'Unknown')}")
    print(f"  Total:      {quota_to_usd(q.get('total_granted', 0))}")
    print(f"  Used:       {quota_to_usd(q.get('total_used', 0))}")
    print(f"  Remaining:  {quota_to_usd(q.get('total_available', 0))}")
    print(f"  Expires:    {format_timestamp(q.get('expires_at', 0))}")
    print(f"{'='*60}\n")

    # Print usage logs section
    if not usage_data.get("success") and not usage_data.get("data"):
        print(f"Usage log error: {usage_data.get('message', 'Unknown error')}")
        return

    records = usage_data.get("data", [])
    if not records:
        print("No usage records found.")
        return

    total_quota = sum(r["quota"] for r in records)
    total_prompt = sum(r["prompt_tokens"] for r in records)
    total_completion = sum(r["completion_tokens"] for r in records)

    print(f"  Usage Statistics ({len(records)} records)")
    print(f"  Total Quota:    {format_quota(total_quota)}")
    print(f"  Input Tokens:   {format_quota(total_prompt)}")
    print(f"  Output Tokens:  {format_quota(total_completion)}")
    print(f"{'='*60}\n")

    print(f"Recent {min(limit, len(records))} calls:")
    print("-" * 100)
    print(f"{'Time':<20} {'Model':<22} {'Quota':>10} {'Input':>8} {'Output':>8} {'Time(ms)':>8}")
    print("-" * 100)

    for record in records[:limit]:
        time_str = format_timestamp(record["created_at"])
        model = record["model_name"][:20]
        quota = format_quota(record["quota"])
        prompt = format_quota(record["prompt_tokens"])
        completion = format_quota(record["completion_tokens"])
        use_time = record["use_time"]

        print(f"{time_str:<20} {model:<22} {quota:>10} {prompt:>8} {completion:>8} {use_time:>8}")


def main():
    parser = argparse.ArgumentParser(description="Query new-api usage statistics and quota")
    parser.add_argument("--key", "-k", required=True, help="API key to query")
    parser.add_argument("--limit", "-l", type=int, default=10, help="Number of records to show")
    parser.add_argument("--json", "-j", action="store_true", help="Output raw JSON")
    parser.add_argument("--quota-only", "-q", action="store_true", help="Only show quota/balance")
    parser.add_argument("--by-model", "-m", action="store_true", help="Show usage grouped by model")

    args = parser.parse_args()

    try:
        quota_data = query_quota(args.key)

        if args.quota_only:
            if args.json:
                print(json.dumps(quota_data, indent=2, ensure_ascii=False))
            else:
                q = quota_data.get("data", {})
                print(f"\nToken Name:    {q.get('name', 'Unknown')}")
                print(f"Total Quota:   {quota_to_usd(q.get('total_granted', 0))}")
                print(f"Used:          {quota_to_usd(q.get('total_used', 0))}")
                print(f"Remaining:     {quota_to_usd(q.get('total_available', 0))}")
                print(f"Expires:       {format_timestamp(q.get('expires_at', 0))}\n")
            return

        usage_data = query_usage(args.key)

        if args.json:
            print(json.dumps({"quota": quota_data, "usage": usage_data}, indent=2, ensure_ascii=False))
        elif args.by_model:
            records = usage_data.get("data", [])
            if not records:
                print("No usage records found.")
                return
            print_by_model(records)
        else:
            print_summary(quota_data, usage_data, args.limit)

    except Exception as e:
        print(f"Error querying API: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
