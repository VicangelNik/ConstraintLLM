# Problem WordDesign

find as large a set $S$ of strings (words) of length 8 over the alphabet $W$ = { A,C,G,T } with the following properties:Each word in $S$ has 4 symbols from { C,G };Each pair of distinct words in $S$ differ in at least 4 positions; and Each pair of words x and y in $S$ (where $x$ and $y$ may be identical) are such that the reverse of $x$ and the Watson-Crick complement of $y$ differ in at least 4 positions. The Watson-Crick complement of $y$ is the word where each A is replaced by a T and vice versa and each C is replaced by a G and vice versa.

## Data

  words.json, and a number n

## Model
  constraints: [Lex](http://pycsp.org/documentation/constraints/Lex), [Sum](http://pycsp.org/documentation/constraints/Sum), [Table](http://pycsp.org/documentation/constraints/Table)

## Execution
```
  python WordDesign1.py -data=[words.json,n=<number>]
```

## Links
  - https://www.csplib.org/Problems/prob033/
  - https://www.cril.univ-artois.fr/XCSP23/competitions/csp/csp

## Tags
  realistic, xcsp23

<br />

## _Alternative Model(s)_

#### WordDesign2.py
 - constraints: [Lex](http://pycsp.org/documentation/constraints/Lex), [MDD](http://pycsp.org/documentation/constraints/MDD)
 - tags: realistic, xcsp23
