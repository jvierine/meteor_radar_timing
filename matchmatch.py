import numpy as n
import matplotlib.pyplot as plt
import h5py

import glob

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

    
def detect_pulses(z,pulse_len=13,thresh=15.0,min_spacing=300.0,debug=False):
    half=n.round(pulse_len/2)
    # square pulse
    w=n.repeat(1.0/pulse_len,int(pulse_len))
    # difference
    wd=n.concatenate((n.repeat(1/pulse_len,pulse_len),n.repeat(-1/pulse_len,pulse_len)))
    # triangle
    w2=n.convolve(w,w)

    # triangle diff
    wtd=n.convolve(w2,wd)[::-1]

    # we expect this to be a triangle
    zo=n.abs(n.convolve(w,z,mode="same"))

    triang_diff=n.convolve(wtd,n.convolve(wd,zo,mode="same"),mode="same")
    triang_diff[triang_diff<0]=0.0

    # diff triangle
    diff_match=n.convolve(wd,w)[::-1]
    
    zod=n.convolve(diff_match,n.convolve(wd,n.abs(z),mode="same"),mode="same")
    zod[zod<0]=0.0
    
    peaks=(zo+triang_diff+zod)/3.0
    v,idx=peak_det(peaks,thresh=thresh)
    idx=n.array(idx)-half
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
        
