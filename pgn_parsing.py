import chess
import chess.pgn


pgn = open("data/pgn/ficsgamesdb_202212_blitz2000_nomovetimes_271471.pgn")

while True:
    game = chess.pgn.read_game(pgn)
    print("GAME")
    if game is None:
        break  # end of file

    
    