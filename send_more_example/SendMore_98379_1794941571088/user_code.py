import json
import sys
from pycsp3 import *

# Read the JSON input from stdin
data = json.load(sys.stdin)
words = data['words']
word1, word2, word3 = words

# Collect all unique letters
letters = sorted(set(word1 + word2 + word3))

# Create a variable for each letter (domain 0..9)
var = {ch: Var(dom=range(10)) for ch in letters}

# Post constraints
satisfy(
    AllDifferent(list(var.values())),
    # Leading letters cannot be zero
    var[word1[0]] != 0,
    var[word2[0]] != 0,
    var[word3[0]] != 0,
    # Arithmetic constraint: word1 + word2 == word3
    Sum(var[word1[i]] * (10 ** (len(word1) - 1 - i)) for i in range(len(word1))) +
    Sum(var[word2[i]] * (10 ** (len(word2) - 1 - i)) for i in range(len(word2))) ==
    Sum(var[word3[i]] * (10 ** (len(word3) - 1 - i)) for i in range(len(word3)))
)

# Solve the model and print the numeric value of word3
if solve() is SAT:
    value = 0
    for ch in word3:
        value = value * 10 + var[ch].value
    print(f"my answer is {value}")