"""
Author: RedFantom
License: GNU GPLv3
Copyright (C) 2018 RedFantom

Docstrings wrapped to 72 characters, line-comments to 80 characters,
code to 120 characters.
"""
import socket
import threading
from queue import Queue
from connection import Connection


class Client(threading.Thread, Connection):
    """
    Class that provides an interface to a ClientHandler to send and
    receive messages. This class should be used as a parent class
    for a class that implements the desired functionality. For this
    purpose, the update() function of this class should be overridden.
    """
    def __init__(self, host, port, separator="+"):
        """
        :param host: host name to connect to
        :param port: port number to connect to
        :param separator: message separator
        """
        threading.Thread.__init__(self)
        if not isinstance(separator, str) or len(separator) != 1:
            raise ValueError("Invalid separator character")
        self.exit_queue = Queue()
        self.message_queue = Queue()
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket_lock = threading.Lock()
        self.address = host
        self.port = port
        self.separator = separator

    def connect(self):
        """
        Function to connect to the specified server. Can be overridden
        to additionally perform error handling or perhaps some sort of
        login functionality.
        """
        self.socket_lock.acquire()
        timeout = self.socket.gettimeout()
        self.socket.settimeout(4)
        self.socket.connect((self.address, self.port))
        self.socket.settimeout(timeout)
        self.socket_lock.release()

    def run(self):
        """
        Loop of the Thread to call self.update() and
        self.process_command() by extent.
        """
        while True:
            if not self.exit_queue.empty():
                break
            self.update()
        Connection.close(self, "exit")

    def update(self):
        """
        Function to be implemented by a child class to perform the
        functionality it's made for. Here the child class can process
        messages and call actions to be performed on that. Keep in
        mind that this is run in a separate thread and thus requires
        special care to prevent dead-locks.
        """
        self.receive()

    def close(self, message=None):
        """
        Function that can be overridden by a child class to perform
        additional functionality, such as sending a logout message.
        The actual closing of the socket and such are performed by
        the run() function, which exits upon calling this function
        when it is ready.
        """
        self.exit_queue.put(True)
