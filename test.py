import time

while True:
    m = 'the current time is {}\n'.format(time.asctime(time.localtime()))
    with open('log', 'a') as f:
        f.write(m)
    time.sleep(1)