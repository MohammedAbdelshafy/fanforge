---
type: repository
status: active
owner_repo: MohammedAbdelshafy/fanforge
product_name: FanForge
source_of_truth: https://github.com/MohammedAbdelshafy/fanforge
---

# FanForge CONTEXT

One job: organize asset requests into jobs, run them through a chosen backend and create a review gallery.

## Inputs
- Commands and backend contract: [README](README.md)
- Implementation: [fanforge](fanforge/)
- Tests: [tests](tests/)
- Sample brief: [samples](samples/)

## Process
1. Validate the project brief and each item.
2. Queue one job per item without hiding overwrites.
3. Run only queued jobs through the selected backend.
4. Label mock output accurately.
5. Build a gallery with each item's prompt, asset path and status.
6. Human reviews assets before delivery.

## Output
A job queue, assets and a gallery index.

## Check
Run tests and the sample pipeline with the mock backend. Do not label placeholders as AI-generated and do not claim a provider works unless tested with the actual configuration.
