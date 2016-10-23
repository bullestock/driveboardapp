
import sys
import time
import json
import threading
import logging
from websocket.SimpleWebSocketServer import WebSocket, SimpleWebSocketServer
from config import conf
import driveboard

logging.basicConfig(format='%(asctime)s %(message)s', level=logging.DEBUG)



class Server():
    def __init__(self):
        self.reset()

    def reset(self):
        self.server = None
        self.serverthread = None
        self.serverlock = threading.Lock()
        self.stop_server = False
        self.messagethread = None
        self.messageglock = threading.Lock()
        self.message = None
        self.message_on_connected = None
        self.stop_messager = False
        self.msg_every = 1
        self.msg_send_counter = 0

S = Server()


class ClientSocket(WebSocket):

    def handleMessage(self):
        # echo
        # self.sendMessage(str(self.data))

        # print str(self.data)
        try:
            msg = json.loads(str(self.data))
        except ValueError:
            msg = {}
        # print msg

        if "status_every" in msg:
            with S.messageglock:
                S.msg_every = msg["status_every"]
                # print S.msg_every

        # if 'cmd_air_enable' in msg:
        #     print "air"
        #     driveboard.air_on()
        #
        # elif 'cmd_air_disable' in msg:
        #     print "noair"
        #     driveboard.air_off()



    def handleConnected(self):
        print "statserver: Client %s connected." % self.address
        with S.messageglock:
            message_cache = S.message_on_connected
        if message_cache:
            self.sendMessage(message_cache)

    def handleClose(self):
        print "statserver: Client connection %s closed." % self.address



def start():
    ### server thread
    print "statserver: Starting on port %s." % (conf['websocket_port'])
    S.stop_server = False
    S.server = SimpleWebSocketServer(conf['network_host'],
                                     conf['websocket_port'], ClientSocket)

    def run_server():
        while True:
            with S.serverlock:
                S.server.process(timeout=0.01)
                if S.stop_server:
                    break
            # sys.stdout.flush()

    S.serverthread = threading.Thread(target=run_server)
    S.serverthread.daemon = True  # kill thread when main thread exits
    S.serverthread.start()

    ### messager thread
    S.stop_messager = False
    def run_messager():
        message_cache = None
        while True:
            with S.messageglock:
                if S.stop_messager:
                    break
                if S.message:
                    message_cache = S.message
                    S.message = None
            if message_cache:
                with S.serverlock:
                    # broadcast message
                    for client in S.server.connections.itervalues():
                        try:
                            client.sendMessage(message_cache)
                        except Exception as n:
                            print n
                message_cache = None
            time.sleep(0.01)
            # sys.stdout.flush()

    S.messagethread = threading.Thread(target=run_messager)
    S.messagethread.deamon = True  # kill thread when main thread exits
    S.messagethread.start()



def stop():
    if S.messagethread and S.messagethread.is_alive():
        with S.messageglock:
            S.stop_messager = True
        S.messagethread.join()
        print "statserver: Message thread stopped."
    else:
        print "statserver: Message thread was already stopped."

    if S.serverthread and S.serverthread.is_alive():
        with S.serverlock:
            S.stop_server = True
        S.serverthread.join()
        print "statserver: Server thread stopped."
    else:
        print "statserver: Server thread was already stopped."

    S.reset()



def is_running():
    return bool(S.server)


def msg_every_now():
    ret = False
    with S.messageglock:
        S.msg_send_counter += 1
        # print "--- %s >= %s" % (S.msg_send_counter, S.msg_every)
        if S.msg_send_counter >= S.msg_every:
            # print "-"
            S.msg_send_counter = 0
            ret = True
    return ret


def send(msg):
    """Broadcast a message to all clients.
    This function is low-latency optimized by delegating the sending
    process to a different thread. Even the locking is optimized
    with some caching.
    """
    with S.messageglock:
        S.message = msg


def on_connected_message(msg):
    """Set message that will be send to a newly connected client"""
    with S.messageglock:
        S.message_on_connected = msg
