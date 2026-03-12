# Dataset Notes

## Naming

- Dataset name: `IndusCP`
- Retrieval method name in this release: `CARM`

## Release Scope

This release focuses on the CSP dataset and a minimal runnable evaluation pipeline.
It does not include private API keys, experiment logs, internal checkpoints, or temporary repair traces.

## Retrieval Safety

`RAG` and `CARM` are supported in code, but a retrieval corpus is not bundled by default.
Users should prepare a separate retrieval corpus to avoid evaluation leakage.
