import chess.engine
import chess 
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import chess.pgn 
from stockfish import Stockfish
import pandas as pd
import time
import numpy as np
import json
from collections import defaultdict, Counter


def change_config(model):
    """
    Takes a string of the requested model, then modifies the config file
    so that maia uses said model.
    """
    with open("lc0_windows\lc0.config", "w") as file:
        file.write(model)

    with open('lc0_windows\lc0.config', 'r') as file:
        updated_content = file.read()
    print(updated_content)


def apply_engine_v2(row, engine, engine_str):
    """
    Takes in a row, and outputs the move match for a given maia engine.
    """
    moves = row["Moves"]
    if len(moves) < 7:
        return None
    mm_w = []
    mm_b = []
    board = chess.Board()
    
    # exclude the first 6 moves in our analysis
    for j in range(6):
        board.push_san(moves[j])
        
    for i in range(6, len(moves)):
    
        if i%2 == 0:
            mm_w.append(get_move(board, engine, engine_str) == moves[i])

        else:
        #if i%2 == 1:
            mm_b.append(get_move(board, engine, engine_str) == moves[i])

        board.push_san(moves[i])

    # Calculate the proportion of True values
    proportion_true_w = sum(mm_w) / len(mm_w)
    proportion_true_b = sum(mm_b) / len(mm_b)    

    w_out = {
        "elo": int(row["BlackElo"]),
        "mm": proportion_true_b
    }
    w_out = {
        "elo": int(row["WhiteElo"]),
        "mm": proportion_true_w
    }
    
    return [w_out, w_out]

def execute_maia_mm_v2(model, games):
    """
    Executes the move matching algorithms and returns a list of dictionaries {elo: , mm: }
    """
    change_config(model)
    maia = chess.engine.SimpleEngine.popen_uci(["lc0_windows\lc0.exe"])
    mm = []

    for game in games:
        try:
            move_matches = apply_engine_v2(game, maia, "maia")
            mm.append(move_matches[0])
            mm.append(move_matches[1])
        except:
            continue
    maia.quit()

    return mm






def execute_stockfish_mm(games, depth):
    """
    Executes the move matching algorithms and returns a list of dictionaries {elo: , mm: }
    """
    mm = []
    stockfish=Stockfish("../stockfish/stockfish-windows-x86-64-avx2.exe")
    stockfish.set_depth(depth)

    for game in games:
        try:
            move_matches = apply_engine_v2(game, stockfish, "stockfish")
            mm.append(move_matches[0])
            mm.append(move_matches[1])
        except:
            continue

    return mm


def closest_100(x):
    if x < 1100:
        return 1100
    elif x > 1900:
        return 1900
    else:
        return round(x / 100) * 100


def maia_cpl(row, stockfish):
    """ returns the cpl of maia engine for both black and white"""
    # making sure there are more than 6 moves
    moves = row["moves"]
    if len(moves) < 7:
        return None
    
    cpl_w = []
    cpl_b = []

    # defining closest maia model based on the white elo
    model_w = f"--weights=lc0_windows\models\maia-{closest_100(int(row['WhiteElo']))}.pb.gz"
    change_config(model_w)
    maia_w = chess.engine.SimpleEngine.popen_uci(["lc0_windows\lc0.exe"])

    # defining closest maia model based on the black elo
    model_b = f"--weights=lc0_windows\models\maia-{closest_100(int(row['BlackElo']))}.pb.gz"
    change_config(model_b)
    maia_b = chess.engine.SimpleEngine.popen_uci(["lc0_windows\lc0.exe"])
    
    board = chess.Board()
    
    # exclude the first 6 moves in our analysis
    for j in range(6):
        board.push_san(moves[j])
        
    for i in range(6, len(moves)):
    
        if i%2 == 0:
            try:
                maia_move = get_move(board, maia_w, "maia")
                cpl_w.append(get_cpl(maia_move, board, stockfish) - get_cpl(moves[i], board, stockfish))
            except:
                print(f"error: white move")
                print(board)
                print(moves[i])
                continue

        else:
            try:
                maia_move = get_move(board, maia_b, "maia")
                cpl_b.append(-(get_cpl(maia_move, board, stockfish) - get_cpl(moves[i], board, stockfish)))
            except:
                print(f"error: black move")
                print(board)
                print(moves[i])
                continue
        board.push_san(moves[i])

    maia_b.quit()
    maia_w.quit()

    return (np.mean(cpl_w), np.mean(cpl_b))
    

def get_cpl(move, board, stockfish):
    board.push_san(move)
    stockfish.set_fen_position(board.fen())
    eval = stockfish.get_evaluation()
    board.pop()

    if (eval["type"] == "cp"):
        return eval["value"]
    else:
        return 0
    
def get_move(board, engine, engine_str):
    """
    Takes the board engine and engine type and returns the best move based on that.
    """
    if engine_str == "maia":
        maia_move = str(engine.play(board, chess.engine.Limit(time=0.0)).move)
        return maia_move
    elif engine_str == "stockfish":
        engine.set_fen_position(board.fen())
        return engine.get_best_move()

