'''
Script to merge a list of readings into one single file

example:
input: readings_26_04_12_18h43m41s.txt,readings_26_04_12_18h47m01s.txt
output: readings_26_04_12_18h43m41s_to_26_04_12_18h47m01s.txt
'''
import sys, os

from SharedLibs.tools import open_file

def get_timestamp(file_sample_tuple):
    return file_sample_tuple[1][0]


def parse_line(line):
    if not line: 
        return None
    tokens = line.split()
    if not tokens: 
        return None
    return [float(tokens[0])] + tokens[1:]


def main(args):
    if len(args) < 2:
        print "Usage: python %s {file1 file2 file3 ...}" % (args[0])
        exit()
    
    '''
    Sort is not the best way to go, since it doesn't account for
    month increments. Anyway, this can be easily corrected by renaming
    the output file after the merging process finishes.
    '''
    filename_list = list(set(args[1:]))
    filename_list.sort()
    
    if not filename_list:
        print "No filenames provided"
        exit()

    dir_index = filename_list[0].rfind(os.sep, 0, -1) # os.sep is the folder separator (e.g. "/")
    ext_index = filename_list[0].rfind('.', dir_index, -1)
    output_filename = "%s%s_to_%s.gz" % (filename_list[0][:dir_index+1], filename_list[0][dir_index+1:ext_index], filename_list[-1][dir_index+1:ext_index])
        
    files = []
    output_file = open_file(output_filename, "w")
    try:
        for filename in filename_list:
            files.append(open_file(filename))
        
        readings = []        
        '''
        Initialize readings vector
        '''
        for f in files:
            if file:
                parsed_line = parse_line(f.readline())
                if parsed_line:
                    readings.append((f, parsed_line))
        
        while len(readings) > 0:
            readings.sort(key=get_timestamp)
            earliest = readings[0]
            output_file.write("%f %s\n" % (earliest[1][0], " ".join(earliest[1][1:])))
                        
            parsed_line = parse_line(earliest[0].readline())
            if parsed_line and earliest[0]:                    
                readings[0] = (earliest[0], parsed_line)
            else:
                readings.pop(0)            
    finally:
        if output_file:
            output_file.close()
        if files:
            for f in files:
                if f:
                    f.close()
    

if __name__ == "__main__":
    main(sys.argv)