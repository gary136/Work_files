import threading
import time


def m():
    with open('i.txt', 'a') as f:
        f.write('i')
    
class ThreadingExample(object):
    """ Threading example class
    The run() method will be started and it will run in the background
    until the application exits.
    """

    def __init__(self, interval=1):
        """ Constructor
        :type interval: int
        :param interval: Check interval, in seconds
        """
        self.interval = interval

        thread = threading.Thread(target=self.run, args=())
        thread.daemon = True                            # Daemonize thread
        thread.start()                                  # Start the execution

    def run(self):
        """ Method that runs forever """
        while True:
            # Do something
            m()
            print('Doing something important in the background {}'.format(time.asctime(time.localtime())))

            time.sleep(self.interval)

example = ThreadingExample(15)
example.run()
time.sleep(3)
print('Checkpoint')
time.sleep(2)
print('Bye')


