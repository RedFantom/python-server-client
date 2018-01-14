"""
Author: RedFantom
License: GNU GPLv3
Copyright (C) 2018 RedFantom

Docstrings wrapped to 72 characters, line-comments to 80 characters,
code to 120 characters.
"""
from connection import Connection
from utilities import setup_logger


class ClientHandler(Connection):
    """
    Simple class that supports the handling of a single Client. The
    ClientHandler is created by the Server, and runs in the same thread
    as the Server. Communication with the parent server is performed
    using Queues, so the Server only handles commands from a
    ClientHandler when it is ready.
    """

    def __init__(self, sock, address, server_queue, debug=False):
        """
        :param sock: Connection object
        :param address: (ip, id) tuple
        :param server_queue: Queue
        """
        Connection.__init__(self, sock=sock)
        self.server_queue = server_queue
        ip, id = address
        self.logger = setup_logger("ClientHandler", "client_handler_{}.log".format(ip))

    def update(self):
        """
        Function to be implemented by a child class to perform the
        functionality of the class.
        """
        self.receive()
