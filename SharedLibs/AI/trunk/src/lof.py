'''
Created on Nov 27, 2012

@author: giulio
'''
import sys
import numpy
from SharedLibs import tracetools


def euclidian_dist(A, B):
    return numpy.linalg.norm(A-B)


def absolute_dist(A, B):
    return numpy.sum(numpy.abs(A-B))


def calc_distances(A, points, distance):
    dists = []
    for p in points:
        dists.append(distance(A, p))
            
    return dists


def k_dist(A, k, points, distance, dists):    
    dists = sorted(dists)
    return dists[k - 1]         


def reach_dist(A, B, points, k, distance, dists):
    k_dist_result = k_dist(B, k, points, distance, dists)    
    return max(distance(A, B), k_dist_result)


def neighborhood(A, points, k, distance, dists):
    dists = [e for e in enumerate(dists)]
    dists.sort(key=lambda item: item[1])
    
    k_dist = dists[k - 1][1]
    
    neighbors = [ points[dists[k - 1][0]] ]
    for i in xrange(k, len(dists)):
        if dists[i][1] == k_dist:
            neighbors.append(points[dists[i][0]])
        else:
            break
    
    return neighbors


def lrd(A, points, k, distance, dists=None, n_k=None):
    if not dists:
        dists = calc_distances(A, points, distance)
    if not n_k:
        n_k = neighborhood(A, points, k, distance, dists)    
    reachability_sum = sum(reach_dist(A, p, points, k, distance, dists) for p in n_k)
    return float(len(n_k)) / reachability_sum
        

def LOF(A, points, k, distance):
    dists = calc_distances(A, points, distance)
    n_k = neighborhood(A, points, k, distance, dists)    
    lrd_a = lrd(A, points, k, distance, dists=dists, n_k=n_k)    
    return sum(lrd(B, points, k, distance) for B in n_k) / (len(n_k) * lrd_a)


def main(args):
    filename = "/home/giulio/Dropbox/Projeto Sensores/experiments/temperatura/sala_servidores/readings_02_05_12_18h06m45s.arff"
    tr = tracetools.TraceReader(filename=filename, supress_repetitions=False)
    detected_anomaly = False    
    window_size = 20
    k = 15
    anomaly_threshold = 1.5
    timestamps = []
    mid = window_size / 2
    
    try:
        i = 0
        temp_data = []  
        for data in tr.parse():
            temps = [data[c] for c in data.iterkeys() if c != "timestamp"]
            temp_data.append(numpy.array(temps))
            timestamps.append(data["timestamp"])
            i += 1
            if i >= window_size:
                lof = LOF(temp_data[mid], temp_data, k, euclidian_dist)
                if not numpy.isnan(lof):
                    if detected_anomaly and lof < anomaly_threshold:
                        print "%f" % (timestamps[mid])
                        detected_anomaly = False
                    elif not detected_anomaly and lof > anomaly_threshold:
                        print "%f" % timestamps[mid],
                        detected_anomaly = True
                del temp_data[0]
                del timestamps[0]
    finally:
        tr.close()

if __name__ == '__main__':
    main(sys.argv)