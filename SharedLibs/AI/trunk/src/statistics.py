'''
Created on Mar 22, 2013

@author: giulio
'''
import sys
import math
import pprint


def main(args):
    target_functions = ["x**2", "abs(x)"]
    
    filename = 'errors.txt'
    results = []
    line_count = 0
    
    with open(filename) as f:
        for line in f:
            line = line.strip()
            if line:
                line_count += 1
                result = []
                tokens = line.split()
                for x in tokens:
                    x = float(x)
                    result.append([eval(func) for func in target_functions])
                results.append(result)
    
    # AVERAGES
    # Format: [<func1, func2, ...>, <func1, func2, ...>, ...]
    averages = [[0.0] * len(target_functions) for _i in xrange(len(results[0]))]
    for result in results:
        for i in xrange(len(results[0])):
            for j in xrange(len(target_functions)):
                averages[i][j] += result[i][j]
    
    for i in xrange(len(averages)):
        for j in xrange(len(averages[0])):
            averages[i][j] /= line_count
        
    print "\n".join("\t".join("%.06f" % avg for avg in average) for average in averages)
    print "MAX:"
    print "\t".join("%.06f" % max(average[i] for average in averages[1:]) for i in xrange(len(target_functions)))
    
if __name__ == '__main__':
    main(sys.argv)