import read_happy
import numpy as np
from matplotlib import pyplot as plt


def norml_eighs(edge_weights, member_to_party):
    index_to_member = {}
    member_to_index = {}
    for i, m in enumerate(member_to_party):
        index_to_member[i] = m
        member_to_index[m] = i

    # Make adjacency matrix
    A = np.zeros((len(index_to_member), len(index_to_member)))
    for m1, m2 in edge_weights:
        i, j = member_to_index[m1], member_to_index[m2]
        A[i][j] = edge_weights[(m1, m2)]

    D = np.diag(np.sum(A, axis=1))
    invD = np.diag(np.sum(A, axis=1) ** -1)
    L = D - A
    normL = np.dot(np.sqrt(invD), np.dot(L, np.sqrt(invD)))
    w, V = np.linalg.eigh(normL)
    return w


def lambda_distance(eighs1, eighs2):
    NUM_EIGHS = 50
    eighs1, eighs2 = eighs1[:NUM_EIGHS], eighs2[:NUM_EIGHS]
    return np.linalg.norm(eighs1 - eighs2)


def main():
    # member_to_party, edge_weights_by_i, edge_weights_total
    info = [read_happy.read_wcg("senate", session) for session in range(93, 115)]
    eigenvalues = [norml_eighs(info[i][1], info[i][0]) for i in range(len(info))]
    current_session = eigenvalues[-1]
    historical_sessions = eigenvalues[:-1]
    for session in historical_sessions:
        print lambda_distance(current_session, session)

    # member_to_party, edge_weights_by_i, edge_weights_total
    info = [read_happy.read_wvg("senate", session) for session in range(101, 116)]
    eigenvalues = [norml_eighs(info[i][1], info[i][0]) for i in range(len(info))]
    current_session = eigenvalues[-1]
    historical_sessions = eigenvalues[:-1]
    for session in historical_sessions:
        print lambda_distance(current_session, session)


if __name__ == '__main__':
    main()
