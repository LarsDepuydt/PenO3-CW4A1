import threading
from time import sleep

nummer = [0, 0]
class testje(threading.Thread):
    def __init__(self, lijst, index):
        super().__init__()
        self.lijst = lijst
        self.index = index
    def run(self):
        print('hallo')

class print_testje(threading.Thread):
    def __init__(self, woord):
        super().__init__()
        self.woord = woord
    def run(self):
        print(self.woord[0])

step_1 = testje(nummer, 0)
step_2 = print_testje(nummer)

while True:
    print(nummer)
    step_1.start()
    step_1.()
    print(nummer)
    step_2.start()
    step_2.join()
    step_2.end()
    print(nummer)
