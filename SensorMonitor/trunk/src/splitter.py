'''
Splits a readings file per mote.
'''
import sys, os
from SharedLibs.tools import open_file, parse_line


def main(args):    
    if len(args) < 2:
        print "Usage: python %s {input filename}" % (args[0])
        return
    
    input_path = args[1]
    input_filename = os.path.basename(input_path)
    
    """
    Create folder based on the filename 
    """
    dot_index = input_filename.find(".")
    if dot_index < 0:
        dot_index = len(input_filename)
    
    dir_path = os.path.join(os.path.dirname(input_path), input_filename[:dot_index])
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)
    
    output_files = {} # dict that maps mote_ids into files
    
    input_file = open_file(input_path, "r")
    try:
        for line in input_file:
            timestamp, mote_id, counter, value = parse_line(line)  #@UnusedVariable
            if not mote_id:
                print "Mote id is missing!"
                exit()
            
            mote_file = output_files.get(mote_id, None)
            if mote_file is None:
                mote_filename = "%s/mote_%s.txt" % (dir_path, mote_id)
                mote_file = open(mote_filename, "w")
                output_files[mote_id] = mote_file
            
            mote_file.write(line)
    finally:
        if input_file:
            input_file.close()
        for f in output_files.values():
            f.close()
    
if __name__ == "__main__":    
    main(sys.argv)