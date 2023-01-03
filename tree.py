import matplotlib; matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
import networkx as nx

from netgraph import Graph, InteractiveGraph

unbalanced_tree = [
    (0, 1),
    (0, 2),
    (0, 3),
    (0, 4),
    (0, 5),
    (2, 6),
    (3, 7),
    (3, 8),
    (4, 9),
    (4, 10),
    (4, 11),
    (5, 12),
    (5, 13),
    (5, 14),
    (5, 15)
]

fig, ax = plt.subplots()
plot_instance = InteractiveGraph(unbalanced_tree, node_layout='dot', ax=ax)

plt.show()