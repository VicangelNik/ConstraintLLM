# What the LLM takes in and out

Every request is made in `src/constraintllm/llm.py`. The model receives two messages and nothing else:

```python
request_kwargs = {
    "model": self.settings.model_name,
    "temperature": temperature,
    "messages": [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": prompt},
    ],
}
```

- **Input:** `system_prompt` (fixed instructions per method) and `prompt` (the problem statement, plus retrieved examples for RAG/CARM/TOT, or the failing code and solver output for a repair).
- **Output:** one text reply, normally a fenced `python` code block. The program extracts the code and saves it as `user_code.py` in a temporary folder, then executes it with PyCSP3 (`python3 user_code.py -data=<file.json> -solve`).

The code does not concatenate the two messages. The provider's chat template turns them into one token sequence, with the system turn first. That difference matters for two reasons:

- Models are trained to treat the system message as higher-priority instructions, so it carries different weight than the same text placed in the user message.
- The token count in `usage.prompt_tokens` is larger than the character counts in the trace suggest. It includes the template's role tokens, and the characters of both messages are tokenized.

## Example: `calls_66428.jsonl`

Problem `SendMore`, method `CARM`. Long text is shortened with `...`.

**Call 1: code generation**

```json
{
  "problem": "SendMore",
  "method": "CARM",
  "purpose": "generate_code",
  "model": "nvidia/nemotron-3-ultra-550b-a55b:free",
  "temperature": 0.01,
  "finish_reason": "stop",
  "usage": { "prompt_tokens": 4533, "completion_tokens": 12879, "total_tokens": 17412 },
  "system_prompt": "You are an expert in constraint programming and PyCSP3.\nConvert the given problem statement into correct PyCSP3 code.\nRules:\n- Do not solve the problem manually.\n- Only output Python code in a single ```python``` block.\n ...",
  "prompt": "Here are some similar questions and codes for reference:\n\ndescription1: ... result code1: ... The problem:\n**Problem Description:**\nThis is a cryptarithmetic (alphametic) puzzle ...",
  "response": "```python\nfrom pycsp3 import *\n\n# Parse input data ...\nword1, word2, word3 = words\n ..."
}
```

**Call 2: repair of that code on case `0.json`**

```json
{
  "problem": "SendMore",
  "method": "CARM",
  "case": "0.json",
  "round": 1,
  "purpose": "fix_code",
  "temperature": 0.0,
  "system_prompt": "You are repairing a PyCSP3 model.\nReturn only corrected Python code inside one ```python``` block.\n ...",
  "prompt": "Problem statement:\n...\n\nCurrent code:\n```python\n...\n```\n\nInput instance:\n...\n\nExpected output:\n...\n\nObserved stdout:\n...\n\nObserved stderr:\n...",
  "response": "```python\nfrom pycsp3 import *\n ..."
}
```

Only `system_prompt` and `prompt` are the input, and `response` is the output. The other fields (`purpose`, `problem`, `method`, `case`, `round`, `usage`, ...) are metadata and are not sent to the model.
