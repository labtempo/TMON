'''
Created on Sep 15, 2012

@author: Giulio
'''
import cProfile, pstats
import ts_bitmaps

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
        args = (r"'D:\\Giulio\\workspace2\\AI\\src\\ts_bitmaps.py'", \
                r'"D:\\Giulio\\workspace2\\AI\\src\\tests\\test_hidden_vars.txt"')
        cProfile.run("ts_bitmaps.main([%s])" % (",".join(args)), output_filename)
    
    p = pstats.Stats(output_filename)
    p.sort_stats('time').print_stats(20)
    
    
def main():
    plot_benchmark("ts_bitmaps_bench", reset=True)

if __name__ == '__main__':
    main()