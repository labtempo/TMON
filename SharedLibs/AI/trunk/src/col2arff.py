'''
Script that takes a column-based readings file and transforms it into an arff 
file (Weka) while filling time gaps.

A column-based file has no header and separates data with spaces. For instance:

filename.txt contents:

1335303937.198361 172 23.198930
1335303942.198133 171 23.295180
1335303942.198133 172 23.198930

The arff-equivalent would be:

@relation database
@attribute timestamp numeric
@attribute mote_171
@attribute mote_172

@data
1335303937.198361,23.295180,23.198930
'''
import sys, os
from SharedLibs.tracetools import TraceReader, TraceWriter, TraceAdapter, UNIFORM_FILE_FORMAT, RAW_FILE_FORMAT, TEMP


def get_output_filename(input_filename, ext=".arff"):
    fname_noext = os.path.basename(input_filename).split(".")[0]    
    return os.path.join(os.path.dirname(input_filename), fname_noext + ext)


def main(args):
    if len(args) < 2:
        print "Usage: python %s {input_filename} [-compress {factor}] [-i motes_to_ignore]" % args[0]
        exit()
        
    filename = args[1]
    motes_to_ignore = [int(m) for m in args[args.index('-i') + 1:]] if '-i' in args else []
    compression_factor = int(args[args.index('-compress') + 1]) if '-compress' in args else 0
    
    tracereader = TraceReader(filename, supress_repetitions=False, auto_timestamps=False, \
                              auto_interpolation=False, motes_to_ignore=motes_to_ignore)    
    
    print "Pre-processing..."
    if filename.endswith("agg"):
        t_adapter = TraceAdapter(tracereader, RAW_FILE_FORMAT, TEMP)
        outname = get_output_filename(filename, ".txt")
    else:
        t_adapter = TraceAdapter(tracereader, UNIFORM_FILE_FORMAT)
        outname = get_output_filename(filename)
    tracewriter = TraceWriter(outname, arff_attributes=t_adapter.arff_attributes)
       
    
    print "Processing..."
    try:
        if compression_factor == 0:
            for data in t_adapter.parse():
                tracewriter.write(data)
        else:
            #acc = dict.fromkeys(tracereader.arff_attributes, 0.0)
            acc = None
            count = 0
            for data in t_adapter.parse():                
                if count % compression_factor == 0:
                    if acc:
                        # Calculate mean
                        for k, v in acc.iteritems():
                            acc[k] /= compression_factor
                        tracewriter.write(acc)
                    acc = data.copy()
                else:          
                    for k, v in data.iteritems():
                        acc[k] += v
                
                count += 1
    finally:
        tracereader.close()
        tracewriter.close()
        
    print "Done."

if __name__ == "__main__":
    main(sys.argv)