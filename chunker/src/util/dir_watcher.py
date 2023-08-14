import logging

from inotify_simple import INotify, flags

logger = logging.getLogger()

class DirWatcher():
    """
    Wrapper around the INotify linux module in order
    to utilize enter and exit functionality in Python.

    Example:
    ```python
        with DirWatcher('./my_dir', inotify_simple.flags.CLOSE_WRITE) as watcher:
            while True:
                for event in watcher.next(timeout=1)
                    print('file was closed!')
    ```
    """

    def __init__(self, directory, flags):
        self.directory = directory
        self.flags = flags
        self.watch = None
        self.inotify = None

    def __enter__(self):
        self.inotify = INotify()
        self.watch = self.inotify.add_watch(self.directory, self.flags)
        return self

    def __exit__(self, type, value, traceback):
        try:
            self.inotify.rm_watch(self.watch)
        except:
            logger.exception('failed to remove watch')

    def next(self, timeout=None):
        for event in self.inotify.read(timeout=timeout):
            yield event