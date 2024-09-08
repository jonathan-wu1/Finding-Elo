# making cpl function
import chess.engine
import chess 
from stockfish import Stockfish
import numpy as np


def stockfish_cpl(row):
    """ returns the average cpl of white and black"""
    moves = row["Moves"]
    stockfish=Stockfish("../stockfish/stockfish-windows-x86-64-avx2.exe")
    stockfish.set_depth(12)#How deep the AI looks
    
    cpl_w = []
    cpl_b = []
    
    board = chess.Board()
    
    # exclude the first 6 moves in our analysis
    for j in range(6):
        board.push_san(moves[j])
    

    for i in range(6, len(moves)):
        # find the best move from stockfish
        stockfish.set_fen_position(board.fen())
        best_move = stockfish.get_best_move()

        # evaluate the stockfish move
        board.push_san(best_move)
        best_eval = stockfish.get_evaluation()
        board.pop()

        # evaluate the player move
        board.push_san(moves[i])
        stockfish.set_fen_position(board.fen())
        player_eval = stockfish.get_evaluation()
        

        # continue if it is a mate
        if player_eval["type"] == "mate" or best_eval["type"] == "mate":
            continue
        
        if i%2 == 0:
            cpl_w.append(best_eval["value"] - player_eval["value"])
            
        else:
            cpl_b.append(player_eval["value"] - best_eval["value"])

    return (np.mean(cpl_w), np.mean(cpl_b))



# Function to calculate material in centipawns
def calculate_material(board):
    material = 0
    material = {"white": 0,
                "black": 0}
    piece_values = {
        chess.PAWN: 100,
        chess.KNIGHT: 320,
        chess.BISHOP: 330,
        chess.ROOK: 500,
        chess.QUEEN: 900,
        chess.KING: 0  # King's value is not counted
    }

    for piece_type in piece_values:
        material["white"] += len(board.pieces(piece_type, chess.WHITE)) * piece_values[piece_type]
        material["black"] += len(board.pieces(piece_type, chess.BLACK)) * piece_values[piece_type]
    
    return material
