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
GAMES = 1e6
MAX_EDGE_WIDTH = 10
MIN_EDGE_WIDTH = 0.2
NODE_SIZE = 6
COUNT_CUTOFF_FRACTION = 0.02 # 2% of games


def count_games_in_pgn(pgn):
    counter = 0
    while True:
        game = chess.pgn.read_game(pgn)
        if game is None:
            break
        counter += 1
    return counter

def normalize_edge_width(counter):
    return MIN_EDGE_WIDTH + (MAX_EDGE_WIDTH - MIN_EDGE_WIDTH) * (counter / GAMES)

def get_counter_percent(counter):
    return round(counter / GAMES * 100, 2)

def visualize_tree(tree, edge_counters=False):
    # Annotations
    annotations = nx.get_node_attributes(tree, 'label')
    
    # Node layout (left to right)
    node_positions = get_sugiyama_layout(list(tree.edges), node_size=NODE_SIZE)
    node_positions = {node : (-x, y) for node, (y, x) in node_positions.items()}
    
    
    fig, ax = plt.subplots(figsize=(16, 8))
    if edge_counters:
        edge_labels = {
            (n1, n2): f"{data['label']}\n{get_counter_percent(tree.edges[(n1, n2)]['counter'])}%"
            for n1, n2, data in tree.edges(data=True)
            }
        edge_width = {
            edge: normalize_edge_width(tree.edges[edge]['counter']) 
            for edge in tree.edges
            }
    else:
        edge_labels = nx.get_edge_attributes(tree, 'label')
        edge_width = 0.5
    plot_instance = InteractiveGraph(tree, ax=ax,
                                    node_layout=node_positions,
                                    node_labels=nx.get_node_attributes(tree, 'eco'),
                                    node_label_fontdict=dict(size=10),
                                    edge_labels=edge_labels,
                                    edge_width=edge_width,
                                    annotations=annotations,
                                    )
    return plot_instance
    

def parse_eco_data_to_tree(pgn_path: str, save=False) -> 'nx.DiGraph':
    # Make tree to store all the theory positions
    theory_tree = nx.DiGraph()
    # Make root node with starting FEN position
    
    theory_tree.add_node(chess.STARTING_FEN, label='Starting\nPosition', eco='00')
    root = list(theory_tree.nodes)[0]
    
    pgn = open(pgn_path, encoding="utf-8-sig")
    chess.pgn.read_game(pgn) # skip first header as it's not a game
    while True:
        game = chess.pgn.read_game(pgn)
        if game is None:
            break  # end of file
        
        eco_code = game.headers["ECO"]
        opening_name = game.headers["Opening"]
        try:
            variation_str = game.headers["Variation"]
        except KeyError:
            variation_str = ''
            
        if variation_str:
            variations = variation_str.split(',')
        
        full_name = (opening_name + ' ' + variation_str).strip()
        print(eco_code, full_name)
        # print(game.mainline_moves())
        
        # Make the moves for this variation
        board = game.board()
        num_moves = len(list(game.mainline_moves()))
        for move_idx, move in enumerate(game.mainline_moves()):
            # Keep the previous board position for edge creation
            prev_board_fen = board.fen()
            # Get SAN notation of the move
            san = board.san(move)
            # Make the move on the board
            board.push(move)
            if board.fen() not in theory_tree.nodes:
                # First time seeing this board, add the node and connect to the preceding board
                theory_tree.add_node(board.fen())
                theory_tree.add_edge(prev_board_fen, board.fen(), label=san, counter=0)
                
                if move_idx == num_moves - 1:
                    # This is a leaf node, add the ECO code and opening/variation name
                    theory_tree.nodes[board.fen()]['eco'] = eco_code
                    theory_tree.nodes[board.fen()]['opening'] = opening_name
                    theory_tree.nodes[board.fen()]['label'] = full_name
                    theory_tree.nodes[board.fen()]['variations'] = variation_str
                    
            else:
                # We've seen this board before, do something?
                continue
        
        # print(board)
        # print()
    if save:
        # Save tree to json
        json_tree = nx.tree_data(theory_tree, 
                                 root=root)
        with open('data/eco_tree.json', 'w') as fp:
            json.dump(json_tree, fp)
    return theory_tree

if __name__ == "__main__":
    tree = parse_eco_data_to_tree("data/eco_pgn/eco.pgn", save=False)
    # tree = nx.tree_graph(json.load(open('data/eco_tree.json')))
    print("Number of theory nodes:", len(tree.nodes))
    
    # Count number of games we have
    pgn = open("data/pgn/ficsgamesdb_202212_blitz2000_nomovetimes_271471.pgn")
    GAMES = min(GAMES, count_games_in_pgn(pgn))
    
    # Now lets go through a database to get counts for each opening
    pgn = open("data/pgn/ficsgamesdb_202212_blitz2000_nomovetimes_271471.pgn")
    game_idx = 0
    while True:
        game = chess.pgn.read_game(pgn)
        if game is None:
            break  # end of file
        
        if game_idx > GAMES:
            break # enough games parsed
        
        # Get the ECO code fot this game's opening
        eco_code = game.headers['ECO']
        
        # starting position/root node
        board = game.board()
        if board.fen() != chess.STARTING_FEN:
            # skip games that don't start from the root node
            continue
        
        print("Parsing game", game_idx)
        for move_idx, move in enumerate(game.mainline_moves()):
            if move_idx > DEPTH:
                break
            
            # Keep the previous board position for edge creation
            prev_board_fen = board.fen()
            # Get SAN notation of the move
            san = board.san(move)
            # Make the move on the board
            board.push(move)
            
         
            if board.fen() in tree.nodes:
                try:
                    tree.edges[(prev_board_fen, board.fen())]['counter'] += 1
                except KeyError:
                    print(f"KeyError: {prev_board_fen} -> {board.fen()}")
                    break

        game_idx += 1
        
            
    
    # Filter edges with low counter
    threshold = int(COUNT_CUTOFF_FRACTION * GAMES)
    tree.remove_edges_from([(n1, n2) for n1, n2, w in tree.edges(data="counter") if w < threshold])
    tree.remove_nodes_from(list(nx.isolates(tree)))
    
    # # Save tree to json
    # json_tree = nx.tree_data(tree, root=tree.nodes[chess.STARTING_FEN])
    # with open('tree.json', 'w') as fp:
    #     json.dump(json_tree, fp)
        
    plot_instance = visualize_tree(tree, edge_counters=True)
    plt.show()