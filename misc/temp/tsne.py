from old_code_for_bad_data import read_graph
import networkx as nx
from node2vec import Node2Vec

wcg, (bcg_node_info, bcg_id_to_nid, edge_weights) = read_graph.read_wcg("senate", 115)
graph = nx.Graph()
for i,j in edge_weights:
    graph.add_weighted_edges_from([(i,j,edge_weights[i,j])])
print graph.nodes()

node2vec = Node2Vec(graph, dimension=20, walk_length=16, num_walks=100, workers=1)
