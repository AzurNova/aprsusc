from __future__ import division
from collections import defaultdict
from itertools import combinations
import numpy as np
import requests as rq
from scipy.special import comb
import snap
import time
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
        time.sleep(1)
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


def get_covote_data(id1, id2, chamber, session):
    assert chamber == 'house' or chamber == 'senate', "Chamber must be house or senate."
    assert type(session) is int and 0 < session <= 115, "Must be valid Congress session."
    r = rq.get('https://api.propublica.org/congress/v1/members/%s/votes/%s/%s/%s.json % (id1, id2, chamber, session)',
               headers=api_header)
    while r.json()['status'] != 'OK':
        print 'Request failed for ids: %s, %s, trying again.' % (id1, id2)
        time.sleep(1)
        r = rq.get(
            'https://api.propublica.org/congress/v1/members/%s/votes/%s/%s/%s.json % (id1, id2, chamber, session)',
            headers=api_header)
    return r.json()


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
    sponsored_bills = {}
    wg = snap.TUNGraph.New()
    for node in node_info:
        if node_info[node]['type'] == 'bill':
            continue
        if not wg.IsNode(node):
            wg.AddNode(node)
        connected = snap.TIntV()
        snap.GetNodesAtHop(g, node, 2, connected, False)
        if node in sponsored_bills:
            num_bills = sponsored_bills[node]
        else:
            bills = snap.TIntV()
            snap.GetNodesAtHop(g, node, 1, bills, False)
            num_bills = len(bills)
            sponsored_bills[node] = num_bills
        for node2 in tqdm(connected, total=len(connected)):
            if node == node2:
                continue
            if not wg.IsNode(node2):
                wg.AddNode(node2)
            if node2 in sponsored_bills:
                num_bills2 = sponsored_bills[node2]
            else:
                bills2 = snap.TIntV()
                snap.GetNodesAtHop(g, node2, 1, bills2, False)
                num_bills2 = len(bills2)
                sponsored_bills[node2] = num_bills2
            data = get_cosponsorship_data(node_info[node]['info']['id'], node_info[node2]['info']['id'], chamber, session)
            common_bills = int(data['results'][0]['common_bills'])
            edge_weights[(node, node2)] = common_bills / num_bills
            edge_weights[(node2, node)] = common_bills / num_bills2
            wg.AddEdge(node, node2)
    snap.SaveEdgeList(wg, 'wcg_%s_%s.graph' % (chamber, session))
    np.save('wcg_edge_weights_%s_%s.npy' % (chamber, session), edge_weights)
    np.save('wcg_sponsored_bills_%s_%s.npy' % (chamber, session), sponsored_bills)
    print wg.GetNodes()
    print wg.GetEdges()


def create_weighted_vote_graph(chamber, session):
    g = snap.TUNGraph.New()
    node_info = {}
    id_to_nid = {}
    covote_data = {}
    edge_weights = defaultdict(dict)
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
        data = get_covote_data(m1['id'], m2['id'], chamber, session)['results'][0]
        key = tuple(sorted([data['first_member_id'], data['second_member_id']]))
        covote_data[key] = {'common_votes': data['common_votes'], 'disagree_votes': data['disagree_votes'],
                            'agree_percent': data['agree_percent'], 'disagree_percent': data['disagree_percent']}
        g.AddEdge(id_to_nid[m1['id'], id_to_nid[m2['id']]])
        edge_weights[id_to_nid[m1['id']][id_to_nid[m2['id']]]] = float(data['agree_percent']) / 100
        edge_weights[id_to_nid[m2['id']][id_to_nid[m1['id']]]] = float(data['agree_percent']) / 100
    snap.SaveEdgeList(g, 'wvg_%s_%s.graph' % (chamber, session))
    np.save('wvg_node_info_%s_%s.npy' % (chamber, session), node_info)
    np.save('wvg_id_to_nid_%s_%s.npy' % (chamber, session), id_to_nid)
    np.save('wvg_edge_weights_%s_%s.npy' % (chamber, session), edge_weights)
    np.save('wvg_covote_data_%s_%s.npy' % (chamber, session), covote_data)
    print g.GetNodes()
    print g.GetEdges()


def main():
    chamber = 'senate'
    session = 115
    # create_bipartite_consponsorship_graph(chamber, session)
    create_weighted_graph(chamber, session)


if __name__ == '__main__':
    main()
