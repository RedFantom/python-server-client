"""
Author: RedFantom
License: GNU GPLv3
Copyright (C) 2018 RedFantom

Docstrings wrapped to 72 characters, line-comments to 80 characters,
code to 120 characters.
"""
import socket
import threading
import logging
from queue import Queue
from select import select
from client_handler import ClientHandler
from utilities import setup_logger


class Server(threading.Thread):
    """
    A Thread that runs a socket.socket network to listen for incoming
    Client connections. For each of these Clients, a ClientHandler is
    created that can perform actions for a single Client.
    """
    def __init__(self, host, port, amount=8, log_name="Server", log_file="python_server.log",
                 log_level_std=logging.ERROR, log_level_file=logging.DEBUG):
        """
        :param host: hostname to bind to, binds to all available
            addresses if it is an empty string
        :param port: port number, int only
        :param amount: Amount of Clients allowed to connect to the
            Server simultaneously
        """
        threading.Thread.__init__(self)
        # Create a non-blocking socket to provide the best performance in the loop
        # The socket is a SOCK_STREAM (TCP) socket
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.settimeout(0)
        if not Server.check_host_validity(host, port):
            raise ValueError("The host or port value is not valid: {0}:{1}".format(host, port))
        # May fail with PermissionError, socket.error or some other errors
        self.socket.bind((host, port))
        # Attributes
        self.client_handlers = []
        self.exit_queue = Queue()
        self.amount = amount
        self.logger = setup_logger(log_name, log_file, log_level_std, log_level_file)
        # server_queue contains commands of ClientHandlers
        self.server_queue = Queue()
        # The banned list contains IP addresses that will not be accepted
        self.banned = []

    def run(self):
        """
        Loop to provide all the Server functionality. Ends if a True
        value is found in the exit_queue Queue attribute. Allows for
        maximum of eighth people to be logged in at the same time.
        """
        self.socket.listen(self.amount)

        while True:
            # Check if the Server should exit its loop
            if not self.exit_queue.empty() and self.exit_queue.get():
                self.logger.debug("Strategy network is exiting loop")
                break
            # The select.select function is used so the Server can immediately
            # continue with its operations if there are no new clients. This
            # could also be done with a try/except socket.error block, but this
            # would introduce a rather high performance penalty, so the select
            # function is used.
            if self.socket in select([self.socket], [], [], 0)[0]:
                self.logger.info("Server ready to accept Clients")
                connection, address = self.socket.accept()
                # Check if the IP is banned
                if address[0] not in self.banned:
                    # The ClientHandler is created and then added to the list of
                    # active ClientHandlers
                    self.client_handlers.append(ClientHandler(connection, address, self.server_queue))
                else:
                    # If the IP is banned, then a message is sent
                    connection.send(b"ban")
                    connection.close()
            # Check if the Server should exit its loop for the second time in
            # this loop
            if not self.exit_queue.empty() and self.exit_queue.get():
                break
            # Call the update() function on each of the active ClientHandlers to
            # update their state This is a rather long part of the loop. If
            # there are performance issues, the update() function should be
            # checked for problems first, unless the problem in loop code is
            # apparent.
            for client_handler in self.client_handlers:
                try:
                    client_handler.update()
                except Exception as e:
                    self.logger.error(
                        "Error occurred while updating handler for {}: {}".format(client_handler.address, repr(e)))
            # The server_queue contains commands from ClientHandlers, and these
            # should *all* be handled before continuing.
            while not self.server_queue.empty():
                self.do_action_for_server_queue()
            # This is the end of a cycle

        # The loop is broken because an exit was requested. All ClientHandlers
        # are requested to close their their functionality (and sockets)
        self.logger.info("Server closing ClientHandlers")
        for client_handler in self.client_handlers:
            client_handler.close()
            self.logger.debug("Server closed ClientHandler {0}".format(client_handler.name))
        self.logger.debug("Strategy network is returning from run()")
        # Last but not least close the listening socket to release the bind on the address
        self.socket.close()

    def do_action_for_server_queue(self):
        """
        Function called by the Server loop if the server_queue is not
        empty. Does not perform checks, so must only be called after
        checking that the server_queue is not empty.

        Retrieves the command of a ClientHandler from the server_queue
        and handles it accordingly. See line comments for more details.

        Currently only supports the banning of Clients upon a violation
        detected by a ClientHandler and the exiting of Clients.
        """
        handler, command = self.server_queue.get()
        self.logger.debug("Received command in server queue: {}".format(command))

        if command == "ban":
            # The ClientHandler itself should perform the closing functionality
            self.banned.append(handler.address)
        elif command == "exit":
            self.client_handlers.remove(handler)
        else:
            self.logger.error("Unsupported command found in server queue: {}".format(command))

    @staticmethod
    def check_host_validity(host, port):
        """
        Checks if the host and port are valid values, returns True if
        valid, False if not.
        """
        # The host should be str type, the port int type
        if not isinstance(host, str) or not isinstance(port, int):
            return False
        return True

    def close(self):
        self.stop()

    def __exit__(self):
        self.stop()

    def stop(self):
        self.exit_queue.put(True)
