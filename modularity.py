import read_happy

def wcg_degrees(edge_weights, member_to_party):
    odegs, idegs = {}, {}
    for i, j in edge_weights:
        if i not in odegs:
            odegs[i] = 0.
        if j not in idegs:
            idegs[j] = 0.
        odegs[i] += edge_weights[i, j]
        idegs[j] += edge_weights[i, j]
    return odegs, idegs

def wcg_modularity(edge_weights, member_to_party):
    m = sum(edge_weights.values())
    print len(edge_weights)
    print m
    for i, j in edge_weights:
        if member_to_party[i] != member_to_party[j]:
            continue
        Aij = edge_weights[i, j]


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
    member_to_party, edge_weights_by_i, edge_weights_total = read_happy.read_wcg("senate", 114)
    modularity = wcg_modularity(edge_weights_by_i, member_to_party)
    print "\nwcg modularity test"
    print modularity

if __name__ == "__main__":
    main()