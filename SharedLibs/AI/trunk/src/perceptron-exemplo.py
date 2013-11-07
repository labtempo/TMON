import math
import matplotlib
matplotlib.use('QT4Agg')
from pylab import show, plot, xlabel, ylabel


def prodM(a, b):
    acumula = 0
    for i in xrange(min(len(a), len(b))):
        acumula += a[i] * b[i]
    return acumula

def sigmoid(z):
    exp_z = math.exp(z) 
    return exp_z / (1. + exp_z)
    
def erro(a, p):
    erro = 0.
    for x, y in a:
        erro += (y - prodM(x, p))
    return (erro / len(a)) ** 2


def backp(a, p, learning_rate= 0.001):
    error = 0.
    delta = 0.
    theta = 1.
    for x, y in a[:10]:
        #error += float(i[1]) - prodM(i[0],p) #linear perceptron
        error += y - sigmoid(prodM(x, p))
        delta += error * y * (1. - y) #error * y * (1-y) -- sigmoid perceptron (logistic perceptron)
        #delta += error #linear perceptron
        #print "erro", error, "prod", prodM(i[0],p)
        #print "p", p
        
    for j in xrange(len(p)):
        #error = y - sigmoid(prodM(x, p))
        #delta = error * y * (1. - y) #error * y * (1-y) -- sigmoid perceptron (logistic perceptron)
        p[j] += delta * x[j] * learning_rate
        
    return erro(a, p)



a = [[ [float(i), 1], abs(math.sin(i+1)) ] for i in xrange(1,100)]
p = [2,1]


xlabel("Iterations")
ylabel("Error")


l = []
F_erro = float('inf')
S_erro = F_erro
while S_erro <= F_erro and len(l) < 1000:
    l.append(backp(a,p))
    F_erro = S_erro
    S_erro = l[-1]

plot(range(len(l)), l)
show()
