# Problem SendMore

Cryptarithmetic puzzle `word1 + word2 = word3`: distinct letters take distinct digits, leading letters are non-zero.
Added as a small custom problem (not part of the original IndusCP release).

## Data
  `{"words": [word1, word2, word3]}` (0: SEND+MORE=MONEY, 1: TO+GO=OUT, 2: BASE+BALL=GAMES, 3: CROSS+ROADS=DANGER)

## Output
  Satisfaction problem, so the expected output (`N.out`) is the numeric value of word3, printed as `my answer is <value>`
  (read by `extract_cost` in `run_code.py`).

## Execution
  python SendMore.py -data=0.json -solve

## Model
  constraints: AllDifferent, Sum
