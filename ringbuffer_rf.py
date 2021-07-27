import numpy as np

class ringbuffer_raw:
    def __init__(self,N=10000):
        self.head=0
        self.tail=0
        self.N=N
        self.z=np.zeros(N,dtype=np.complex64)

    def add(self,i0,inz):
        n_in=len(inz)
        idx=(np.arange(n_in,dtype=np.uint64)+i0)%self.N
        self.z[idx]=inz
        self.tail = i0 + n_in
        self.head = self.tail - self.N
        
    def get(self,i0,n_out):
        idx=(np.arange(n_out,dtype=np.uint64)+i0)%self.N
        return(self.z[idx])
    
        
        
        
if __name__ == "__main__":
    rb=ringbuffer_raw(N=1000)
    rb.add(0,np.zeros(1000))
    rb.add(1000,np.zeros(1000))    
    z=rb.get(0,1000)
    print(z)
