from pycsp3 import *

words = [w.lower() for w in data]
word1, word2, word3 = words
letters = sorted(set("".join(words)))
pos = {c: i for i, c in enumerate(letters)}

# x[i] is the digit assigned to the ith distinct letter
x = VarArray(size=len(letters), dom=range(10))


def value(word):
    return Sum(x[pos[c]] * 10 ** i for i, c in enumerate(reversed(word)))


satisfy(
    # distinct letters take distinct digits
    AllDifferent(x),

    # leading letters cannot be 0
    [x[pos[w[0]]] > 0 for w in words],

    # the equation
    value(word1) + value(word2) == value(word3)
)

if solve() is SAT:
    solution = values(x)
    print("my answer is", int("".join(str(solution[pos[c]]) for c in word3)))
