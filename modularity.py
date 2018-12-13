import read_happy
import numpy as np
import matplotlib.pyplot as plt
import os.path

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
    # print W
    # print len(edge_weights)
    # print len(member_to_party)
    # print len([m for m in member_to_party if member_to_party[m] == "D"])
    # print len([m for m in member_to_party if member_to_party[m] == "R"])

    Q = 0.
    for i, j in edge_weights:
        if member_to_party[i] != member_to_party[j]:
            continue
        Aij = edge_weights[i, j]
        dio, dji = odeg[i], ideg[j]
        Q += Aij - dio*dji/W
    Q /= W
    # print Q
    return Q

def flip_party(member_to_party, m):
    new_mtp = {m: member_to_party[m] for m in member_to_party}
    new_mtp[m] = "D" if member_to_party[m] == "R" else "R"
    return new_mtp

def gen_dqs(type, chamber, session):
    filename = 'processed_data/modularities/%s_%s_%s_dQ' % (type, chamber, session)
    # if os.path.isfile(filename+'.npy'):
    #     dQ_d, dQ_r = np.load(filename+'.npy')
    #     return dQ_d, dQ_r
    if type == "wcg":
        member_to_party, edge_weights_by_i, edge_weights_total = read_happy.read_wcg(chamber, session)
    else:
        member_to_party, edge_weights_by_i, edge_weights_total = read_happy.read_wvg(chamber, session)
    Q = wcg_modularity(edge_weights_by_i, member_to_party)
    # Qp = random_modularity(edge_weights_by_i, member_to_party)
    # print type, chamber, session, Q, Qp
    dQ_d, dQ_r = [], []
    for m in member_to_party:
        Qp = wcg_modularity(edge_weights_by_i, flip_party(member_to_party, m))
        if member_to_party[m] == "D":
            dQ_d.append(-(Q-Qp))
        elif member_to_party[m] == "R":
            dQ_r.append(Q-Qp)
    np.save(filename, [dQ_d, dQ_r])
    return dQ_d, dQ_r

def dq_plot(type, chamber, sessions, options):
    bins, xlim = options["bins"], options["xlim"]
    if "xticks" in options:
        xticks, xlabels = options["xticks"], options["xlabels"]
    xlabel = options["xlabel"]
    fig, axes = plt.subplots(len(sessions), 1, sharex=True, sharey=True, figsize=(5,10))
    medians = []
    for i, session in enumerate(sessions[::-1]):
        dQ_d, dQ_r = gen_dqs(type, chamber, session)
        ax = axes[i]
        ax.hist(dQ_d, bins, facecolor=(0,0,1,0.5), edgecolor=(0,0,0,1), linewidth=0.75, label="Democrat")
        ax.hist(dQ_r, bins, facecolor=(1,0,0,0.5), edgecolor=(0,0,0,1), linewidth=0.75, label="Republican")
        ax.tick_params(axis='y', left=False, labelleft=False, labelright=False)
        ax.axvline(0, color='k', linestyle='dashed', linewidth=1)
        ax.axvline(np.percentile(dQ_d, 25), color=(0,0,1,0.4), linewidth=1)
        d_median = np.median(dQ_d)
        ax.axvline(d_median, color=(0,0,1,0.8), linewidth=1.5)
        ax.axvline(np.percentile(dQ_d, 75), color=(0,0,1,0.4), linewidth=1)
        ax.axvline(np.percentile(dQ_r, 25), color=(1,0,0,0.4), linewidth=1)
        r_median = np.median(dQ_r)
        ax.axvline(r_median, color=(1,0,0,0.8), linewidth=1.5)
        ax.axvline(np.percentile(dQ_r, 75), color=(1,0,0,0.4), linewidth=1)
        ax.axvline(np.median(dQ_d+dQ_r), color=(0,1,0,0.8), linewidth=1.5, label="Majority Cutoff = $median(R\cup{D})$")
        ax.set_ylabel("$%s^\mathregular{th}$" % session, fontsize=8, rotation=0, labelpad=12)
        medians.append((d_median, r_median))
    for i, ax in enumerate(axes):
        bot, top = ax.get_ylim()
        y = 0.2*bot+0.8*top
        ax.plot(medians[i], [y]*2, color=(1,0.6,0,0.9), linewidth=1.5, label="Polarity = $median(R)-median(D)$")
    if "xticks" in options:
        plt.xticks(xticks, xlabels)
    ax.set_xlabel(xlabel)
    ax.set_xlim(xlim)
    fig.figsize = (5,10)
    plt.legend(bbox_to_anchor=(0, 26.5), loc="lower left")
    # plt.savefig("graph/modularity/%s_%s_1_raw.png" % (type, chamber), dpi=1000)
    plt.show()

def random_modularity(edge_weights, member_to_party):
    mean = sum(edge_weights.values())
    nweights = len(edge_weights)
    mems = len(member_to_party)
    dems = len([m for m in member_to_party if member_to_party[m] == "D"])
    reps = len([m for m in member_to_party if member_to_party[m] == "R"])
    print mean, nweights, mems, dems, reps

    mean = 2647.44899866/9900
    edge_weights = {}
    for i in range(100):
        for j in range(100):
            if i == j:
                continue
            weight = np.random.normal(mean, 0.05)
            edge_weights[i,j] = weight

    member_to_party = {d:"D" for d in range(0,46)}
    member_to_party.update({r:"R" for r in range(46,100)})
    return wcg_modularity(edge_weights, member_to_party)

def main():
    # 2647.44899866
    # 9900
    # 100
    # 46
    # 54

    sessions = range(93, 115)
    options = {"bins": np.linspace(-0.01, 0.01, 51),
               "xlim": (-0.01, 0.01),
               "xticks": [-0.01, -0.008, -0.006, -0.004, -0.002, 0, 0.002, 0.004, 0.006, 0.008, 0.01],
               "xlabels": [10,8,6,4,2,0,2,4,6,8,10],
               "xlabel": "$\mid{dQ}\mid\\times{10^{-3}}$"}
    dq_plot("wcg", "senate", sessions, options)
    options = {"bins": np.linspace(-0.0040, 0.0040, 41),
               "xlim": (-0.004, 0.004),
               "xticks": [-0.004, -0.003, -0.002, -0.001, 0, 0.001, 0.002, 0.003, 0.004],
               "xlabels": [4,3,2,1,0,1,2,3,4],
               "xlabel": "$\mid{dQ}\mid\\times{10^{-3}}$"}
    dq_plot("wcg", "house", sessions, options)
    sessions = range(101, 116)
    options = {"bins": np.linspace(-0.012, 0.012, 61),
               "xlim": (-0.012, 0.012),
               "xticks": [-0.012, -0.01, -0.008, -0.006, -0.004, -0.002, 0, 0.002, 0.004, 0.006, 0.008, 0.01, 0.012],
               "xlabels": [12, 10, 8, 6, 4, 2 ,0, 2, 4, 6, 8, 10, 12],
               "xlabel": "$\mid{dQ}\mid\\times{10^{-3}}$"}
    dq_plot("wvg", "senate", sessions, options)
    options = {"bins": np.linspace(-0.0025, 0.0025, 51),
               "xlim": (-0.0025, 0.0025),
               "xticks": [-0.0025, -0.002, -0.0015, -0.001, -0.0005, 0, 0.0005, 0.001, 0.0015, 0.002, 0.0025],
               "xlabels": [25, 20, 15, 10, 5, 0, 5, 10, 15, 20, 25],
               "xlabel": "$\mid{dQ}\mid\\times{10^{-4}}$"}
    dq_plot("wvg", "house", sessions, options)

if __name__ == "__main__":
    main()