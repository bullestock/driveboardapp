
import sys
import os
import time
import argparse

import web
from config import conf

__author__  = 'Stefan Hechenberger <stefan@nortd.com>'



### Setup Argument Parser
argparser = argparse.ArgumentParser(description='Run DriveboardApp.', prog='driveboardapp')
argparser.add_argument('-v', '--version', action='version', version='%(prog)s ' + conf['version'],
                       default=False, help='print version of this app')
argparser.add_argument('-t', '--threaded', dest='threaded', action='store_true',
                       default=True, help='run web server in thread')
argparser.add_argument('-d', '--debug', dest='debug', action='store_true',
                       default=False, help='print more verbose for debugging')
argparser.add_argument('-u', '--usbhack', dest='usbhack', action='store_true',
                       default=False, help='use usb reset hack (advanced)')
argparser.add_argument('-b', '--browser', dest='browser', action='store_true',
                       default=False, help='launch interface in browser')
argparser.add_argument('-r', '--disable_rfid', dest='disable_rfid', action='store_true',
                       default=False, help='do not use RFID reader')
args = argparser.parse_args()

# <cardid>: { user: <username>, approved: <bool> }
card_data = {
}

print "DriveboardApp " + conf['version']
conf['usb_reset_hack'] = args.usbhack

# run
web.start(threaded=args.threaded, args=args)
if args.threaded:
    while 1:
        try:
            time.sleep(0.1)
        except KeyboardInterrupt:
            break
    web.stop()
print "END of DriveboardApp"
