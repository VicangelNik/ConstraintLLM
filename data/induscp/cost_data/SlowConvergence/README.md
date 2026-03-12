# Problem SlowConvergence

This problem involves sorting two arrays subject to specific constraints. Given an integer n, the task is to find two arrays x and y, where each element in both arrays lies within the range 0 to 10n. The goal is to satisfy a set of constraints that impose certain relationships between these arrays.



The specific constraints are as follows:

​	1.	For each pair of adjacent elements y[i-1] and y[i] (where i ranges from 2 to n), the condition y[i-1] - y[i] <= 0 must hold, meaning the array y is non-increasing.

​	2.	For each y[i] (where i ranges from 1 to n), the condition y[0] - y[i] <= n - i + 1 must hold, meaning there is a relationship between each element of y and the first element y[0].

​	3.	The condition y[n] - x[0] <= 0 must hold, meaning the last element of array y is less than or equal to the first element of array x.

​	4.	For every pair of elements x[i] and x[j] (where 1 <= i < j <= n), the condition x[i] - x[j] <= 0 must hold, meaning the array x is non-increasing.



The objective is to find arrays x and y that satisfy all these constraints.



The output is the values of the arrays x and y that satisfy all the constraints.

## Data
  An integer n

## Execution
```
  python SlowConvergence.py -data=number
```

## Links
  - https://www.minizinc.org/challenge2008/results2008.html

## Tags
  academic, mzn08
