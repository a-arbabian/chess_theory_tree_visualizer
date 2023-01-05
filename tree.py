import io
import json
import numpy as np
import matplotlib; matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import networkx as nx
from netgraph import Graph, InteractiveGraph, get_sugiyama_layout
import chess 
import chess.pgn
import chess.svg

MAX_GAME_DEPTH = 6
GAMES = 1e6
MAX_EDGE_WIDTH = 12
MIN_EDGE_WIDTH = 0.2
COUNT_CUTOFF_FRACTION = 0.02 # must account for at least 2% of games
NODE_SIZE = 5
SCALE = (1., 2.)


def count_games_in_pgn(pgn_path):
    pgn = open(pgn_path, "r")
    #read content of file to string
    data = pgn.read()
    #get number of occurrences of the substring in the string
    return data.count("[Event")
    

def normalize_edge_width(counter):
    return MIN_EDGE_WIDTH + (MAX_EDGE_WIDTH - MIN_EDGE_WIDTH) * (counter / GAMES)

def get_counter_percent(counter, total):
    if total == 0:
        return 0
    return round(counter / total * 100, 2)

def visualize_tree(tree, edge_counters=False):
    fig, ax = plt.subplots()
    # Node colors based on ECO Code 
    color_map = {
        'A': ('red', 'Flank Openings'),
        'B': ('orange', "'Semi-Open' games (Other than the French Defence)"),
        'C': ('yellow', "'Open' games (and the French Defence)"),
        'D': ('green', "'Closed' games and 'Semi-Closed' games (incl. the Grünfeld Defence)"),
        'E': ('lightblue', "Indian Defences (Other than the Grünfeld Defence)"),
        '0': ('white', 'No ECO Code'),
    }
    node_color = {node: color_map[data.get('eco', '0')[0]][0] for node, data in tree.nodes(data=True)}
    
    # Annotations
    annotations = nx.get_node_attributes(tree, 'eco')
    
    # Node layout (left to right)
    node_positions = get_sugiyama_layout(list(tree.edges), 
                                         node_size=NODE_SIZE,
                                         scale=SCALE)
    node_positions = {node : (-x, y) for node, (y, x) in node_positions.items()}
    # print(node_positions.values())

    # Node labels
    node_labels = nx.get_node_attributes(tree, 'label')
    node_labels = {node: '\n'.join(label.split()) for node, label in node_labels.items()}
    
    if edge_counters:
        # Edge labels are the move SAN notation and
        #   the percentage of games that move was played from previous position
        edge_labels = {
            (n1, n2): f"{data['label']}\n"
            f"{get_counter_percent(tree.edges[(n1, n2)]['counter'], tree.nodes[n1]['counter'])}%"
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
                                    node_size=NODE_SIZE,
                                    node_color=node_color,
                                    node_labels=node_labels,
                                    node_label_fontdict=dict(size=10),
                                    edge_labels=edge_labels,
                                    edge_label_fontdict=dict(size=7),
                                    edge_width=edge_width,
                                    annotations=annotations,
                                    scale=SCALE,
                                    )
    
    # Legend
    handles = []
    for col, name in color_map.values():
        patch = mpatches.Patch(color=col, label=name)
        handles.append(patch)
    ax.legend(handles=handles, loc='best')
    
    # Resize figure 
    fig.subplots_adjust(left=0, bottom=0, right=1, top=1)
    
    # fig.savefig('test.pdf', dpi=300)
    return plot_instance
    

def parse_eco_data_to_tree(pgn_path: str, save=False) -> 'nx.DiGraph':
    # Make tree to store all the theory positions
    theory_tree = nx.DiGraph()
    # Make root node with starting FEN position
    
    theory_tree.add_node(chess.STARTING_FEN, label='Starting\nPosition', eco='00', counter=0)
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
                theory_tree.add_node(board.fen(), counter=0)
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
    
    
    # pgn file with all the games we want to analyze
    pgn_path = "data/pgn/ficsgamesdb_2022_chess2000_nomovetimes_271748.pgn"
    # Count number of games we have
    GAMES = min(GAMES, count_games_in_pgn(pgn_path))
    
    # Now lets go through a database to get counts for each opening
    pgn = open(pgn_path)
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
            # skip games that don't start from the starting FEN position
            continue
        tree.nodes[board.fen()]['counter'] += 1
        
        print("Parsing game", game_idx)
        for move_idx, move in enumerate(game.mainline_moves()):
            if move_idx > MAX_GAME_DEPTH:
                break
            
            # Keep the previous board position for edge creation
            prev_board_fen = board.fen()
            # Get SAN notation of the move
            san = board.san(move)
            # Make the move on the board
            board.push(move)
            
         
            if board.fen() in tree.nodes:
                try:
                    tree.nodes[board.fen()]['counter'] += 1
                    tree.edges[(prev_board_fen, board.fen())]['counter'] += 1
                    if eco_code == tree.nodes[board.fen()]['eco']:
                        # we've reached the deepest ECO node for this game, after this it not theory
                        break
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