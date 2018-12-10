import read_graph
import util
import numpy as np
from matplotlib import pyplot as plt

# Calculates "cohesion" (intra-cluster and inter-cluster density) from the wcg
def cohesion(graph, bcg_node_info, bcg_id_to_nid, edge_weights, voting=False):
    print [node.GetId() for node in graph.Nodes()]
    print [i for i in edge_weights]
    # Sanity check: all edge weights in edge_weights:
    for i, j in edge_weights:
        assert (graph.IsEdge(i, j))

    # Initialize and populate party_members and all_members, by scraping through bcg_node_info for type "member"
    #   all_members : list, nids of all congress members' nodes
    #   party_member : dict, party (e.g. "D", "R", "I") => members: list, nids of all congress members of that party
    parties = ["D", "R", "I"]
    party_members = {p:[] for p in parties}
    all_members = []
    for nid in bcg_node_info:
        nid_info = bcg_node_info[nid]
        type_, info = nid_info["type"], nid_info["info"]
        if type_ == "member":
            print nid, nid_info
            party, name, id = info["party"], info["name"], info["id"]
            all_members.append(nid)
            party_members[party].append(nid)
            if not graph.IsNode(nid):
                print nid
            assert(graph.IsNode(nid))
    party_counts = dict(map(lambda x: (x, len(party_members[x])), party_members))

    # Sanity check: sum of party members is equal to total party members
    assert(sum(party_counts.values()) == len(all_members))

    # Calculates intra-cluster (int) and inter-cluster (ext) degrees
    #   Intra-cluster density = sum of weights of all edges between members in a party
    #                           / total edges within the party
    #   Inter-cluster density = sum of weights of all edges from members of a party to members not of that party
    #                           / total edges going out of the party
    # int_degrees = {m: 0 for m in all_members}
    # ext_degrees = {m: 0 for m in all_members}
    d_int = {p: 0. for p in parties}
    d_ext = {p: 0. for p in parties}
    for p in parties:
        w_int, w_ext, int_edges, ext_edges = 0., 0., 0, 0
        members = party_members[p]
        for i in members:
            for j in all_members:
                if graph.IsEdge(i, j):
                    if util.same_party(bcg_node_info, i, j):
                        w_int += edge_weights[i, j]
                        int_edges += 1
                    else:
                        w_ext += edge_weights[i, j]
                        ext_edges += 1
        d_int[p] = w_int / int_edges
        d_ext[p] = w_ext / ext_edges
    d_G = sum(edge_weights.values()) / graph.GetEdges() / 2
    print d_int
    print d_ext
    print d_G
    return d_int, d_ext, d_G

def plot_cosponsorship_cohesion(sessions):
    dints_all, dexts_all, dGs_all = {}, {}, {}
    for session in sessions:
        print("year %s" % session)
        wcg, wcg_info = read_graph.read_wcg("senate", session)
        dints_all[session], dexts_all[session], dGs_all[session] = cohesion(wcg, *wcg_info)
    for party, color in [("D", "b"), ("R", "r"), ("I", "g")]:
        dints = [dints_all[session][party] for session in sessions]
        dexts = [dexts_all[session][party] for session in sessions]
        plt.plot(sessions, dints, color + ".-")
        plt.plot(sessions, dexts, color + ".-")
    dGs = [dGs_all[session] for session in sessions]
    plt.plot(sessions, dGs, "k.--")
    plt.xticks(np.arange(100, 120, 5))
    plt.yticks(np.arange(0, 1, 0.5))
    plt.show()

def plot_voting_cohesion(sessions):
    dints_all, dexts_all, dGs_all = {}, {}, {}
    for session in sessions:
        print("year %s" % session)
        wvg, wvg_info = read_graph.read_wvg("senate", session)
        dints_all[session], dexts_all[session], dGs_all[session] = cohesion(wvg, *wvg_info, voting=True)
    for party, color in [("D", "b"), ("R", "r"), ("I", "g")]:
        dints = [dints_all[session][party] for session in sessions]
        dexts = [dexts_all[session][party] for session in sessions]
        plt.plot(sessions, dints, color + ".-")
        plt.plot(sessions, dexts, color + ".-")
    dGs = [dGs_all[session] for session in sessions]
    plt.plot(sessions, dGs, "k.--")
    plt.xticks(np.arange(100, 120, 5))
    plt.yticks(np.arange(0, 1, 0.5))
    plt.show()

def main():
    plot_cosponsorship_cohesion([114, 115])
    # plot_voting_cohesion([114, 115])

if __name__ == "__main__":
    main()