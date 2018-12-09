import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import networkx as nx

def draw_graph(graph, colors, title=None):
    graphx = nx.Graph()
    for node in graph.Nodes():
        graphx.add_node(node.GetId())
    for edge in graph.Edges():
        graphx.add_edge(edge.GetSrcNId(), edge.GetDstNId())

    pos = nx.spring_layout(graphx)
    nx.draw_networkx_nodes(graphx, pos, nodelist=colors[0], node_color='r', nodesize=800)
    nx.draw_networkx_nodes(graphx, pos, nodelist=colors[1], node_color='b', nodesize=800)
    nx.draw_networkx_nodes(graphx, pos, nodelist=colors[2], node_color='g', nodesize=800)
    nx.draw_networkx_edges(graphx, pos)

    labels = {n:str(n) for c in colors for n in c}
    # nx.draw_networkx_labels(graphx, pos, labels, font_color='white', font_size=7)
    plt.axis('off')
    plt.legend(handles=[
        mpatches.Patch(color='red', label='central node'),
        mpatches.Patch(color='blue', label='1 hop away'),
        mpatches.Patch(color='green', label='2 hops away')
    ])
    if title:
        plt.title(title)
    plt.show()