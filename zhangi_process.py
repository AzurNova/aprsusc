import numpy as np
import csv


def processes_govtrack_data(chamber, session):
    party_bioguide = np.load('raw_data/party_bioguide.npy').item()
    party_thomas = np.load('raw_data/party_thomas.npy').item()

    member_to_party = {}# id => party
    bill_to_id = {} # bill number => bill id
    name_to_id = {} # name => id
    member_to_bills = {} # id => set of bills

    new_bill, new_member = 1000, 0
    with open('raw_data/govtrack_cosponsor_split/gcd_%s_%s.csv' % (session, chamber)) as data:
        reader = csv.reader(data, delimiter=',')
        first = True
        for row in reader:
            if first:
                first = False
                continue
            bill, name, thomas_id, bioguide_id = row[0:4]
            if bill not in bill_to_id:
                bill_to_id[bill] = new_bill
                new_bill += 1

            if name not in name_to_id:
                member = new_member
                new_member += 1
                name_to_id[name] = member
                if thomas_id != 'NA':
                    party = party_thomas[thomas_id]
                elif bioguide_id != 'NA':
                    party = party_bioguide[bioguide_id]
                else:
                    party = 'I'
                member_to_party[member] = party

            member = name_to_id[name]
            if member not in member_to_bills:
                member_to_bills[member] = set()
            member_to_bills[member].add(bill_to_id[bill])
    # print member_to_party, member_to_bills
    total_bills = len(bill_to_id)
    return member_to_party, member_to_bills, total_bills

def process(chamber, session):
    print chamber, session
    weights_total = {}
    weights_by_i = {}
    member_to_party, member_to_bills, total_bills = processes_govtrack_data(chamber, session)

    for i in member_to_party:
        for j in member_to_party:
            if i == j:
                continue
            i_bills, j_bills = member_to_bills[i], member_to_bills[j]
            shared_bills = i_bills & j_bills
            weights_by_i[i, j] = 0 if len(i_bills) == 0 else float(len(shared_bills)) / len(i_bills)
            weights_total[i, j] = float(len(shared_bills)) / total_bills
            # print weights_by_i[i, j], weights_total[i, j]

    np.save('zhangi/happy_wcg_%s_%s_weights_total' % (chamber, session), weights_total)
    np.save('zhangi/happy_wcg_%s_%s_weights_by_i' % (chamber, session), weights_by_i)
    np.save('zhangi/happy_wcg_%s_%s_party' % (chamber, session), member_to_party)

def main():
    #93 => 114
    for session in range(93, 115):
        process('senate', session)


if __name__ == "__main__":
    main()
