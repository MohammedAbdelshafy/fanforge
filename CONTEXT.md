---
type: repository
status: active
owner_repo: MohammedAbdelshafy/fanforge
product_name: Asset Queue & Gallery
source_of_truth: https://github.com/MohammedAbdelshafy/fanforge
---

# Asset Queue & Gallery CONTEXT

One job: turn an asset brief into a queue, run jobs through a configured backend, and create a gallery of results.

## Inputs
- Usage: [README](README.md)
- Implementation: [fanforge](fanforge/)
- Tests: [tests](tests/)
- Example brief: [samples](samples/)

## Process
1. Validate the brief and create job records.
2. Execute queued jobs through the selected backend.
3. Track each result as done or failed.
4. Build a gallery that shows each item's status and output location.
5. Keep mock output clearly labeled as a placeholder.

## Output
A queue file, generated assets from the configured backend, and a gallery index.

## Check
Run the tests and a sample run using the mock backend. Do not describe placeholders as generated imagery or promise external model output until a real backend is verified.
