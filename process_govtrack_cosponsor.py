from __future__ import division
from __future__ import division
from collections import defaultdict
from itertools import combinations
import numpy as np
import requests as rq
from scipy.special import comb
import snap
import time
from tqdm import tqdm
import os
import csv


def split_govtrack_data():
    filenames = os.listdir('raw_data/govtrack_cosponsor_data')
    for filename in tqdm(filenames, total=len(filenames)):
        congress = filename.split('_')[3]
        stem = 'raw_data/govtrack_cosponsor_split'
        with \
                open('%s/gcd_%s_senate.csv' % (stem, congress), 'w') as senate, \
                open('%s/gcd_%s_house.csv' % (stem, congress), 'w') as house, \
                open('raw_data/govtrack_cosponsor_data/%s' % filename) as data:
            reader = csv.reader(data, delimiter=',')
            writer_senate = csv.writer(senate, delimiter=',')
            writer_house = csv.writer(house, delimiter=',')
            first = True
            for row in reader:
                if first:
                    writer_senate.writerow(row)
                    writer_house.writerow(row)
                    first = False
                else:
                    if row[0][0] == 's':
                        writer_senate.writerow(row)
                    if row[0][0] == 'h':
                        writer_house.writerow(row)


def generate_legisators_party_dicts():
    bioguide_to_party = {}
    thomas_to_party = {}
    file_pre = 'raw_data/govtrack_cosponsor_data/legislators'
    with open('%s-current.csv' % file_pre) as data1, open('%s-historical.csv' % file_pre) as data2:
        first = True
        for row in csv.reader(data1, delimiter=','):
            if first:
                first = False
                continue
            if row[12] == 'Republican':
                party = 'R'
            elif row[12] == 'Democrat':
                party = 'D'
            else:
                party = 'I'
            if row[23] != '':
                thomas_to_party[row[23]] = party
            if row[22] != '':
                bioguide_to_party[row[22]] = party
        first = True
        for row in csv.reader(data2, delimiter=','):
            if first:
                first = False
                continue
            if row[12] == 'Republican':
                party = 'R'
            elif row[12] == 'Democrat':
                party = 'D'
            else:
                party = 'I'
            if row[23] != '':
                thomas_to_party[row[23]] = party
            if row[22] != '':
                bioguide_to_party[row[22]] = party
    np.save('raw_data/party_thomas.npy', thomas_to_party)
    np.save('raw_data/party_bioguide.npy', bioguide_to_party)


def process_govtrack_data(chamber, session):
    party_bioguide = np.load('raw_data/party_bioguide.npy').item()
    party_thomas = np.load('raw_data/party_thomas.npy').item()
    m = []
    b = {}
    to_bills = defaultdict(list)
    bills = set()
    members = set()
    new_id = 0
    with open('raw_data/govtrack_cosponsor_split/gcd_%s_%s.csv' % (session, chamber)) as data:
        reader = csv.reader(data, delimiter=',')
        first = True
        for row in reader:
            print row
            if first:
                first = False
                continue
            if row[0] not in bills:
                bills.add(row[0])
                b[row[0]] = new_id
                new_id += 1
            if row[2] + row[3] not in members:
                members.add(row[2] + row[3])
                if row[3] != 'NA':
                    party = party_bioguide[row[3]]
                elif row[2] != 'NA':
                    party = party_thomas[row[2]]
                else:
                    party = 'I'
                data = {'id': new_id, 'name': row[1], 'party': party}
                m.append(data)
                to_bills[new_id].append(row[0])
                new_id += 1
    return m, b, to_bills
    # m = list of {id => id i dont give a fuck about, not node id
    #              name => name i dont give a fuck about
    #              party => "R", "D", "I"


def get_cosponsorship(m1, m2, to_bills):
    return list(set(to_bills[m1]) & set(to_bills[m2]))


def create_bipartite_consponsorship_graph(chamber, session):
    print("Creating bipartite cosponsorship graph (bcg)...")
    m, b, to_bills = process_govtrack_data(chamber, session)
    g = snap.TUNGraph.New()
    node_info = {}
    id_to_nid = {}
    created_nodes = set()
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
        bills = get_cosponsorship(m1['id'], m2['id'], to_bills)
        for bill in bills:
            if b[bill] not in created_nodes:
                nid = g.GetMxNId()
                node_info[nid] = {'type': 'bill', 'info': bill}
                id_to_nid[b[bill]] = nid
                created_nodes.add(b[bill])
                g.AddNode(nid)
            g.AddEdge(id_to_nid[m1['id']], id_to_nid[b[bill]])
            g.AddEdge(id_to_nid[m2['id']], id_to_nid[b[bill]])
    snap.SaveEdgeList(g, 'govtrack_data/bcg_%s_%s.graph' % (chamber, session))
    np.save('govtrack_data/bcg_node_info_%s_%s.npy' % (chamber, session), node_info)
    np.save('govtrack_data/bcg_id_to_nid_%s_%s.npy' % (chamber, session), id_to_nid)
    np.save('raw_data/govtrack_cosponsor_temp/m_%s_%s.npy' % (chamber, session), m)
    np.save('raw_data/govtrack_cosponsor_temp/b_%s_%s.npy' % (chamber, session), b)
    np.save('raw_data/govtrack_cosponsor_temp/to_bills_%s_%s.npy' % (chamber, session), to_bills)
    print("Completed bipartite cosponsorship graph!")


def make_zhangi_happy(chamber, session):
    weights_total = {}
    weights_by_i = {}
    party = {}
    m, b, to_bills = process_govtrack_data(chamber, session)
    print len(b)
    print len(to_bills)
    print to_bills
    for m1 in m:
        for m2 in m:
            if m1['id'] == m2['id']:
                continue
            shared_bills = get_cosponsorship(m1['id'], m2['id'], to_bills)
            weights_total[(m1['id'], m2['id'])] = float(len(shared_bills)) / len(b)
            if len(to_bills[m1['id']]) == 0:
                weights_by_i[(m1['id'], m2['id'])] = 0.
            else:
                weights_by_i[(m1['id'], m2['id'])] = float(len(shared_bills)) / len(to_bills[m1['id']])
            # if weights_by_i[(m1['id'], m2['id'])] == 1:
                # print shared_bills, to_bills[m1['id']]
        party[m1['id']] = m1['party']
    np.save('zhangi/happy_wcg_%s_%s_weights_total' % (chamber, session), weights_total)
    np.save('zhangi/happy_wcg_%s_%s_weights_by_i' % (chamber, session), weights_by_i)
    np.save('zhangi/happy_wcg_%s_%s_party' % (chamber, session), party)


def read_bcg(chamber, session):
    edge_list_name = 'govtrack_data/bcg_%s_%s.graph' % (chamber, session)
    node_info_name = 'govtrack_data/bcg_node_info_%s_%s.npy' % (chamber, session)
    id_to_nid_name = 'govtrack_data/bcg_id_to_nid_%s_%s.npy' % (chamber, session)
    return snap.LoadEdgeList(snap.PUNGraph, edge_list_name, 0, 1), \
           np.load(node_info_name).item(), \
           np.load(id_to_nid_name).item()


def create_weighted_cosponsorship_graph(chamber, session):
    print("Creating weighted cosponsorship graph (wcg)...")
    m = np.load('raw_data/govtrack_cosponsor_temp/m_%s_%s.npy' % (chamber, session))
    b = np.load('raw_data/govtrack_cosponsor_temp/b_%s_%s.npy' % (chamber, session)).item()
    to_bills = np.load('raw_data/govtrack_cosponsor_temp/to_bills_%s_%s.npy' % (chamber, session)).item()
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
            continue
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
            common_bills = len(get_cosponsorship(node_info[node]['info']['id'], node_info[node2]['info']['id'], to_bills))
            edge_weights[(node, node2)] = common_bills / len(to_bills[node_info[node]['info']['id']])
            edge_weights[(node2, node)] = common_bills / len(to_bills[node_info[node2]['info']['id']])
            wcg.AddEdge(node, node2)
    snap.SaveEdgeList(wcg, 'govtrack_data/wcg_%s_%s.graph' % (chamber, session))
    np.save('govtrack_data/wcg_edge_weights_%s_%s.npy' % (chamber, session), edge_weights)
    np.save('govtrack_data/wcg_sponsored_bills_%s_%s.npy' % (chamber, session), sponsored_bills)
    print("Completed weighted cosponsorship graph!")

def main():
    #split_govtrack_data()
    #generate_legisators_party_dicts()
    #create_bipartite_consponsorship_graph('senate', 114)
    #create_weighted_cosponsorship_graph('senate', 114)
    #93 => 114
    for session in range(114, 115):
        zhangi_makes_himself_happy('senate', session)


if __name__ == "__main__":
    main()
