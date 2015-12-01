import Queue
import threading

from metaswitch.sasclient import sender, LOGGER


class Client(object):
    def __init__(self, system_name, system_type, resource_identifier, sas_address, sas_port):
        """
        Constructs the client and the message queue.
        """
        self._queue = Queue.Queue()
        self._stopper = None
        self._worker = None

        LOGGER.debug("Starting SAS client")
        self.start(system_name, system_type, resource_identifier, sas_address, sas_port)

    def start(self, system_name, system_type, resource_identifier, sas_address, sas_port):
        """
        Spins up the thread to do the work, and connects to the SAS server.
        :return:
        """
        if self._worker:
            # We already had a worker. start must have been called twice consecutively. Log, and try to recover.
            # TODO: log error
            self.stop()

        self._stopper = threading.Event()
        self._worker = sender.MessageSender(self._stopper, self._queue, system_name, system_type, resource_identifier,
                                            sas_address, sas_port)
        self._worker.setDaemon(True)

        # Make the initial connection.
        self._worker.connect()

        # Start the message sender worker thread.
        self._worker.start()

    def stop(self):
        """
        Stop the worker thread, closing the connection, and remove references to thread-related objects. Queued messages
        will be left on the queue until the queue is garbage collected, or the queue is reused and the messages are
        sent.
        The worker thread is a daemon, so it isn't usually necessary to call this, but it is preferred.
        """
        # TODO: think about the case where the thread is connecting (with no timeout) but the system wants to stop.
        self._stopper.set()
        self._worker.join()
        if self._queue.empty():
            # TODO: log that the queue exited successfully, with no messages left
            pass
        else:
            # TODO: log that the queue exited with messages still on.
            pass

        self._worker = None
        self._stopper = None

    def send(self, message):
        self._queue.put(message)


class Trail(object):
    next_trail = 1
    next_trail_lock = threading.Lock()

    def __init__(self):
        self._trail = Trail.next_trail

        Trail.next_trail_lock.acquire()
        Trail.next_trail += 1
        Trail.next_trail_lock.release()

    def get_trail_id(self):
        return self._trail
