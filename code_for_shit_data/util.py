# Retrieves corresponding parties for each nid in 'nodes'
def get_parties(bcg_node_info, nodes):
    return [bcg_node_info[i]["info"]["party"] for i in nodes]

# Returns true if nids 'i' and 'j' are of the same party
def same_party(bcg_node_info, i, j):
    pi, pj = get_parties(bcg_node_info, [i, j])
    return pi == pj