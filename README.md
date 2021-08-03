# Over the air radar pulse detection

A simple program that records radar pulses over the air and captures the phase and amplitude of each outgoing pulse. This is a very early beta version that only works with the Sodankylä SKymet meteor radar. For other radars, you'll need to fine tune the parameters. 

This metadata is useful for synchronizing a multi-static network of meteor radars when using older skyimet radars that are not gps synchronized.

You'll need a USRP N200 with an internal GPSDO and a BasicRX or LFRX daughterboard. You'll also need a VHF antenna and a GPS antenna. 
