
import socket
import time

class ClientTCPAdapter():
    
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.connected = False       
        self.message = ""

    #------------------------------------------------------------------------------------------#
    def _connect(self):
        """
        Connect to the server
        :return: boolean
        """
        try:
            self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        except socket.error as msg:
            self.client = None
            self.connected = False
            
        try:    
            self.client.connect((self.host, self.port))
        except socket.error:
            logging.error('Could not connect to ' + self.host)
            self.connected = False
        else:
            self.connected = True                
    
    #------------------------------------------------------------------------------------------#
    def _read_all(self, timeout=0.1):
        """
        Method to read from server until communication is finished
        :param timeout: float / the timeout
        :return:
        """
        # make socket non blocking
        self.client.setblocking(0)     
        total_data = '';
        data = '';     
        begin = time.time()
        while 1:
            # if you got some data, then break after timeout
            if data and time.time() - begin > timeout:
                break
         
            # if you got no data at all, wait a little longer, twice the timeout
            elif time.time() - begin > timeout * 2:
                break
            elif data.find('END\r') > 0:
                break
            # recv something
            try:
                data = data + self.client.recv(8192)
                if data:

                    # change the beginning time for measurement
                    begin = time.time()
                else:
                    # sleep for sometime to indicate a gap
                    time.sleep(0.1)
            except:
                pass
        
        # join all parts to make final string
        return data

    #------------------------------------------------------------------------------------------#
    def _read(self):
        """
        read a message from server
        """
        if self.connected:
            
            ret = self._read_all()
            ret = ret.splitlines()
            try:
                ret.pop()
            except:
                ret = ''
                
            self.message = "\n".join(ret)
            self.client.sendall('quit\n')

    #------------------------------------------------------------------------------------------#
    def send(self, message):
        """
        send a message
        :param message: string - the message
        """

        self._connect()
        if self.connected:    
            self.client.sendall(message + "\n")
            self._read()        
            self.client.close()

    #------------------------------------------------------------------------------------------#
    def receive(self):
        return self.message
