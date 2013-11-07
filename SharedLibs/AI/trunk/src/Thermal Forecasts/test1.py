def function(a=10, b=0.5, point=(0,0)):
    '''sen(a*x + b)'''
    if sin(a*point[0]+b) > point[1]:
        return -1
    else:
        return +1

samples1 = []

def choose_color(n):
    color = {1:'r^', -1:'b^'}
    return color[n]

for i in range(1000):
    x, y = uniform(-1,1), uniform(-1,1)
    samples1.append(((x,y), function(point=(x,y))))

pylab.figure()

data = SupervisedDataSet(2,1)

for i in samples1:
    data.addSample(i[0],i[1])

#net = buildNetwork(2, 10, 1)

net = FeedForwardNetwork()
inLayer = LinearLayer(2)
hiddenLayer0 = SigmoidLayer(10)
hiddenLayer1 = SigmoidLayer(2)
outLayer = LinearLayer(1)

net.addInputModule(inLayer)
net.addModule(hiddenLayer0)
net.addModule(hiddenLayer1)
net.addOutputModule(outLayer)

net.addConnection(FullConnection(inLayer, hiddenLayer0))
net.addConnection(FullConnection(hiddenLayer0, hiddenLayer1))
net.addConnection(FullConnection(hiddenLayer1, outLayer))

net.sortModules()

trainer1 = BackpropTrainer(net, data)
trainer1.trainEpochs(epochs=100)

for i in samples1:
    pylab.plot(i[0][0], i[0][1], choose_color(i[1]))

for i in range(200):
    for j in range(200):
        if abs(net.activate((float(i)/100-1, float(j)/100-1))) < 0.1:
            pylab.plot(float(i)/100-1, float(j)/100-1, 'gs')


