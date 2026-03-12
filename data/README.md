# Data Layout

## `induscp/`

- `statements.json`: latest problem statements and metadata
- `problem_list.txt`: released problem list
- `cost_data/<problem_name>/`: problem-specific code, inputs and optional outputs

## `knowledge_base.json`

- retrieval knowledge base used by `RAG` and `CARM`
- source file for open-source release: `data/csp_train_data4.json`
- current size: 149 entries

## Notes

- The released dataset keeps the latest statements and associated test data.
- Temporary solver artifacts have been removed.
- `user_code.py` files generated during experiments have been removed from the release package.
- The bundled knowledge base is intended for retrieval, not as part of the `IndusCP` evaluation set.
- See `docs/knowledge_base_license_review.md` for source and license risk notes.
