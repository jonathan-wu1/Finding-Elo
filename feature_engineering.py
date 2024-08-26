from collections import defaultdict, Counter
import chess
import chess.pgn
import time
import multiprocessing as mp
import sys
from stockfish import Stockfish
import numpy as np
import json

def stockfish_cpl(moves):
    """ returns the average cpl of white and black"""
    stockfish=Stockfish("stockfish/stockfish-windows-x86-64-avx2.exe")
    stockfish.set_depth(12)#How deep the AI looks
    
    position_evals = []

    cpl_w = []
    cpl_b = []
    
    board = chess.Board()
    
    if len(moves) < 6:
        return ([], [], [])
    
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

        position_evals.append(player_eval["value"])
        
        # continue if it is a mate
        if player_eval["type"] == "mate" or best_eval["type"] == "mate":
            position_evals.append(position_evals[-1])
            continue
        else:
            position_evals.append(player_eval["value"])
            if i%2 == 0:
                cpl_w.append(best_eval["value"] - player_eval["value"])
                
            else:
                cpl_b.append(player_eval["value"] - best_eval["value"])

    return (cpl_w, cpl_b, position_evals)

def extract_features(chess_game):
    features = defaultdict(int)
    features["event"] = chess_game.headers.get('Event', '')
    features["round"] = chess_game.headers.get('Round', '')
    features["white"] = chess_game.headers.get('White', '')
    features["black"] = chess_game.headers.get('Black', '')
    features["result"] = chess_game.headers.get('Result', '')
    features["moves"] = [str(move) for move in chess_game.mainline_moves()]
    features["white_elo"] = chess_game.headers.get('WhiteElo', '')
    features["black_elo"] = chess_game.headers.get('BlackElo', '')
    features["ECO"] = chess_game.headers.get('ECO', '')
    features["Opening"] = chess_game.headers.get('Opening', '')
    

    cpls = stockfish_cpl(features["moves"])
    features["white_cpl"] = cpls[0]
    features["black_cpl"] = cpls[1]
    features["stockfish_eval"] = cpls[2]

    first_check = True
    first_queen_move = True

    node = chess_game
    while node.variations:  # and node.board().fullmove_number < cut_off:
        move = node.variation(0).move

        board = node.board()

        # print(board.fullmove_number, move)
        moved_piece = board.piece_type_at(move.from_square)
        captured_piece = board.piece_type_at(move.to_square)

        if moved_piece == chess.QUEEN and first_queen_move:
            features['queen_moved_at'] = board.fullmove_number
            first_queen_move = False

        if captured_piece == chess.QUEEN:
            features['queen_changed_at'] = board.fullmove_number

        # if captured_piece:
            # print('Capture', board.fullmove_number, move, moved_piece,captured_piece)
            # captures[]
            # if board.fullmove_number == 10:
            #    features['captures_5']
        if move.promotion:
            features['promotion'] += 1
        if board.is_check():
            features['total_checks'] += 1
            if first_check:
                features['first_check_at'] = board.fullmove_number
                first_check = False

        if move == 'e1g1':
            features['white_king_castle'] = board.fullmove_number
        elif move == 'e1c1':
            features['white_queen_castle'] = board.fullmove_number
        elif move == 'e8g8':
            features['black_king_castle'] = board.fullmove_number
        elif move == 'e8c8':
            features['black_queen_castle'] = board.fullmove_number


        node = node.variation(0)
    
    if board.is_checkmate():
        features['is_checkmate'] += 1
    if board.is_stalemate():
        features['is_stalemate'] += 1
    if board.is_insufficient_material():
        features['insufficient_material'] += 1
    if board.can_claim_draw():
        features['can_claim_draw'] += 1
    features['total_moves'] = board.fullmove_number

    # Pieces at the end of the chess_game
    piece_placement = board.fen().split()[0]
    end_pieces = Counter(x for x in piece_placement if x.isalpha())

    # count number of piece at end position
    features.update({'end_' + piece: cnt
                     for piece, cnt in end_pieces.items()})
    
    return features

def process_pgn_file(pgn_file_path, limit):
    games = []
    pgn_file = open(pgn_file_path)
    game = chess.pgn.read_game(pgn_file)

    count = 0
    while game is not None:
        # Read the next game
        games.append(game)
        game = chess.pgn.read_game(pgn_file)
        count += 1
        if count == limit:
            break
        
    pgn_file.close()

    return games



if __name__ == "__main__":

    # run this script first
    # !pgn-extract -e data/data.pgn --output data/data_openings.pgn
    
    sys.setrecursionlimit(50000)
    start_time = time.time()
    pgn_file_path = "data/data_openings.pgn"
    games = process_pgn_file(pgn_file_path, 21600)
    print(f"number of games: {len(games)}")

    with mp.Pool() as pool:
      result = pool.map(extract_features, games)
    

    print(result[0])
    # Save to an NDJSON file
    ndjson_file_path = 'data/raw/feature_engineered1.ndjson'

    with open(ndjson_file_path, 'w') as f:
        for item in result:
            json.dump(item, f)
            f.write('\n')  # Write a newline after each JSON object

    end_time = time.time()
    print(end_time - start_time)

