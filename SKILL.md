---
name: new-api-usage
description: Query usage statistics and quota from new-api deployments. Automatically detects configured new-api providers in OpenClaw config. Use when the user wants to check API key usage, token consumption, quota details, balance, or model usage statistics. Trigger on keywords like "new-api usage", "API用量", "查询用量", "token使用情况", "余额查询", "剩余额度", "供应商用量".
---

# New API Usage Query

Query usage statistics and quota balance from new-api deployments. Auto-detects configured providers.

## Auto-Detection

The skill reads OpenClaw config (`~/.openclaw/openclaw.json`) to find providers with `baseUrl` matching new-api patterns:
- Contains `new-api`
- Or matches user-configured new-api hosts

Uses the corresponding API key from auth profiles.

## Usage

```bash
# Auto-detect new-api providers and query all
uv run python scripts/query_usage.py --auto

# Query specific key
uv run python scripts/query_usage.py --key sk-xxxxx

# Query specific provider
uv run python scripts/query_usage.py --provider custom-custom36
```

## Options

| Option | Description |
|--------|-------------|
| `--auto` | Auto-detect new-api providers from OpenClaw config |
| `--provider` | Query specific provider by ID |
| `--key` | Manual API key (overrides auto-detection) |
| `--base-url` | Custom base URL (for manual query) |
| `--today` | Show only today's records (default behavior) |
| `--all-records` | Show all records (not just today) |
| `--limit N` | Limit records (default: 100) |
| `--by-model` | Group statistics by model |
| `--quota-only` | Only show balance/quota |
| `--json` | Output raw JSON |

## Default Behavior

When no options specified with `--auto`:
1. Shows today's records only
2. Limits to 100 most recent calls
3. Displays balance + usage summary

## API Endpoints

- **Quota**: `GET /api/usage/token/` (Bearer auth)
- **Usage Log**: `GET /api/log/token?key={api_key}` (Bearer auth)

## Response Fields

| Field | Description |
|-------|-------------|
| `total_granted` | Total quota ($1 = 500000 units) |
| `total_used` | Quota consumed |
| `total_available` | Remaining quota |
| `model_name` | Model used |
| `quota` | Call quota cost |
| `prompt_tokens` | Input tokens |
| `completion_tokens` | Output tokens |
