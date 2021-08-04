# Over the air radar pulse metadata logging

A simple software defined radio program that records radar pulses over the air and captures the phase, amplitude, and timing of radar pulses being transmitted by a radar. This metadata is useful for synchronizing a multi-static network of meteor radars when using older pulsed radar transmitters that are not GPS synchronized. 

This is a very early beta version that only works with the Sodankylä meteor radar, which sends out 13 microsecond pulses at a pulse repetition frequency of about 2444 Hz. For other radars, you'll need to fine tune the parameters or even make changes to the program. 

You'll need a USRP N200 with an internal GPSDO and a BasicRX or LFRX daughterboard. You'll also need a VHF antenna and a GPS antenna. 
