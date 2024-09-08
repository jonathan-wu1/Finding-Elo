# ALL YOU NEED TO KNOW ABOUT MAIA CHESS

## FIRST: Checking Move Match accuracy of Maia Chess Engines

What files to run in what order.

1. extracting.ipynb: This file extracts 5000 games from the lichess database and saves the data to a ndjson file. 
2. lichess_eda.ipynb: This file takes a quick look at the distribution of elo from the 5000 games extracted.
3. executing_mm.ipynb: This file calculates the move match of each Maia Engine for all 5000 games.
4. maia_analysis: This plots the move match accuracy of each different Maia Engine.

![Image](../plots/mm_maia.png)


## SECOND: Maia CPL functions
### More specifically, how to calculate the difference in performance between a player and their respective Maia Engine.

1. maia_functions.py: Contains the functions necessary to calculate the Maia CPL.
2. benchamrking.ipynb: Benchmarks the time required for the Maia CPL to run, and contains examples of how to use the code.