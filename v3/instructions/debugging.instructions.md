---
applyTo: '**'
description: 'Error recovery for tool failures and hypothesis priority for debugging'
---

# Debugging Reference

For the full debugging methodology (scientific method, reproduce-hypothesize-investigate-fix), see `debugger.agent.md`.

## Hypothesis Priority

Test in this order (most common causes first):
1. Config / environment mismatch
2. Wrong import
3. Type / null / undefined
4. Async timing / race condition
5. Data shape mismatch
6. Logic error

## Error Recovery for Tool Failures

| Tool Failure | Recovery |
|---|---|
| `replace_string_in_file` fails (no match) | Re-read file, copy exact text, retry |
| Terminal command hangs | Check timeout, try Ctrl+C or new terminal |
| `get_errors` shows errors after edit | Read errors, fix immediately |
| File not found | Verify path with `file_search`, check case sensitivity |
| Permission denied | Check if file is read-only or locked by another process |
