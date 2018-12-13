import read_graph
import util

def wcg_degrees(wcg_edge_weights):
    odegs, idegs = {}, {}
    for src, dst in wcg_edge_weights:
        if src not in odegs:
            odegs[src] = 0.
        if dst not in idegs:
            idegs[dst] = 0.
        odegs[src] += wcg_edge_weights[src, dst]
        idegs[dst] += wcg_edge_weights[src, dst]
    return odegs, idegs

def wcg_modularity(wcg, bcg_node_info, bcg_id_to_nid, wcg_edge_weights):
    m = sum(wcg_edge_weights.itervalues())
    odegs, idegs = wcg_degrees(wcg_edge_weights)
    Q = 0.
    for i, j in wcg_edge_weights:
        if not util.same_party(bcg_node_info, i, j):
            continue
        Aij = wcg_edge_weights[i, j] if ((i, j) in wcg_edge_weights) else 0.
        dio, dji = odegs[i], idegs[j]
        Q += Aij - dio*dji/m
    Q /= m
    return Q

def main():
    wcg, wcg_info = read_graph.read_wcg("senate", 115)
    print "\nwcg modularity test"
    modularity = wcg_modularity(wcg, *wcg_info)
    print modularity

if __name__ == "__main__":
    main()