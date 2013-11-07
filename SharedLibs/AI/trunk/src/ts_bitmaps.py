'''
Created on Aug 27, 2012

@author: Giulio
'''
import sys
import struct
import pprint
from sax import SAX
from collections import Counter, OrderedDict
from PIL import Image




SMALL_VALUE = 0.00001

def chunk_read(input_filename, chunk_size=1024 * 1024):    
    with open(input_filename, "rb") as f:
        while True:
            chunk = f.read(chunk_size)
            if chunk:
                for b in chunk:
                    yield struct.unpack("B", b)[0]
            else:
                f.close()
                break


def slidingWindow(sequence, winSize, step=1):
    """Returns a generator that will iterate through
    the defined chunks of input sequence.  Input sequence
    must be iterable."""    
    # Pre-compute number of chunks to emit
    numOfChunks = ((len(sequence)-winSize)/step) + 1

    # Do the work
    for i in range(0, numOfChunks * step, step):
        yield sequence[i:i+winSize]


def count_subseqs(words, size):
    counter = Counter()
    for w in words:
        subwords = slidingWindow(w, size, step=1)        
        for sub in subwords:            
            counter[sub] += 1
    return counter


def gen_subwords(level, alphabet):
    if level == 1:
        for l in alphabet:
            yield l
    else: 
        for l1 in alphabet:
            for l2 in gen_subwords(level - 1, alphabet):  
                yield l1 + l2
        
        
def dict2bitmap(d, level=2, mag=30):
    length = level ** 2    
    real_size = (length * mag, length * mag)
    img = Image.new("RGB", size=real_size)
    count = 0        
    for subseq in gen_subwords(level, "abcd"):
        for i in xrange(mag ** 2):
            coords = (i % mag + count % real_size[0], i / mag + (count / real_size[1]) * mag)            
            img.putpixel(coords, d.get(subseq, 0))
        count += mag
    #img.show()


def dict2colors(d):
    pprint.pprint(d)
    max_val = max(d.values())
    min_val = min(d.values())    
    for k in d.keys():
        v = int(float(d[k] - min_val)/(max_val - min_val) * 255)        
        d[k] = (v, 0, 255 - v)        


class TimeseriesBitmap(object):
    def __init__(self, alphabet, level, window_size=1):
        self.level = level
        self.window_size = window_size
        self.frequencies = OrderedDict()
        self.alphabet = alphabet
        for subword in gen_subwords(level, self.alphabet):            
            self.frequencies[subword] = 0        
        self.word_buffer = []
        self.subword_count = self.level ** len(self.alphabet)
            
    def calc_freqs(self, data_buffer):
        '''
        @deprecated: update now does the calculations
        '''
        self.frequencies = OrderedDict()
        word_len = self.level
        for word in data_buffer:
            for subword in slidingWindow(word, winSize=word_len, step=1):
                self.frequencies[subword] += 1
        
    def update(self, word):
        self.word_buffer.append(word)
        word_len = self.level
        if len(self.word_buffer) > self.window_size:
            last_word = self.word_buffer.pop(0)
            for subword in slidingWindow(last_word, winSize=word_len, step=1):
                self.frequencies[subword] -= 1
        for subword in slidingWindow(word, winSize=word_len, step=1):
            self.frequencies[subword] += 1
            
    
    def getAnomalyScore(self, a_bitmap):
        '''
        Get the anomaly score by normalizing both frequencies and then
        calculating the Euclidian distance.
        '''
        if len(self.word_buffer) < self.window_size or len(a_bitmap.word_buffer) < a_bitmap.window_size:
            return 0.0
        
        score = 0.0
        max_self_freq = float(max(max(self.frequencies.itervalues()), 1))
        max_bitmap_freq = float(max(max(a_bitmap.frequencies.itervalues()), 1))
        for freq, bitmap_freq in zip(self.frequencies.itervalues(), a_bitmap.frequencies.itervalues()):            
            score += (freq / max_self_freq - bitmap_freq / max_bitmap_freq) ** 2
                    
        return score / self.subword_count
    

def main(args):
    if len(args) < 2:
        print "Usage: python %s {filename}" % (args[0])
        exit()    
    
    filename = args[1]
        
    print "Reading..."
    data = []
    with open(filename) as f:
        for line in f:
            data.append(float(line.split()[1]))
    print "Read %d lines." % (len(data))
    
    
    print "Converting to SAX..."
    sax = SAX()
    N = 1600 # size of the sliding window
    n = 400 # size of a symbol
    lag_window = 8
    lead_window = 4
    bitmap_level = 2
    alphabet = "abcd"
    chunks = slidingWindow(data, N, step=n)
    words = []
    for chunk in chunks:
        word = sax.convert(chunk, alphabet, n)
        words.append(word)
    
    print "Anomaly detection..."
    with open("bitmap_anomaly.txt", "w") as out:        
        bitmap1 = TimeseriesBitmap(alphabet, bitmap_level, lag_window)
        bitmap2 = TimeseriesBitmap(alphabet, bitmap_level, lead_window)        
        
        for i in xrange(len(words) - (lag_window + lead_window)):
            bitmap1.update(words[i])
            bitmap2.update(words[i + lag_window])            
            if i >= lag_window:
                score = bitmap1.getAnomalyScore(bitmap2)
            else:
                score = 0.0
            
            for _ in xrange(n):    
                out.write("%s\n" % score)
            
if __name__ == '__main__':
    main(sys.argv)
    #main(["ts", r"D:\Giulio\My Dropbox\Projeto Sensores\experiments\temperatura\sala_servidores\hidden_vars.txt"])
    