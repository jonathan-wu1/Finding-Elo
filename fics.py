from collections import defaultdict, Counter
import chess
import chess.pgn
import time
import multiprocessing as mp
import sys
from stockfish import Stockfish
import numpy as np
import json

from feature_engineering import *



if __name__ == "__main__":


    # run this script first
    # !pgn-extract -e data/data.pgn --output data/data_openings.pgn
    
    sys.setrecursionlimit(50000)
    start_time = time.time()
    pgn_file_path = "data/landing/ficsgamesdb.pgn"
    games = process_pgn_file(pgn_file_path, 40000)
    print(f"number of games: {len(games)}")

    end_time = time.time()
    print(f"Reading time: {end_time - start_time}")

    start_time = time.time()
    chunk_size = 5000  # Process 1000 games at a time
    num_chunks = len(games) // chunk_size + (1 if len(games) % chunk_size > 0 else 0)

    for i in range(num_chunks):
        chunk_start = time.time()
        print(f"Chunk starting at index {i}")
        start_index = i * chunk_size
        end_index = min(start_index + chunk_size, len(games))
        games_chunk = games[start_index:end_index]

        try:
            with mp.Pool() as pool:
                result = pool.map(extract_features, games_chunk)
            save_results(result, start_index, ndjson_file_path = f'data/raw/fics/fics_{start_index}.ndjson')

            chunk_end = time.time()
            print(f"Processed and saved chunk {start_index} to {start_index + chunk_size}")
            print(f"Time taken to process {chunk_size} games: {chunk_end - chunk_start}")
            print("------------------------------------------")
        except Exception as e:
            print(f"An error occurred while processing chunk {start_index}: {e}")
            
    
    end_time = time.time()
    print(f"Processing time total: {end_time - start_time}")