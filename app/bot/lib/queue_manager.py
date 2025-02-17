import random

class QueueManager:
    def __init__(self):
        self.track_queue = []

    def add_to_queue(self, url):
        self.track_queue.append(url)

    def add_to_front_of_queue(self, url):
        self.track_queue.insert(0, url)

    def shuffle_queue(self):
        random.shuffle(self.track_queue)

    def clear_queue(self):
        self.track_queue.clear()

    def get_next_track(self):
        return self.track_queue.pop(0) if self.track_queue else None

    def is_queue_empty(self):
        return len(self.track_queue) == 0

    def get_queue_list(self):
        return self.track_queue


queue_manager = QueueManager()