
import zmq
import sys
class ClientZMQAdapter():
    
    def __init__(self, host, port):
        context = zmq.Context()
        self.host = str(host)
        self.port = str(port)
        self.username = ""
        self.password = ""
        # Socket to receive messages on
        
        self.socket = context.socket(zmq.REQ)        
                
        self.socket.RCVTIMEO = 10000
        self.message = ''

    #------------------------------------------------------------------------------------------#
    def send(self, message):
        """
        Send a message to the server
        :param message: string
        :return:boolean
        """
        self.socket.plain_username = self.username
        self.socket.plain_password = self.password
        self.socket.connect ("tcp://"+self.host+":"+self.port)
        
        self.socket.send_string(b''+message, zmq.NOBLOCK)
        try:
            self.message = self.socket.recv()            
        except:
            self.message = ''
            return False
        return True

    #------------------------------------------------------------------------------------------#
    def setUsername(self, username):
        """
        authentification to the server with username
        :param username: string - the username
        """
        self.username = username

    #------------------------------------------------------------------------------------------#
    def setPassword(self, password):
        """
        authentification to the server with password
        :param password: string - the password
        """
        self.password = password

    #------------------------------------------------------------------------------------------#
    def receive(self):
        """
        Return the currently received message
        :return:string - message from server
        """
        return self.message

    