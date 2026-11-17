import sys; sys.path.insert(0, sys.argv[2])
import numpy as np, lutgrid as L
n,t=L.load_cube(sys.argv[1])
i=np.arange(n**3); ref=np.stack([i%n,(i//n)%n,i//(n*n)],1)/(n-1)
d=np.abs(t-ref).max(1)*255
print('vs identity (8-bit units): mean %.3f p99 %.3f max %.3f'%(d.mean(),np.percentile(d,99),d.max()))
k=d.argmax(); print('worst node in',ref[k].round(3),'out',t[k].round(3))
