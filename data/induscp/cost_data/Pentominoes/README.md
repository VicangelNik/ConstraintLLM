# Problem Pentominoes

We are given a grid with specified width and height, a set of tiles, and a deterministic finite automaton (DFA) for each tile that defines the legal sequences or placements of that tile. Additionally, there is a special symbol that must be placed at the end of each row in the grid.

The task is to place the tiles on the grid such that:

1. **Automaton Constraints**: Each tile is placed according to the transitions defined by its associated automaton, ensuring that the sequence or adjacency of tiles adheres to the automaton's rules.

2. **Special Symbol Placement**: The special symbol is placed at the end of every row.

3. **Prohibition of Special Symbol Elsewhere**: The special symbol is not placed in any other cell within the grid.

The objective is to find a valid tiling of the grid that satisfies all these constraints.

Objective

Find a tiling of the grid that adheres to the automaton rules for each tile and ensures the special symbol is correctly placed at the end of each row.

## Data Example
  02.json

## Model
  constraints: [Regular](http://pycsp.org/documentation/constraints/Regular)

## Execution
```
  python Pentominoes1.py -data=<datafile.json>
  python Pentominoes1.py -data=<datafile.dzn> -parser=Pentominoes_ParserZ.py
```

## Links
  - https://fr.wikipedia.org/wiki/Pentomino
  - https://www.minizinc.org/challenge2013/results2013.html

## Tags
  recreational, mzn08, mzn11, mzn13

<br />

## _Alternative Model(s)_

#### Pentominoes2.py
 - constraints: [Regular](http://pycsp.org/documentation/constraints/Regular)
 - tags: recreational, mzn20
