import numpy as np
import matplotlib.pyplot as plt
import datetime

dateTime = []
value0 = []
value1 = []
value2 = []
value3 = []
x = datetime.datetime.now()
plt.title("Sports Watch Data")
plt.xlabel("Average Pulse")
plt.ylabel("Calorie Burnage")
plt.grid()
for i in range(10000):
    x = [datetime.datetime.now()]
    xpoints0 = np.array(dateTime)
    ypoints0 = np.array(value0)
    ypoints1 = np.array(value1)
    ypoints2 = np.array(value2)
    ypoints3 = np.array(value3)
    y0 = np.random.randint(10,20)
    y1 = np.random.randint(0,2)
    y2 = np.random.randint(0,2)
    y3 = np.random.randint(0,2)
    print(y1,y2,y3)
    dateTime.append(x)
    value0.append(y0)
    value1.append(y1)
    value2.append(y2)
    value3.append(y3)
    #time.append(i)
    plt.plot(xpoints0,ypoints0)
    plt.plot(xpoints0,ypoints1)
    plt.plot(xpoints0,ypoints2)
    plt.plot(xpoints0,ypoints3)
    plt.pause(1)
plt.show()
