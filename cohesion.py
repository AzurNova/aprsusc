from read_graph import *

def wcg_cohesion(wcg, bcg_node_info, bcg_id_to_nid, wcg_edge_weights):
    # Sanity check: all edge weights in wcg_edge_weights:
    for i, j in wcg_edge_weights:
        assert (wcg.IsEdge(i, j))

    # Initialize party_members by scraping bcg_node_info for member nodes
    parties = ["D", "R", "I"]
    party_members = {p:[] for p in parties}
    for nid in bcg_node_info:
        nid_info = bcg_node_info[nid]
        type_, info = nid_info["type"], nid_info["info"]
        if type_ == "member":
            party, name, id = info["party"], info["name"], info["id"]
            party_members[party].append(nid)
            assert(wcg.IsNode(nid))
    party_counts = dict(map(lambda x: (x, len(party_members[x])), party_members))

    # print "party counts:", party_counts
    total_congressmen = sum(party_counts.values())

    # Calculates intra-cluster (int) and inter-cluster (ext) degrees
    int_degrees, ext_degrees = {}, {}
    for party in parties:
        members = party_members[party]
        for m in members:
            int_degrees[m] = 0
        for i in range(len(members)-1):
            mi = members[i]
            for j in range(i+1, len(members)):
                mj = members[j]
                if wcg.IsEdge(mi, mj):
                    int_degrees[mi] += 1
                    int_degrees[mj] += 1
        for m in members:
            ext_degrees[m] = wcg.GetNI(m).GetDeg() - int_degrees[m]

    party_cohesion = {"D": 0., "R": 0., "I": 0.}
    member_scores = {}
    for party in parties:
        members = party_members[party]
        if len(members) < 2:
            continue
        int_edges = 0
        for msrc in members:
            score = 0.
            for mdst in members:
                if msrc is not mdst and (msrc, mdst) in wcg_edge_weights:
                    score += wcg_edge_weights[msrc, mdst]
            member_scores[msrc] = score
            party_cohesion[party] += score
            int_edges += int_degrees[msrc]
        int_edges /= 2
        party_cohesion[party] /= int_edges

    party_cohesion["ALL"] = sum(wcg_edge_weights.values()) / wcg.GetEdges()
    # print edge_weights

    return party_cohesion

def wcg_degrees(edge_weights):
    odegs, idegs = {}, {}
    for src, dst in edge_weights:
        if src not in odegs:
            odegs[src] = 0.
        if dst not in idegs:
            idegs[dst] = 0.
        odegs[src] += edge_weights[src, dst]
        idegs[dst] += edge_weights[src, dst]
    return odegs, idegs

def get_parties(node_info, nodes):
    return [node_info[i]["info"]["party"] for i in nodes]

def same_party(node_info, i, j):
    pi, pj = get_parties(node_info, [i, j])
    return pi == pj

def wcg_modularity(wcg, node_info, id_to_nid, edge_weights):
    m = sum(edge_weights.itervalues())
    odegs, idegs = wcg_degrees(edge_weights)
    Q = 0.
    for i, j in edge_weights:
        if not same_party(node_info, i, j):
            continue
        Aij = edge_weights[i,j] if (i,j in edge_weights) else 0.
        dio, dji = odegs[i], idegs[j]
        Q += Aij - dio*dji/m
    Q /= m
    return Q

def main():
    print "wcg cohesion test"
    wcg, wcg_info = read_wcg("senate", 115)
    party_cohesion = wcg_cohesion(wcg, *wcg_info)
    print party_cohesion

    print "\nwcg modularity test"
    modularity = wcg_modularity(wcg, *wcg_info)
    print modularity

    # print "\nrandom test"
    # test = []
    # edge_list = wcg_info[3]
    # for edge in edge_list:
    #     src, dst = edge
    #     if src == 0:
    #         test.append(edge_list[edge])
    # print sum(test)
    # pass


if __name__ == "__main__":
    main()