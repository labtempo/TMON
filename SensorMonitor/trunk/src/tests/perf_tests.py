'''
Created on Aug 16, 2012

@author: Giulio
'''
import cProfile, pstats
import plot

def file_exists(filename):
    fp = None
    try:
        fp = open(filename)
    except IOError:
        pass
    finally:
        if fp:
            fp.close()
            return True
    return False


def plot_benchmark(output_filename, reset=False):
    if reset or not file_exists(output_filename):    
        args = (r"'D:\Giulio\workspace2\SensorMonitor\src\plot.py'", \
                '"D:/Giulio/My Dropbox/Projeto Sensores/experiments/temperatura/sala_servidores/readings_02_05_12_18h06m45s.arff"', \
                "'-h'", r"'D:\Giulio\Downloads\highlights.txt'", "'-bench'")
        cProfile.run("plot.main([%s])" % (",".join(args)), output_filename)
    
    p = pstats.Stats(output_filename)
    p.sort_stats('time').print_stats(20)
    
    
def main():
    plot_benchmark("plot_bench", reset=True)

if __name__ == '__main__':
    main()