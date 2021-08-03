#!/usr/bin/env python3
#
# SPDX-License-Identifier: GPL-3.0-or-later
#
"""
 Meteor radar timing info recorder
 Use GPS timing.
"""
import argparse
import numpy as np
import uhd
import time
import threading
import numpy as n
import matplotlib.pyplot as plt
import glob
import re
import os
import scipy.signal
import scipy.signal as ss
import os
import signal
from datetime import datetime, timedelta
import traceback
import iono_logger
import gps_lock as gl
import stuffr
import ringbuffer_rf as rb
import h5py

import matchmatch as mm

WantExit = False        # Used to signal an orderly exit


def orderlyExit(signalNumber, frame):
    global WantExit
    # Signal that we want to exit after current sweep
    print("Recieved SIGUSR1", flush=True)
    WantExit = True



def receive_continuous(u, t0, log, thresh=15.0, pulse_len=15,sample_rate=1000000.0):
    """
    New receive script, which processes data incoming from the usrp
    one packet at a time.
    """
    global WantExit

    # hold 10000 samples in a ring buffer
    ringb=rb.ringbuffer_raw(N=10000)

    gps_mon=gl.gpsdo_monitor(u, log, exit_on_lost_lock=True)

    # it seems that waiting until a few seconds before the sweep start
    # helps to keep the ethernet link "alive" for the start of streaming
    t_now=u.get_time_now().get_real_secs()
    while t0-t_now > 5.0:
        t_now=u.get_time_now().get_real_secs()
        print("Waiting for setup %1.2f" % (t0-t_now))
        time.sleep(1)
    t_now=u.get_time_now().get_real_secs()

    # setup usrp to stream continuously, starting at t0
    stream_args=uhd.usrp.StreamArgs("fc32", "sc16")
    rx_stream=u.get_rx_stream(stream_args)
    stream_cmd = uhd.types.StreamCMD(uhd.types.StreamMode.start_cont)
    stream_cmd.stream_now=False
    stream_cmd.time_spec=uhd.types.TimeSpec(t0)
    rx_stream.issue_stream_cmd(stream_cmd)
    md=uhd.types.RXMetadata()

    # this is how many samples we expect to get from each packet
    max_samps_per_packet = rx_stream.get_max_num_samps()

    # receive buffer size large enough to fit one packet
    recv_buffer=n.zeros(max_samps_per_packet, dtype=n.complex64)

    # initial timeout is long enough for us to receive the first packet, which
    # happens at t0
    timeout=(t0-t_now)+5.0

    prev_samples=-1
    
    locked=True
    Exit = False

    prev_outfname=None
    ho = None
    start_idx=[]
    amps=[]
    phases=[]

    det=mm.detector(pulse_len=pulse_len,thresh=thresh)

    try:
        while locked and not Exit:
            num_rx_samps=rx_stream.recv(recv_buffer, md, timeout=timeout)
            if num_rx_samps == 0:
                # shit happened. we probably lost a packet.
                log.log("dropped packet. number of received samples is 0")
                continue

            # the start of the incoming buffer is at this sample index
            samples=int(md.time_spec.get_full_secs())*int(sample_rate) + \
                int(md.time_spec.get_frac_secs()*sample_rate)

            # the number of seconds
            h0=int(np.floor(samples/1000000))
            dirname="./pulses/"+stuffr.sec2dirname(h0)
            
            outfname="%s/pulses-%012d.h5"%(dirname,h0)
            
            if outfname != prev_outfname:
                if ho != None and prev_outfname != None:
                    ho["si"]=start_idx
                    ho["amp"]=amps
                    ho["phase"]=phases
                    
                    mean_ipp=n.mean(n.diff(n.array(start_idx)))
                    print("wrote %s mean_ipp= %1.2f mus"%(prev_outfname,mean_ipp))
                    start_idx=[]
                    amps=[]
                    phases=[]
                    
                    ho.close()
                    gps_mon.check()
                os.system("mkdir -p %s"%(dirname))
                ho=h5py.File(outfname,"w")
                
            prev_outfname=outfname

            # this is how many samples we have jumped forward.
            step = samples-prev_samples

            if prev_samples == -1:
                step = num_rx_samps

            if step != 363 or num_rx_samps != 363:
                log.log("anomalous step %d num_rx_samps %d " % (step, num_rx_samps))

            prev_samples=samples

            ringb.add(samples,recv_buffer)

            # 50 samples before and after buffer
            z=ringb.get(samples-363-50,363+100)*32768.0

            pv,pi=det.detect_pulses(z)
            for pidx in pi:
                pidx=int(pidx)
                if pidx >= 50 and pidx < 363+50:
                    z_mean=n.mean(z[pidx:(pidx+pulse_len)])
                    start_idx.append(samples-363-50+pidx)
                    amps.append(n.abs(z_mean))
                    phases.append(n.angle(z_mean))
            
            Exit = WantExit
            
            timeout=0.1
    except Exception as e:
        traceback.print_exc()
        traceback.print_stack()
        print("interrupt")
        pass
    print("Issuing stop command...")
    stream_cmd = uhd.types.StreamCMD(uhd.types.StreamMode.stop_cont)
    rx_stream.issue_stream_cmd(stream_cmd)

    num_rx_samps=rx_stream.recv(recv_buffer, md, timeout=0.1)
    print("Clearing buffers: ", end='')
    while(num_rx_samps != 0):
        print(".", end='')
        num_rx_samps=rx_stream.recv(recv_buffer, md, timeout=0.1)
    print("\nStream stopped")
    exit(0)
    return

def main():
    """
    Start up everything and run main loop from here.
    """
    log = iono_logger.logger("rx-")    
    # register signals to be caught
    signal.signal(signal.SIGUSR1, orderlyExit)

    sample_rate=1e6
    addr="192.168.10.4"
    freq=36.9e6
    thresh=15.0

    # Configuring USRP
    sample_rate=sample_rate

    # configure usrp
    usrp = uhd.usrp.MultiUSRP("addr=%s,recv_buff_size=500000000" % (addr))
    usrp.set_rx_rate(sample_rate)
    subdev_spec=uhd.usrp.SubdevSpec("A:A")
    usrp.set_rx_subdev_spec(subdev_spec)

    # Synchronizing clock
    gl.sync_clock(usrp, log, min_sync_time=0)

    # figure out when to start the cycle.
    t_now=usrp.get_time_now().get_real_secs()
    # add 5 secs for setup time
    t0=np.uint64(np.ceil(t_now)+5.0)

    # start with initial frequency
    tune_req=uhd.libpyuhd.types.tune_request(freq)
    usrp.set_rx_freq(tune_req)

    # start reading data

    # infinitely loop on receive
    receive_continuous(usrp, t0, log, thresh=thresh)


if __name__ == "__main__":
    main()
