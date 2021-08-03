import numpy as n
import matplotlib.pyplot as plt
import h5py
import scipy.fftpack as fp

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

    
def detect_pulses(z,pulse_len=13,thresh=15.0,min_spacing=300.0,debug=True):

    # square pulse
    w=n.array(n.repeat(1.0/pulse_len,int(pulse_len)),dtype=n.float32)
    # difference
    wd=n.array(n.concatenate((n.repeat(1/pulse_len,pulse_len),n.repeat(-1/pulse_len,pulse_len))),dtype=n.float32)
    # triangle
    w2=n.array(n.convolve(w,w,mode="same"),dtype=n.float32)

    # triangle diff
    wtd=n.array(n.convolve(w,wd)[::-1],dtype=n.float)
 #   plt.plot(wtd)
  #  plt.show()
    

    # we expect this to be a triangle
#    zo=n.abs(n.convolve(w,z,mode="same"))
    zo=n.roll(n.abs(fftconv(w,z)),-pulse_len)#n.convolve(w,z,mode="same"))
#    plt.plot(zo)
#    plt.show()

    #    triang_diff=n.convolve(wtd,n.convolve(wd,zo,mode="same"),mode="same")
    triang_diff=n.roll(n.real(fftconv(wtd,fftconv(wd,zo))),-int(2.5*pulse_len-1))#n.convolve(wd,zo,mode="same"),mode="same")
    triang_diff[triang_diff<0]=0.0
#    plt.plot(triang_diff)
#    plt.plot(z.real)
#    plt.plot(z.imag)
#    plt.plot(zo)
#    plt.show()
    
    peaks=(zo+triang_diff)/2.0
    v,idx=peak_det(peaks,thresh=thresh)
    idx=n.array(idx)
    if debug:
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
    fl=glob.glob("test/testing*.h5")
    fl.sort()
    for f in fl:
        h=h5py.File(f,"r")
        z=h["z"][()]
        p=detect_pulses(z)
        h.close()

if __name__ == "__main__":
    test()
        
