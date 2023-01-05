# Chess Theory Tree
### 
<p align="center">
  <img src="tree_example.png">
</p>

Parse a PGN database of chess matches into a tree that fits each game's opening to a tree of [ECO codes](https://www.365chess.com/eco.php). The tree above parses a FICS Games Database (83171 games) with all time controls, average rating > 2000, and for entirety of 2022.  The games are each matched to nodes in the theory tree with traversal, and the positions with less than 2% occurance are filtered out to keep the graph legible.

TODO:
- [x] get some data from High elo players
- [x] learn how to use ECO codes
- [x] plot K most popular openings/ECO codes on Netgraph
- [ ] try using PyQT or d3.js to overlay chess board for each position
    - PyQT example: https://github.com/paulbrodersen/netgraph/issues/46


