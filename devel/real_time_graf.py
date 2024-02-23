import numpy as np
import matplotlib.pyplot as plt
import datetime
from matplotlib.widgets import CheckButtons
dateTime = []
value0 = []
value1 = []
value2 = []
value3 = []
x = datetime.datetime.now()
plt.title("Digital in")
plt.xlabel("Time")
plt.ylabel("Value")


def callback(label):
    ln = lines_by_label[label]
    ln.set_visible(not ln.get_visible())
    ln.figure.canvas.draw_idle()

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
    print(y0,y1,y2,y3)
    dateTime.append(x)
    value0.append(y0)
    value1.append(y1)
    value2.append(y2)
    value3.append(y3)
    #time.append(i)
    fig, ax = plt.subplots()
    l0 = ax.plot(xpoints0,ypoints0,visible=True, lw=2, color='black', label='IN0')
    l1 = ax.plot(xpoints0,ypoints1,visible=True, lw=2, color='red', label='IN1')
    l2 = ax.plot(xpoints0,ypoints2,visible=True, lw=2, color='blue', label='IN2')
    l3 = ax.plot(xpoints0,ypoints3,visible=True, lw=2, color='green', label='IN3')
    fig.subplots_adjust(left=0.25)
    print("fdsadfas",l0,l1,l2,l3)
    lines_by_label = {l.get_label(): l for l in [l0, l1, l2, l3]}
    plt.pause(1)
    rax = fig.add_axes([0.05, 0.4, 0.1, 0.15])
    check = CheckButtons(
    ax=rax,
    labels=lines_by_label.keys(),
    actives=[l.get_visible() for l in lines_by_label.values()],)
    check.on_clicked(callback)
plt.show()
