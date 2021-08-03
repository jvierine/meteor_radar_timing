import numpy as n
import matplotlib.pyplot as plt
import h5py
import scipy.fftpack as fp
import time

import glob


def fftconv(a,b,N=None):
    N=n.max([len(a),len(b)])
    c=fp.ifft(fp.fft(a,N)*fp.fft(b,N))
    return(c)

def peak_det(z,thresh=15,min_spacing=300):
    peaks=[]
    idxs=[]
    zt=n.copy(z)
    while n.max(zt) > thresh:
        mi=n.argmax(zt)
        peaks.append(zt[mi])
        idxs.append(mi)
        mini=n.max([0,mi-min_spacing])
        maxi=n.min([len(z),mi+min_spacing])
        zt[mini:mi]=0.0
        zt[mi:maxi]=0.0
    return(peaks,idxs)

class detector:
    def __init__(self,pulse_len=13,thresh=15.0,min_spacing=300,debug=False):
        self.pulse_len=pulse_len
        self.thresh=thresh
        self.min_spacing=min_spacing
        self.debug=debug
        # square pulse
        self.w=n.array(n.repeat(1.0/self.pulse_len,int(self.pulse_len)),dtype=n.float32)
        # difference
        self.wd=n.array(n.concatenate((n.repeat(1/self.pulse_len,self.pulse_len),n.repeat(-1.0/self.pulse_len,self.pulse_len))),dtype=n.float32)
        # triangle
        self.w2=n.array(n.convolve(self.w,self.w,mode="same"),dtype=n.float32)
        
        # triangle diff
        self.wtd=n.array(n.convolve(self.w,self.wd)[::-1],dtype=n.float)
    

    def detect_pulses(self,z):#,pulse_len=13,thresh=15.0,min_spacing=300.0,debug=True):
        zo=n.roll(n.abs(fftconv(self.w,z)),-self.pulse_len)#n.convolve(w,z,mode="same"))

        triang_diff=n.roll(n.real(fftconv(self.wtd,fftconv(self.wd,zo))),-int(2.5*self.pulse_len-1))#n.convolve(wd,zo,mode="same"),mode="same")
        triang_diff[triang_diff<0]=0.0
    
        peaks=(zo+triang_diff)/2.0
        v,idx=peak_det(peaks,thresh=self.thresh)
        idx=n.array(idx)
        if self.debug:
            print(v)
            print(idx)
            plt.plot(peaks)
            plt.plot(z.real)
            plt.plot(z.imag)
            for i in idx:
                plt.axvline(i)
            plt.show()
        return(peaks,idx)

def test():
    d=detector()
    fl=glob.glob("test/testing*.h5")
    fl.sort()
    for f in fl:
        h=h5py.File(f,"r")
        z=h["z"][()]
        N=len(z)
        nrep=int(n.ceil(1e6/N))
        t0=time.time()
        for i in range(nrep):
            p=d.detect_pulses(z)
        t1=time.time()
        print("dt=%1.2f"%(t1-t0))
        h.close()

if __name__ == "__main__":
    test()
        

