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
    try_url = 'https://api.propublica.org/congress/v1/members/%s/bills/%s/%s/%s.json' % (id1, id2, session, chamber)
    r = rq.get(try_url, headers=api_header)
    try:
        count = 0
        while r.json()['status'] != 'OK':
            count += 1
            if count > 3:
                tqdm.write('Request failed 3x for cosponsorship data, ids: %s, %s. %s' % (id1, id2, try_url))
                return None
            time.sleep(2)
            r = rq.get(try_url, headers=api_header)
    except ValueError:
        print 'ValueError: %s' % (try_url)
        return None
    return r.json()


def get_cosponsorship(id1, id2, chamber, session):
    data = get_cosponsorship_data(id1, id2, chamber, session)
    if data == None:
        return None
    bills = []
    for bill in data['results'][0]['bills']:
        bills.append({'number': bill['number'], 'title': bill['title']})
    return bills


def get_covote_data(id1, id2, chamber, session):
    assert chamber == 'house' or chamber == 'senate', "Chamber must be house or senate."
    assert type(session) is int and 0 < session <= 115, "Must be valid Congress session."
    try_url = 'https://api.propublica.org/congress/v1/members/%s/votes/%s/%s/%s.json' % (id1, id2, session, chamber)
    r = rq.get(try_url, headers=api_header)
    try:
        count = 0
        while r.json()['status'] != 'OK':
            count += 1
            if count > 3:
                tqdm.write('Request failed 3x for covote data, ids: %s, %s. %s' % (id1, id2, try_url))
                return None
            time.sleep(2)
            r = rq.get(try_url, headers=api_header)
    except ValueError:
        print 'ValueError: %s' % (try_url)
        return None
    return r.json()


def create_bipartite_consponsorship_graph(chamber, session):
    print("Creating bipartite cosponsorship graph (bcg)...")
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
        if bills is None:
            continue
        for bill in bills:
            if bill['number'] not in created_nodes:
                nid = g.GetMxNId()
                node_info[nid] = {'type': 'bill', 'info': bill}
                id_to_nid[bill['number']] = nid
                created_nodes.add(bill['number'])
                g.AddNode(nid)
            g.AddEdge(id_to_nid[m1['id']], id_to_nid[bill['number']])
            g.AddEdge(id_to_nid[m2['id']], id_to_nid[bill['number']])
    snap.SaveEdgeList(g, 'data/bcg_%s_%s.graph' % (chamber, session))
    np.save('data/bcg_node_info_%s_%s.npy' % (chamber, session), node_info)
    np.save('data/bcg_id_to_nid_%s_%s.npy' % (chamber, session), id_to_nid)
    print("Completed bipartite cosponsorship graph!")


def read_bcg(chamber, session):
    edge_list_name = 'data/bcg_%s_%s.graph' % (chamber, session)
    node_info_name = 'data/bcg_node_info_%s_%s.npy' % (chamber, session)
    id_to_nid_name = 'data/bcg_id_to_nid_%s_%s.npy' % (chamber, session)
    return snap.LoadEdgeList(snap.PUNGraph, edge_list_name, 0, 1), \
           np.load(node_info_name).item(), \
           np.load(id_to_nid_name).item()


def create_weighted_cosponsorship_graph(chamber, session):
    print("Creating weighted cosponsorship graph (wcg)...")
    g, node_info, id_to_nid = read_bcg(chamber, session)
    edge_weights = {}
    sponsored_bills = {}
    wcg = snap.TUNGraph.New()
    for node in tqdm(node_info, total=len(node_info), position=0):
        if node_info[node]['type'] == 'bill':
            continue
        if not wcg.IsNode(node):
            wcg.AddNode(node)
        connected = snap.TIntV()
        if not g.IsNode(node):
            print("FUCK WHY IS %s NOT A NODE" % (node,))
        snap.GetNodesAtHop(g, node, 2, connected, False)
        if node in sponsored_bills:
            num_bills = sponsored_bills[node]
        else:
            bills = snap.TIntV()
            snap.GetNodesAtHop(g, node, 1, bills, False)
            num_bills = len(bills)
            sponsored_bills[node] = num_bills
        for node2 in connected:
            if node == node2:
                continue
            if not wcg.IsNode(node2):
                wcg.AddNode(node2)
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
            wcg.AddEdge(node, node2)
    snap.SaveEdgeList(wcg, 'data/wcg_%s_%s.graph' % (chamber, session))
    np.save('data/wcg_edge_weights_%s_%s.npy' % (chamber, session), edge_weights)
    np.save('data/wcg_sponsored_bills_%s_%s.npy' % (chamber, session), sponsored_bills)
    print("Completed weighted cosponsorship graph!")

def create_weighted_vote_graph(chamber, session):
    print("Creating weighted vote graph (wcg)...")
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
        d = get_covote_data(m1['id'], m2['id'], chamber, session)
        if d is None:
            continue
        data = d['results'][0]
        key = tuple(sorted([data['first_member_id'], data['second_member_id']]))
        covote_data[key] = {'common_votes': data['common_votes'], 'disagree_votes': data['disagree_votes'],
                            'agree_percent': data['agree_percent'], 'disagree_percent': data['disagree_percent']}
        g.AddEdge(id_to_nid[m1['id']], id_to_nid[m2['id']])
        edge_weights[id_to_nid[m1['id']]][id_to_nid[m2['id']]] = float(data['agree_percent']) / 100
        edge_weights[id_to_nid[m2['id']]][id_to_nid[m1['id']]] = float(data['agree_percent']) / 100
    snap.SaveEdgeList(g, 'wvg_%s_%s.graph' % (chamber, session))
    np.save('data/wvg_node_info_%s_%s.npy' % (chamber, session), node_info)
    np.save('data/wvg_id_to_nid_%s_%s.npy' % (chamber, session), id_to_nid)
    np.save('data/wvg_edge_weights_%s_%s.npy' % (chamber, session), edge_weights)
    np.save('data/wvg_covote_data_%s_%s.npy' % (chamber, session), covote_data)
    print("Completed weighted vote graph!")

def main():
    chamber = 'senate'
    sessions = np.arange(111, 112, 1)
    for float_session in sessions:
        print "session: %s" % (float_session)
        session = int(float_session)
        create_bipartite_consponsorship_graph(chamber, session)
        create_weighted_cosponsorship_graph(chamber, session)
        create_weighted_vote_graph(chamber, session)


if __name__ == '__main__':
    main()
