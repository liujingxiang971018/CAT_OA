
import numpy as np
import  matplotlib.pyplot as plt
from scipy.optimize import root,fsolve

def theta(theta0):
    a=3.57
    b=[-1.93,-1.34,-0.32]
    def F(x):
        f=0
        P = list()
        P.append(1)
        for i in range(len(b)):
            P.append(1.0 / (1 + np.exp(-1.7 * a * (x - b[i]))))
        P.append(0)
        for j in range(len(b) + 1):
            if  j + 1==3:
                f = f - 1.7 * a * (P[j] + P[j + 1] - 1)

        return np.array(f)
    sol_root=root(F,[theta0])
    sol_fsolve=fsolve(F,[theta0])
    # print(sol_root,sol_root.x)
    print(sol_fsolve)
    if float(sol_fsolve[0])<=-3:
        return -3.0
    if float(sol_fsolve[0])>=3:
        return 3.0
    return sol_fsolve

def plte():
    a = 3.57
    b = [-1.93, -1.34, -0.32]
    f = 0
    x = theta(-1.505)
    P = list()
    P.append(1)
    for i in range(len(b)):
        P.append(1.0 / (1 + np.exp(-1.7 * a * (x - b[i]))))
    P.append(0)
    for j in range(len(b) + 1):
        if j + 1 == 3:
            f = f - 1.7 * a * (P[j] + P[j + 1] - 1)

    plt.scatter(x,f,linewidths=9)
    plt.show()

plte()