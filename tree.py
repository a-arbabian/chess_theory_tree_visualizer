import io
import json
import matplotlib; matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
import networkx as nx
from netgraph import Graph, InteractiveGraph, get_sugiyama_layout
import chess 
import chess.pgn
import chess.svg

DEPTH = 4
GAMES = 1500
MAX_EDGE_WIDTH = 10
MIN_EDGE_WIDTH = 0.2
NODE_SIZE = 6
COUNT_CUTOFF_FRACTION = 0.02 

def normalize_edge_width(counter):
    return MIN_EDGE_WIDTH + (MAX_EDGE_WIDTH - MIN_EDGE_WIDTH) * (counter / GAMES)

def get_counter_percent(counter):
    return round(counter / GAMES * 100, 2)

if __name__ == "__main__":
    tree = nx.DiGraph()
    
    # # Traverse ECO pgn file to get all possible openings
    # file = open("data/eco_pgn/eco.pgn", encoding="utf-8")
    # while True:
    #     line = file.readline()
        
        
    #     print(game.headers)
    #     eco_code = game.headers['ECO']
    #     opening_name = game.headers['Opening']
        
    #     board = game.board()
    #     # Make all the moves in the opening
    #     for move in game.mainline_moves():
    #         board.push(move)
            
    #     # Add the final position to the tree
    #     tree.add_node(board.fen(), label=opening_name, counter=0)
        
    
    pgn = open("data/pgn/ficsgamesdb_202212_blitz2000_nomovetimes_271471.pgn")
    game_idx = 0
    while True:
        game = chess.pgn.read_game(pgn)
        if game is None:
            break  # end of file
        
        if game_idx > GAMES:
            break # enough games parsed
        print("Parsing game", game_idx)
        
        # Get the ECO code fot this game's opening
        eco_code = game.headers['ECO']
        
        # starting position/root node
        board = game.board()
        if board.fen() not in tree.nodes:
            tree.add_node(board.fen(), label='Starting\nPosition', counter=1)
            root = board.fen()
        else:
            tree.nodes[board.fen()]['counter'] += 1
        
        
        
        for move_idx, move in enumerate(game.mainline_moves()):
            if move_idx > DEPTH:
                break
            
            # Keep the previous board position for edge creation
            prev_board_fen = board.fen()
            # Get SAN notation of the move
            san = board.san(move)
            # Make the move on the board
            board.push(move)
            
            # Add/Update node and edge
            if board.fen() not in tree.nodes:
                tree.add_node(board.fen(), label=san, counter=1)
                tree.add_edge(prev_board_fen, board.fen(), label=san, counter=1)
            elif board.fen() == prev_board_fen:
                continue
            else:
                try:
                    tree.nodes[board.fen()]['counter'] += 1
                    tree.edges[(prev_board_fen, board.fen())]['counter'] += 1
                except KeyError:
                    print(f"KeyError: {prev_board_fen} -> {board.fen()}")
                    break

        game_idx += 1
        
            
        
    # Filter edges with low counter
    threshold = int(COUNT_CUTOFF_FRACTION * GAMES)
    tree.remove_edges_from([(n1, n2) for n1, n2, w in tree.edges(data="counter") if w < threshold])
    tree.remove_nodes_from(list(nx.isolates(tree)))
    
    # Annotations
    annotations = {node: chess.svg.board(chess.Board(fen=node), size=100) for node in tree.nodes}
    
    # Node layout
    node_positions = get_sugiyama_layout(list(tree.edges), node_size=NODE_SIZE)
    node_positions = {node : (-x, y) for node, (y, x) in node_positions.items()}
    
    
    fig, ax = plt.subplots(figsize=(18, 12))

    plot_instance = InteractiveGraph(tree, ax=ax,
                                     node_layout=node_positions,
                                    #  node_size=NODE_SIZE,
                                     node_labels=nx.get_node_attributes(tree, 'label'),
                                     node_label_fontdict=dict(size=10),
                                     edge_labels={edge: f"{get_counter_percent(tree.edges[edge]['counter'])}%" for edge in tree.edges},
                                     edge_width={edge: normalize_edge_width(tree.edges[edge]['counter']) for edge in tree.edges},
                                    #  annotations=annotations,
                                     )
    
    json_tree = nx.tree_data(tree, root=root)
    with open('tree.json', 'w') as fp:
        json.dump(json_tree, fp)
        
    plt.show()