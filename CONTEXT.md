---
type: repository
status: active
owner_repo: MohammedAbdelshafy/fanforge
product_name: Creative Asset Queue
source_of_truth: https://github.com/MohammedAbdelshafy/fanforge
---

# Creative Asset Queue CONTEXT

One job: turn a brief into a queue of media tasks and a gallery of outputs from the selected backend.

## Inputs
- Commands and backend limits: [README](README.md)
- Implementation: [fanforge](fanforge/)
- Tests: [tests](tests/)
- Samples: [samples](samples/)

## Process
1. Validate a brief and expand it into queued tasks.
2. Run queued items through the selected backend.
3. Record status and create a gallery of outputs.
4. Clearly label mock assets; never describe placeholders as generated images or videos.
5. Review the backend, provider cost and commercial rights before accepting client work.

## Output
A task queue and a gallery with task status and asset paths.

## Check
Run the tests and bundled mock sample. Verify re-running a queue does not silently overwrite important output. Do not call the project a live generation service unless a real backend is installed and tested.
