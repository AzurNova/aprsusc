import read_happy
import numpy as np
from matplotlib import pyplot as plt

def main2():
    member_to_party, edge_weights_by_i, edge_weights_total = read_happy.read_wvg("senate", 114)
    cohesion(edge_weights_total, member_to_party)
    member_to_party, edge_weights_by_i, edge_weights_total = read_happy.read_wvg("house", 114)
    cohesion(edge_weights_total, member_to_party)

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

def lighten(color):
    return tuple(map(lambda x: (x+1.)/2, color))

def plot_cosponsorship_cohesion(chamber, sessions):
    dints, dexts, dGs = {}, {}, {}
    for session in sessions:
        print("year %s" % session)
        member_to_party, edge_weights_by_i, edge_weights_total = read_happy.read_wcg(chamber, session)
        dints[session], dexts[session], dGs[session] = cohesion(edge_weights_by_i, member_to_party)
    dGs = [dGs[session] for session in sessions]
    # for party, color in [("D", "b"), ("R", "r")]: #, ("I", "g")]:
    plot_options = [("D", (0., 0., 1.), "$d_{int}(Democrat)$", "$d_{ext}(Democrat)$"),
                    ("R", (1., 0., 0.), "$d_{int}(Republican)$", "$d_{ext}(Republican)$")]
    fig, axes = plt.subplots(1, 2, figsize=(10.5,5))
    for i, (party, color, label1, label2) in enumerate(plot_options):
        ax = axes[i]
        x = [session for session in sessions if dints[session][party] > 0]
        dint = [dints[session][party] for session in sessions if dints[session][party] > 0]
        dext = [dexts[session][party] for session in sessions]
        ax.plot(x, dint, "-", color=color, label=label1)
        ax.plot(sessions, dext, "-", color=lighten(color), label=label2)
        ax.plot(sessions, dGs, "k--", label="$d(G)$")
        ax.set_xticks(np.arange(95, 116, 5))
        ax.set_yticks(np.arange(0, 0.6, 0.1))
        ax.set_xlim(92,116)
        ax.set_ylim((0, 0.45))
        # plt.yticks(np.arange(0, 0.3, 0.1)) # edge_weights_total
        # plt.ylim((0, 0.25)) # edge_weights_total
        ax.grid(color=(0.75, 0.75, 0.75), linestyle='--', linewidth=1)
        ax.legend()
        ax.set_xlabel("session")
    # fig.suptitle("senate party cosponsorship cohesion")
    plt.savefig("graph/cohesion/wcg_%s_raw.png" % chamber, dpi=1000)

def plot_voting_cohesion(chamber, sessions):
    dints, dexts, dGs = {}, {}, {}
    for session in sessions:
        print("year %s" % session)
        member_to_party, edge_weights_by_i, edge_weights_total = read_happy.read_wvg(chamber, session)
        dints[session], dexts[session], dGs[session] = cohesion(edge_weights_by_i, member_to_party)
    dGs = [dGs[session] for session in sessions]
    # for party, color in [("D", "b"), ("R", "r")]: #, ("I", "g")]:
    plot_options = [("D", (0., 0., 1.), "$d_{int}(Democrat)$", "$d_{ext}(Democrat)$"),
                    ("R", (1., 0., 0.), "$d_{int}(Republican)$", "$d_{ext}(Republican)$")]
    fig, axes = plt.subplots(1, 2, figsize=(10.5,5))
    for i, (party, color, label1, label2) in enumerate(plot_options):
        ax = axes[i]
        x = [session for session in sessions if dints[session][party] > 0]
        dint = [dints[session][party] for session in sessions if dints[session][party] > 0]
        dext = [dexts[session][party] for session in sessions]
        ax.plot(x, dint, "-", color=color, label=label1)
        ax.plot(sessions, dext, "-", color=lighten(color), label=label2)
        ax.plot(sessions, dGs, "k--", label="$d(G)$")
        ax.set_xticks(np.arange(100, 116, 5))
        ax.set_yticks(np.arange(0, 1.0, 0.1))
        ax.set_ylim((0.2, 0.95))
        ax.set_xlim((100, 116))
        # plt.yticks(np.arange(0, 0.3, 0.1)) # edge_weights_total
        # plt.ylim((0, 0.25)) # edge_weights_total
        ax.grid(color=(0.75, 0.75, 0.75), linestyle='--', linewidth=1)
        ax.legend()
        ax.set_xlabel("session")
    # fig.suptitle("senate party voting cohesion")
    # plt.savefig("graph/cohesion/wvg_%s_raw.png" % chamber, dpi=1000)
    plt.show()

def main():
    # main2()
    # plot_cosponsorship_cohesion("senate", range(93,115))
    # plot_cosponsorship_cohesion("house", range(93,115))
    plot_voting_cohesion("senate", range(101,116))
    plot_voting_cohesion("house", range(101,116))

if __name__ == "__main__":
    main()