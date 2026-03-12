# Problem TSP_TW

The Traveling Salesman Problem with Time Windows (TSPTW) is a popular variant of the TSP where the salesman’s customers must be visited within given time windows.

The Traveling Salesman Problem (TSP) is a classic combinatorial optimization problem where a salesman must visit a set of cities and return to the starting point, minimizing the total travel distance. In this problem, time window constraints are added, meaning each city must be visited within a specified time window. Specifically, each city has an earliest arrival time (Earliest) and a latest arrival time (Latest), and the salesman must arrive and leave each city within these time windows. The objective is to find the shortest route that visits all cities while satisfying all time window constraints.

The code defines variables `x` to represent the visiting order and `a` to represent the visiting times, using constraints to ensure the uniqueness of the visiting order, satisfaction of time windows, and reasonable visiting times. The ultimate goal is to minimize the total travel distance.

## Data (example)
  n020w020-1.json

## Model
  constraints: [AllDifferent](http://pycsp.org/documentation/constraints/AllDifferent), [Element](http://pycsp.org/documentation/constraints/Element), [Sum](http://pycsp.org/documentation/constraints/Sum)

## Execution
  - python TSP_TW1.py -data=<datafile.json>
  - python TSP_TW1.py -data=<datafile.txt> -parser=TSP_TW_Parser.py

## Links
  - https://www.ijcai.org/proceedings/2022/0659.pdf
  - https://github.com/xgillard/ijcai_22_DDLNS
  - https://www.cril.univ-artois.fr/XCSP23/competitions/cop/cop

## Tags
  realistic, xcsp23

<br />

## _Alternative Model(s)_

#### TSP_TW2.py
 - constraints: [Circuit](http://pycsp.org/documentation/constraints/Circuit), [Element](http://pycsp.org/documentation/constraints/Element), [Sum](http://pycsp.org/documentation/constraints/Sum)
 - tags: realistic, xcsp23
