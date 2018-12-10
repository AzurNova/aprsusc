import read_happy
import numpy as np
from matplotlib import pyplot as plt

def main2():
    member_to_party, edge_weights_by_i, edge_weights_total = read_happy.read_wcg("senate", 114)
    cohesion(edge_weights_total, member_to_party)
    # cohesion(edge_weights_total, party_assign)

# Calculates "cohesion" (intra-cluster and inter-cluster density) from the wcg
def cohesion(edge_weights, member_to_party):
    all_members = [m for m in member_to_party]
    print "all_members:", all_members
    party_members = {p : [] for p in ["D", "R", "I"]}
    for member in member_to_party:
        party = member_to_party[member]
        party_members[party].append(member)

    dint = {p : 0. for p in party_members}
    dext = {p : 0. for p in party_members}
    dG   = {p : 0. for p in party_members}
    print "party_members:", party_members
    for party in party_members:
        wint, wext, eint, eext = 0., 0., 0., 0.
        for i in party_members[party]:
            for j in all_members:
                if (i, j) in edge_weights:
                    if member_to_party[i] == member_to_party[j]:
                        wint += edge_weights[i, j]
                        eint += 1
                    else:
                        wext += edge_weights[i, j]
                        eext += 1
        print wint, eint, wext, eext
        if eint > 0:
            dint[party] = wint / eint
        if eext > 0:
            dext[party] = wext / eext
    dG = sum(edge_weights.values()) / len(edge_weights)
    print "dint:", dint
    print "dext:", dext
    print "dG:", dG
    return dint, dext, dG

def plot_cosponsorship_cohesion(sessions):
    dints, dexts, dGs = {}, {}, {}
    for session in sessions:
        print("year %s" % session)
        member_to_party, edge_weights_by_i, edge_weights_total = read_happy.read_wcg("senate", session)
        dints[session], dexts[session], dGs[session] = cohesion(edge_weights_by_i, member_to_party)
    for party, color in [("D", "b"), ("R", "r")]: #, ("I", "g")]:
        dint = [dints[session][party] for session in sessions if dints[session][party] > 0]
        dext = [dexts[session][party] for session in sessions]
        plt.plot(sessions, dint, color + ".-")
        plt.plot(sessions, dext, color + ".-")
    dGs = [dGs[session] for session in sessions]
    plt.plot(sessions, dGs, "k.--")
    plt.xticks(np.arange(95, 116, 5))
    plt.yticks(np.arange(0, 0.6, 0.1))
    plt.grid(color=(0.75, 0.75, 0.75), linestyle='--', linewidth=1)
    plt.show()

# def plot_voting_cohesion(sessions):
#     dints_all, dexts_all, dGs_all = {}, {}, {}
#     for session in sessions:
#         print("year %s" % session)
#         wvg, wvg_info = read_happy.read_wvg("senate", session)
#         dints_all[session], dexts_all[session], dGs_all[session] = cohesion(wvg, *wvg_info, voting=True)
#     for party, color in [("D", "b"), ("R", "r"), ("I", "g")]:
#         dints = [dints_all[session][party] for session in sessions]
#         dexts = [dexts_all[session][party] for session in sessions]
#         plt.plot(sessions, dints, color + ".-")
#         plt.plot(sessions, dexts, color + ".-")
#     dGs = [dGs_all[session] for session in sessions]
#     plt.plot(sessions, dGs, "k.--")
#     plt.xticks(np.arange(100, 120, 5))
#     plt.yticks(np.arange(0, 1, 0.5))
#     plt.show()

def main():
    # main2()
    plot_cosponsorship_cohesion(range(93,115))
    # plot_voting_cohesion([114, 115])

if __name__ == "__main__":
    main()