from __future__ import division
from itertools import combinations
import numpy as np
import requests as rq
from scipy.special import comb
import snap
from tqdm import tqdm


api_header = {'X-API-Key': 'ZKlkAenQo92aERecb4aTw9FECVeGIoa9je5PBiC3'}

# Retrieves congress members from API
def get_congress_members(chamber, session):
    assert chamber == 'house' or chamber == 'senate', "Chamber must be house or senate."
    assert type(session) is int and 0 < session <= 115, "Must be valid Congress session."
    r = rq.get('https://api.propublica.org/congress/v1/%s/%s/members.json' % (session, chamber), headers=api_header)
    assert r.json()['status'] == 'OK', "Request failed."
    members = []
    for member in r.json()['results'][0]['members']:
        members.append({'name': concat_name(member), 'id': member['id'], 'party': member['party']})
    return members


# Helper method
def concat_name(member):
    middle_name = ' ' + member['middle_name'] + ' ' if member['middle_name'] is not None else ' '
    return member['first_name'] + middle_name + member['last_name']


def get_cosponsorship_data(id1, id2, chamber, session):
    assert chamber == 'house' or chamber == 'senate', "Chamber must be house or senate."
    assert type(session) is int and 0 < session <= 115, "Must be valid Congress session."
    r = rq.get('https://api.propublica.org/congress/v1/members/%s/bills/%s/%s/%s.json' % (id1, id2, session, chamber),
               headers=api_header)
    while r.json()['status'] != 'OK':
        print 'Request failed for ids: %s, %s, trying again.' % (id1, id2)
        r = rq.get(
            'https://api.propublica.org/congress/v1/members/%s/bills/%s/%s/%s.json' % (id1, id2, session, chamber),
            headers=api_header)
    return r.json()


def get_cosponsorship(id1, id2, chamber, session):
    data = get_cosponsorship_data(id1, id2, chamber, session)
    bills = []
    for bill in data['results'][0]['bills']:
        bills.append({'number': bill['number'], 'title': bill['title']})
    return bills


def create_bipartite_consponsorship_graph(chamber, session):
    g = snap.TUNGraph.New()
    node_info = {}
    id_to_nid = {}
    created_nodes = set()
    m = get_congress_members(chamber, session)
    for m1, m2 in tqdm(combinations(m, 2), desc='member pairs', total=comb(len(m), 2)):
        if m1['id'] not in created_nodes:
            nid = g.GetMxNId()
            node_info[nid] = {'type': 'member', 'info': m1}
            id_to_nid[m1['id']] = nid
            created_nodes.add(m1['id'])
            g.AddNode(nid)
        if m2['id'] not in created_nodes:
            nid = g.GetMxNId()
            node_info[nid] = {'type': 'member', 'info': m2}
            id_to_nid[m2['id']] = nid
            created_nodes.add(m2['id'])
            g.AddNode(nid)
        bills = get_cosponsorship(m1['id'], m2['id'], chamber, session)
        for bill in bills:
            if bill['number'] not in created_nodes:
                nid = g.GetMxNId()
                node_info[nid] = {'type': 'bill', 'info': bill}
                id_to_nid[bill['number']] = nid
                created_nodes.add(bill['number'])
                g.AddNode(nid)
            g.AddEdge(id_to_nid[m1['id']], id_to_nid[bill['number']])
            g.AddEdge(id_to_nid[m2['id']], id_to_nid[bill['number']])
    snap.SaveEdgeList(g, 'bcg_%s_%s.graph' % (chamber, session))
    np.save('bcg_node_info_%s_%s.npy' % (chamber, session), node_info)
    np.save('bcg_id_to_nid_%s_%s.npy' % (chamber, session), id_to_nid)
    print g.GetNodes()
    print g.GetEdges()


def read_bcg(chamber, session):
    edge_list_name = 'bcg_%s_%s.graph' % (chamber, session)
    node_info_name = 'bcg_node_info_%s_%s.npy' % (chamber, session)
    id_to_nid_name = 'bcg_id_to_nid_%s_%s.npy' % (chamber, session)
    return snap.LoadEdgeList(snap.PUNGraph, edge_list_name, 0, 1), \
           np.load(node_info_name).item(), \
           np.load(id_to_nid_name).item()


def create_weighted_graph(chamber, session):
    g, node_info, id_to_nid = read_bcg(chamber, session)
    edge_weights = {}
    wg = snap.TUNGraph.New()
    for node in node_info:
        if node_info[node]['type'] == 'bill':
            continue
        if not wg.IsNode(node):
            wg.AddNode(node)
        connected = snap.TIntV()
        snap.GetNodesAtHop(g, node, 2, connected, False)
        bills = snap.TIntV()
        snap.GetNodesAtHop(g, node, 1, bills, False)
        for node2 in tqdm(connected, total=len(connected)):
            if node == node2:
                continue
            if not wg.IsNode(node2):
                wg.AddNode(node2)
                bills2 = snap.TIntV()
                snap.GetNodesAtHop(g, node2, 1, bills2, False)
                data = get_cosponsorship_data(node_info[node]['info']['id'], node_info[node2]['info']['id'], chamber, session)
                common_bills = int(data['results'][0]['common_bills'])
                edge_weights[(node, node2)] = common_bills / len(bills)
                edge_weights[(node2, node)] = common_bills / len(bills2)
            wg.AddEdge(node, node2)
    snap.SaveEdgeList(wg, 'wcg_%s_%s.graph' % (chamber, session))
    np.save('wcg_edge_weights_%s_%s.npy' % (chamber, session), edge_weights)
    print wg.GetNodes()
    print wg.GetEdges()


def main():
    chamber = 'senate'
    session = 115
    # create_bipartite_consponsorship_graph(chamber, session)
    create_weighted_graph(chamber, session)


if __name__ == '__main__':
    main()
