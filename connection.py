"""
Author: RedFantom
License: GNU GPLv3
Copyright (C) 2018 RedFantom

Docstrings wrapped to 72 characters, line-comments to 80 characters,
code to 120 characters.
"""
import socket
from threading import Lock
from queue import Queue


class Connection(object):
    """
    A class that manages a socket object to provide basic functionality
    using strings, such as sending and receiving individual messages.
    The messages are stored in a Queue attribute.

    A Connection can be used in two ways:

    - A child class can inherit the functions from the Connection (like
      a Client does) if the child class makes sure to set the correct
      attributes. Then the class does not have to make a call to
      __init__ and the functions of the class can be used upon an
      instance of the class. Required attributes:

      :attribute socket: Ready-to-go socket object
      :attribute message_queue: Queue-like object to store messages in
      :attribute socket_lock: Lock object to ensure thread-safety
      :attribute separator: Separator for the messages

    - As a plain instance that is initialized with the class initializer
      to set up a socket and a connection to go along with it and send
      messages by calling the functions upon this class instance.
    """

    ATTRIBUTES = {
        "socket": socket.socket,
        "socket_lock": Lock,
        "message_queue": Queue,
        "separator": str
    }

    def __init__(self, address=None, sock=None, separator="+", lock=Lock(), queue=Queue()):
        """
        Either address or sock must be provided, or both.
        :param address: address tuple (address: str, port: int)
        :param sock: Socket object to operate with
        :param separator: UTF-8 character that is used to separate
            individual messages
        :param lock: Lock instance that is used for the socket to
            ensure thread-safety
        :param queue: Queue instance that is used as the message queue
        """
        # Perform argument checks
        if not isinstance(address, tuple) or not isinstance(address[0], str) or not isinstance(address[1], int):
            raise TypeError("address argument not a valid address tuple")
        if not isinstance(sock, socket.socket):
            raise TypeError("sock is not a valid socket")
        if not isinstance(separator, str) or len(separator) != 1:
            raise ValueError("separator is not a valid single character string")
        if not isinstance(lock, Lock):
            raise TypeError("lock is not a valid Lock instance")
        if not isinstance(queue, Queue):
            raise TypeError("queue is not a valid normal Queue")
        if address is None and sock is None:
            raise ValueError("address and sock cannot both be None")

        # Set attributes
        self.socket = sock if sock is not None else socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.separator = separator
        self.socket_lock = lock
        self.message_queue = queue

        # Set-up the socket object
        if sock is None:  # Address is not None and self.socket is not None
            self.socket.connect(address)

    def send(self, message, error=False):
        """
        Sends a message to the server the Connection is connected to.
        :param message: string of the message to send
        :param error: If set to True, errors will be raised when the
            message cannot be sent (that detail what went wrong).
            When set to False (default), the function returns True if
            successful and False upon failure.
        :return: True if successful, False upon failure if error is set
            to False
        """
        if not isinstance(message, str):
            raise TypeError("Connection only supports str messages")
        if not self._check_ready():
            if error is True:
                raise RuntimeError("Not all attributes set correctly")
            return False
        # Lock the socket to ensure thread-safety
        self.socket_lock.acquire()
        try:
            self.socket.send((message + self.separator).encode())
        except (BrokenPipeError, ConnectionError, socket.error):
            # Always release the Lock to prevent a deadlock
            self.socket_lock.release()
            if error is False:
                return False
            # error is True
            raise
        self.socket_lock.release()
        return True

    def receive(self, block=False, timeout=2, buffer=32):
        """
        Function to receive and separate messages received from the
        ClientHandler. Runs a loop to read the socket buffer into
        memory, and then splits the message using the separator. Then,
        each separate command is put in the message_queue.

        This function is not called in the Thread. This function must
        be called manually.
        :param block: When set to True, the function will set the
                      socket to blocking and apply the timeout
        :param timeout: Timeout to use when receiving from the socket
        :param buffer: Buffer size to use for the socket. A smaller
                    buffer size lowers memory usage, but also
                    requires more recv calls in order to receive the
                    full message if the message is longer than the
                    buffer size
        """
        if not self._check_ready():
            raise RuntimeError("Not all attributes set correctly")
        self.socket_lock.acquire()
        self.socket.setblocking(block)
        self.socket.settimeout(timeout)
        total = b""  # Will store the complete buffer contents
        wait = False  # Indicates whether the full message was received
        while True:
            try:
                message = self.socket.recv(buffer)
                # Compare the last character to the separator
                wait = message[-1] != self.separator.encode()[0]
                # Message is empty, end of buffer
                if message == b"":
                    break
                total += message
            # socket.error when non-blocking, timeout when blocking
            except (socket.error, socket.timeout):
                # If the last character was not a separator character, the
                # message is not finished. It may be that two messages are
                # received because of this, but they are put in the queue
                # separately later
                if wait is True:
                    continue  # Keep waiting for more data
                break
        # Done with the socket
        self.socket_lock.release()
        # Split the messages based on the separator
        elements = total.split(self.separator.encode())
        for elem in elements:
            # This whole framework is string-based
            elem = elem.decode()
            # The last element may be empty
            if elem == "":
                continue
            self.message_queue.put(elem)
        # To get a message, access message_queue
        return

    def close(self, message=None):
        """
        Closes the Connection.
        """
        if not self._check_ready():
            raise RuntimeError("Not all attributes set correctly")
        self.socket_lock.acquire()
        if message is not None:
            self.send(message)
        self.socket.close()
        self.socket_lock.release()

    def _check_ready(self):
        """
        Private class function to prevent the usage of a socket without
        the proper attributes if the class was not initialized.
        :raises: AttributeError if an attribute is not available
        :raises: TypeError if an attribute is of the incorrect type
        """
        for attribute, attr_type in self.ATTRIBUTES.items():
            if not hasattr(self, attribute):
                raise AttributeError("Attribute {} is not set".format(attribute))
            if not isinstance(getattr(self, attribute), attr_type):
                raise TypeError("Attribute {} is not of {} type".format(attribute, attr_type))
        return True


