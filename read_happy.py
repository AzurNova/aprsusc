import snap
import numpy as np

# Read: weighted cosponsorship graph
# wcg = PUNGraph
# wcg_edge_weights_senate_115.npy
# dict for info: (id, id) => weight
def read_wcg(chamber, session):
    folder = 'zhangi'
    edge_weights_i_name = '%s/happy_wcg_%s_%s_weights_by_i.npy' % (folder, chamber, session)
    edge_weights_t_name = '%s/happy_wcg_%s_%s_weights_total.npy' % (folder, chamber, session)
    party_name = '%s/happy_wcg_%s_%s_party.npy' % (folder, chamber, session)

    member_to_party = np.load(party_name).item()
    edge_weights_by_i = np.load(edge_weights_i_name).item()
    edge_weights_total = np.load(edge_weights_t_name).item()

    return member_to_party, edge_weights_by_i, edge_weights_total