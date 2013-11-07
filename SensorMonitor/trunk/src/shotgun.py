from random import choice
#---I have to make some tests, and possibly, some corrections.

def take_timestamp(line):
    try:
        return float(line.split()[0])
    except ValueError:
        exit(1)
    except IndexError:
        exit(1)

def shotgun(f_input, size, function, period):
    line = f_input.readline()
    samples = [line]
    
    if not line:
        return
    while abs(take_timestamp(samples[len(samples)-1]) - take_timestamp(samples[0])) < period*size and line:
        line = f_input.readline()
        samples.append(line)
    
    if abs(take_timestamp(samples[len(samples)-1]) - take_timestamp(samples[0])) >= (period-1)*size:
        pos = choice(range(len(samples)))
        for number in range(pos):
            function(samples[number])
        samples = samples[pos:]
        for number in range(len(samples)):
            if not(abs(take_timestamp(samples[number]) - take_timestamp(samples[0])) < size):
                function(samples[number])

    samples = [ samples[len(samples)-1] ]
    samples *= 2

    while samples[1] and abs(take_timestamp(samples[len(samples)-1]) - take_timestamp(samples[0])) < size:
        samples[1] = f_input.readline()
     
    shotgun(f_input, size, function, period)

if __name__ == '__main__':
    from sys import argv, stdin, stdout
    if len(argv) < 2:
        print '''Usage: python %s {size of holes as minutes} [period]
        @param period is a multiplicative factor to size, we take a interval
        bigger as period*size and chose a random point to fire'''
        exit(1)
    size = 60
    try:
        size = float(argv[1])
    except ValueError:
        print '''Enter a valid size.'''
    period = 3
    if len(argv) > 2:
        try:
            period = float(argv[2])
        except ValueError:
            pass
  
    shotgun(stdin, size*60, stdout.write, period)
