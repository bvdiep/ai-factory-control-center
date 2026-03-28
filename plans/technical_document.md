# Technical Document

## Storage Structure
- `$OPENHANDS_STORAGE_PATH/{project_id}/{phase_id}/sessions/`: Stores OpenHands session data.
- `$OPENHANDS_STORAGE_PATH/{project_id}/{phase_id}/logs/`: Stores execution logs.

## Metrics JSON Structure
```json
{
  "prompt_tokens": 100,
  "completion_tokens": 50,
  "reasoning_tokens": 10,
  "cached_tokens_read": 0,
  "cached_tokens_creation": 0,
  "latency": 1.5,
  "model_name": "gpt-4o",
  "provider": "openai"
}
```
