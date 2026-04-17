import numpy as np
import random

Q = np.zeros((4,3))
alpha=0.1
gamma=0.9
epsilon=0.1

def reward(s,a):
    if s==3 and a==2: return 20
    elif s==3: return -20
    elif s==2 and a==2: return 10
    elif s==2 and a==0: return -10
    else: return 2

for _ in range(2000):
    s=random.randint(0,3)
    a=random.randint(0,2) if random.random()<epsilon else np.argmax(Q[s])
    r=reward(s,a)
    ns=random.randint(0,3)
    Q[s,a]+=alpha*(r+gamma*np.max(Q[ns])-Q[s,a])

print('Q-table:',Q)
np.save('q_table.npy',Q)