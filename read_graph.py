import snap
import numpy as np

# .npy holds dicts of congressman
# id_to_nid is
#   <id> (congressman id) => graph nid of congressman
#   <id> (bill number) => graph nid of bill
# node_info is
#   <nid> => node info ({type: "member" OR "bill", info: <infodict>})
#       member <infodict> => keys: <name> <id> <party: String (r, d, or i)>
#       bill <infodict> => keys: <number = id> <title>


# Read: weighted cosponsorship graph
# wcg = PUNGraph
# wcg_edge_weights_senate_115.npy
# dict for info: (id, id) => weight
def read_wcg(chamber, session):
    edge_list_name = 'data/wcg_%s_%s.graph' % (chamber, session)
    node_info_name = 'data/bcg_node_info_%s_%s.npy' % (chamber, session)
    id_to_nid_name = 'data/bcg_id_to_nid_%s_%s.npy' % (chamber, session)
    edge_weights_name = 'data/wcg_edge_weights_%s_%s.npy' % (chamber, session)
    return snap.LoadEdgeList(snap.PUNGraph, edge_list_name, 0, 1), \
           (np.load(node_info_name).item(), \
           np.load(id_to_nid_name).item(), \
           np.load(edge_weights_name).item())