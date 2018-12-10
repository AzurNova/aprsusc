import read_happy

def wcg_degrees(edge_weights, member_to_party):
    odeg, ideg = {}, {}
    for i, j in edge_weights:
        if i not in odeg:
            odeg[i] = 0.
        if j not in ideg:
            ideg[j] = 0.
        odeg[i] += edge_weights[i, j]
        ideg[j] += edge_weights[i, j]
    return odeg, ideg

def wcg_modularity(edge_weights, member_to_party):
    W = sum(edge_weights.values())
    odeg, ideg = wcg_degrees(edge_weights, member_to_party)
    print len(edge_weights)
    print W
    Q = 0.
    for i, j in edge_weights:
        if member_to_party[i] != member_to_party[j]:
            continue
        Aij = edge_weights[i, j]
        dio, dji = odeg[i], ideg[j]
        Q += Aij - dio*dji/W
    Q /= W
    return Q

def flip_party(member_to_party, m):
    new_mtp = {m: member_to_party[m] for m in member_to_party}
    new_mtp[m] = "D" if member_to_party[m] == "R" else "R"
    return new_mtp

def main():
    member_to_party, edge_weights_by_i, edge_weights_total = read_happy.read_wcg("senate", 114)
    print member_to_party
    modularity = wcg_modularity(edge_weights_by_i, member_to_party)
    print "\nwcg modularity test"
    print modularity

if __name__ == "__main__":
    main()