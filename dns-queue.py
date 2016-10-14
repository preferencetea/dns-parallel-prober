"""
PoC for distributing DNS queries
================================

"""
from __future__ import print_function
import argparse
from collections import deque
import itertools
import random
import string
import sys
import time
import threading


INCREASE_PERCENT = 0.1
MAX_DOMAIN_LEN = 3


res = deque()


class Prober(threading.Thread):
    def __init__(self, dns_server, target):
        # invoke Thread.__init__
        super(Prober, self).__init__()
        # set the parameters needed for this thread e.g. hostname
        print("Target: {}".format(target))
        self.target = target
        self.dns_server = dns_server

    def run(self):
        # this simulates how long the DNS query will take; substitute with the
        # actual DNS query command then save the output to a database

        ###
        # remove from here
        #
        # using a normal distribution to simulate real work
        _will_take = abs(random.gauss(0, 1) * 5)
        time.sleep(_will_take)
        res.append("{} done in {}s".format(self.target, _will_take))
        #
        # to here
        ###


def subdomain_gen():
    """Generates all subdomains"""
    for i in range(MAX_DOMAIN_LEN):
        for p in itertools.permutations(string.lowercase, i + 1):
            yield ''.join(p)


sub = subdomain_gen()


def fill(d, amount, dom):
    for i in range(amount):
        # add new probers, taking the hostnames from a list or a generator
        t = Prober('dns_server', '{}.{}'.format(sub.next(), dom))
        t.start()
        d.append(t)


def main(dom, max_running_threads):
    print("-: increase queue ckeck interval by {}%\n.: no change\n".format(INCREASE_PERCENT))
    # this is the starting value - it will adjust it according to depletion rate
    sleep_time = 0.5

    d = deque()
    fill(d, max_running_threads, dom)

    # for plotting
    # ql = deque()
    # ql.append(len(d))

    previous_len = len(d)
    running = True
    while running:
        try:
            time.sleep(sleep_time)
            # go through the queue and remove the threads that are done
            for el in range(len(d)):
                _t = d.popleft()
                if _t.is_alive():
                    # put it back and continue
                    d.append(_t)
                else:
                    # thread was done - we remove it from the queue
                    pass
            # calculate how fast the queue has been changind
            delta = previous_len - len(d)
            rate = delta / sleep_time
            # print('\tq: {}\tdelta: {}\trate: {}\t{}s'.format(len(d), delta, rate, sleep_time))
            # ql.append(len(d))

            if rate > 0 and delta > max_running_threads / 10:
                sleep_time -= (sleep_time * INCREASE_PERCENT)
                print('+', end="")
            else:
                sleep_time += (sleep_time * INCREASE_PERCENT)
                # print('-', end="")
                # else:
                # queue is neither empyting too fast nor filling up too fast -
                # we're OK
                print('.', end="")
                # pass

            fill(d, delta, dom)
            previous_len = len(d)

        except KeyboardInterrupt:
            print("\nPlease wait for all threads to finish...")
            running = False
        finally:
            sys.stdout.flush()

    for el in range(len(d)):
        t = d.popleft()
        t.join()
    print(res)
    # use: gnuplot 'plot "data.txt" with lines' to see queue
    # with open('data.txt', 'w') as f:
    #     for i, el in enumerate(ql):
    #         f.write('{} {}\n'.format(i, el))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("domain")
    parser.add_argument("max_running_threads", type=int)
    args = parser.parse_args()
    main(args.domain, args.max_running_threads)
