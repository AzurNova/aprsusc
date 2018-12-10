import numpy as np
import json
import os


def processes_data(chamber, session):
    member_to_party = {} # id => party
    bill_to_id = {} # bill number => bill id
    name_to_id = {} # name => id
    member_to_bills = {} # id => {'Y': set of bills, 'N': set of bills, 'A': set of bills}

    new_bill, new_member = 1000, 0

    bill_filenames = []
    for year in os.listdir('raw_senate_vote_data/data/%s/votes' % session):
        for bill in os.listdir('raw_senate_vote_data/data/%s/votes/%s' % (session, year)):
            bill_filenames.append('raw_senate_vote_data/data/%s/votes/%s/%s/data.json' % (session, year, bill))

    bad_bill_count = 0
    for filename in bill_filenames:
        datafile = open(filename)
        data = json.load(datafile)
        try:
            votes = [(member, 'Y') for member in data['votes']['Yea']] + \
                    [(member, 'N') for member in data['votes']['Nay']] + \
                    [(member, 'A') for member in data['votes']['Not Voting'] + data['votes']['Present']]
            billname = '-'.join(
                [data['date'].split('-')[0], str(data['congress']), data['chamber'] + str(data['number'])])
            bill_to_id[billname] = new_bill
            new_bill += 1
        except KeyError:
            bad_bill_count += 1
            continue
        for member, vote in votes:
            if member == 'VP':
                continue
            name = member['first_name'] + ' ' + member['last_name']
            if name not in name_to_id:
                id = new_member
                new_member += 1
                name_to_id[name] = id
                if member['party'] != 'D' and member['party'] != 'R':
                    member_to_party[id] = 'I'
                else:
                    member_to_party[id] = member['party']
            member = name_to_id[name]

            if member not in member_to_bills:
                member_to_bills[member] = {'Y': set(), 'N': set(), 'A': set()}
            member_to_bills[member][vote].add(bill_to_id[billname])
    # print member_to_party, member_to_bills
    print 'bad bills: %s' % bad_bill_count
    total_bills = len(bill_to_id)
    return member_to_party, member_to_bills, total_bills


def process(chamber, session):
    print chamber, session
    weights_total = {}
    weights_by_i = {}
    member_to_party, member_to_bills, total_bills = processes_data(chamber, session)

    for i in member_to_party:
        for j in member_to_party:
            if i == j:
                continue
            i_bills, j_bills = member_to_bills[i], member_to_bills[j]
            shared_bills = (i_bills['Y'] & j_bills['Y']) | (i_bills['N'] & j_bills['N'])
            weights_by_i[i, j] = 0 if len(i_bills['Y']) + len(i_bills['N']) == 0 else float(len(shared_bills)) / (len(i_bills['Y']) + len(i_bills['N']))
            weights_total[i, j] = float(len(shared_bills)) / total_bills
            # print weights_by_i[i, j], weights_total[i, j]

    np.save('zhangi/happy_vote_wcg_%s_%s_weights_total' % (chamber, session), weights_total)
    np.save('zhangi/happy_vote_wcg_%s_%s_weights_by_i' % (chamber, session), weights_by_i)
    np.save('zhangi/happy_vote_wcg_%s_%s_party' % (chamber, session), member_to_party)


def main():
    #101 => 115
    for session in range(101, 116):
        process('senate', session)


if __name__ == "__main__":
    main()
