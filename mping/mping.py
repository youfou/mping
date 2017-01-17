#!/usr/bin/env python3
# coding: utf-8

import argparse
import ctypes
import json
import os
import random
import re
import select
import socket
import struct
import sys
import threading
import time

if sys.platform.startswith('win32'):
    clock = time.clock
    run_as_root = ctypes.windll.shell32.IsUserAnAdmin() != 0
else:
    clock = time.time
    run_as_root = os.getuid() == 0

DEFAULT_DURATION = 3

EXIT_CODE_BY_USER = 1
EXIT_CODE_DNS_ERR = 2
EXIT_CODE_IO_ERR = 3


# Credit: https://gist.github.com/pyos/10980172
def chk(data):
    x = sum(x << 8 if i % 2 else x for i, x in enumerate(data)) & 0xFFFFFFFF
    x = (x >> 16) + (x & 0xFFFF)
    x = (x >> 16) + (x & 0xFFFF)
    return struct.pack('<H', ~x & 0xFFFF)


# From the same gist commented above, with minor modified.
def ping(addr, timeout=1, udp=not run_as_root, number=1, data=b''):
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM if udp else socket.SOCK_RAW, socket.IPPROTO_ICMP) as conn:
        payload = struct.pack('!HH', random.randrange(0, 65536), number) + data

        conn.connect((addr, 80))
        conn.sendall(b'\x08\0' + chk(b'\x08\0\0\0' + payload) + payload)
        start = clock()

        while select.select([conn], [], [], max(0, start + timeout - clock()))[0]:
            data = conn.recv(65536)
            if data[20:] == b'\0\0' + chk(b'\0\0\0\0' + payload) + payload:
                return clock() - start


class PingResults(list):
    def __init__(self, multiply=1000):
        """
        A list to save ping results, and can be used to count min/avg/max, etc.
        :param multiply: Every valid result will be multiplied by this number.
        """
        super(PingResults, self).__init__()
        self.multiple = multiply

    def append(self, rtt):
        """
        To receive a ping result, accept a number for how long the single ping took, or None for timeout.
        :param rtt: The ping round-trip time.
        """
        if rtt is not None and self.multiple:
            rtt *= self.multiple
        return super(PingResults, self).append(rtt)

    @property
    def valid_results(self):
        return list(filter(lambda x: x is not None, self))

    @property
    def valid_count(self):
        return len(self.valid_results)

    @property
    def loss_rate(self):
        if self:
            return 1 - len(self.valid_results) / len(self)

    @property
    def min(self):
        if self.valid_results:
            return min(self.valid_results)

    @property
    def avg(self):
        if self.valid_results:
            return sum(self.valid_results) / len(self.valid_results)

    @property
    def max(self):
        if self.valid_results:
            return max(self.valid_results)

    @property
    def form_text(self):
        if self.valid_results:
            return '{0.valid_count}, {0.loss_rate:.1%}, {0.min:.1f}/{0.avg:.1f}/{0.max:.1f}'.format(self)
        elif self:
            return 'FAILED'
        else:
            return 'EMPTY'

    def __str__(self):
        return self.form_text

    def __repr__(self):
        return '{}({})'.format(self.__class__.__name__, self.form_text)


class PingTask(threading.Thread):
    def __init__(self, host, timeout, interval):
        """
        A threading.Thread based class for each host to ping.
        :param host: a host name or ip address
        :param timeout: timeout for each ping
        :param interval: the max time to sleep between each ping
        """

        if re.match(r'[\d.]+$', host):
            self.ip = host
        else:
            print('Resolving host: {}'.format(host))
            try:
                self.ip = socket.gethostbyname(host)
            except socket.gaierror:
                print('Unable to resolve host: {}'.format(host))
                exit(EXIT_CODE_DNS_ERR)

        self.timeout = timeout
        self.interval = interval

        self.pr = PingResults()
        self.terminated = False

        super(PingTask, self).__init__()

    def run(self):
        while not self.terminated:
            rtt = ping(self.ip, timeout=self.timeout)
            self.pr.append(rtt)
            escaped = rtt or self.timeout
            if escaped < self.interval:
                time.sleep(self.interval - escaped)

    def stop(self):
        self.terminated = True


def mping(hosts, duration=DEFAULT_DURATION, timeout=1.0, interval=0.0, quiet=False, sort=True):
    """
    Ping hosts in multi-threads, and return the ping results.
    :param hosts: A list of hosts, or a {name: host, ...} formed dict. A host can be a domain or an ip address
    :param duration: The duration which pinging lasts in seconds
    :param timeout: The timeout for each single ping in each thread
    :param interval: The max time to sleep between each single ping in each thread
    :param quiet: Do not print results while processing
    :param sort: The results will be sorted by valid_count in reversed order if this param is True
    :return: A list of PingResults
    """

    def ret(_tasks, _sort=True):
        r = list(zip(heads, [t.pr for t in _tasks]))
        if _sort:
            r.sort(key=lambda x: x[1].valid_count, reverse=True)
        return r

    if isinstance(hosts, list):
        heads = hosts
    elif isinstance(hosts, dict):
        heads = list(hosts.items())
        hosts = hosts.values()
    else:
        type_err_msg = '`hosts` should be a host list, or a {name: host, ...} formed dict.'
        raise TypeError(type_err_msg)

    try:
        tasks = [PingTask(host, timeout, interval) for host in hosts]
    except KeyboardInterrupt:
        exit(EXIT_CODE_BY_USER)
    else:
        doing_msg = 'Pinging {} hosts'.format(len(hosts))
        if duration > 0:
            doing_msg += ' within {} seconds'.format(duration)
        doing_msg += '...'

        if quiet:
            print(doing_msg)

        for task in tasks:
            task.start()

        start = clock()
        remain = duration

        try:
            while remain > 0 or duration <= 0:
                time.sleep(min(remain, 1))
                if not quiet:
                    print('\n{}\n{}'.format(
                        results_string(ret(tasks, True)[:10]),
                        doing_msg))
                remain = duration + start - clock()
        except KeyboardInterrupt:
            print()
        finally:
            for task in tasks:
                task.stop()
            for task in tasks:
                task.join()

        return ret(tasks, sort)


def table_string(rows):
    rows = list(map(lambda x: list(map(str, x)), rows))
    widths = list(map(lambda x: max(map(len, x)), zip(*rows)))
    rows = list(map(lambda y: ' | '.join(map(lambda x: '{:{w}}'.format(x[0], w=x[1]), zip(y, widths))), rows))
    rows.insert(1, '-|-'.join(list(map(lambda x: '-' * x, widths))))
    return '\n'.join(rows)


def results_string(prs):
    named = True if isinstance(prs[0][0], tuple) else False
    rows = [['host', 'count, loss%, min/avg/max']]
    if named:
        rows[0].insert(0, 'name')

    for head, pr in prs:
        row = list()
        if named:
            row.extend(head)
        else:
            row.append(head)
        row.append(pr.form_text)
        rows.append(row)
    return table_string(rows)


def main():
    ap = argparse.ArgumentParser(
        description='Ping multiple hosts concurrently and find the fastest to you.',
        epilog='A plain text file or a json can be used as the -p/--path argument: '
               '1. Plain text file: hosts in lines; '
               '2. Json file: hosts in a list or a object (dict) with names.')

    ap.add_argument(
        'hosts', type=str, nargs='*',
        help='a list of hosts, separated by space')

    ap.add_argument(
        '-p', '--path', type=str, metavar='path',
        help='specify a file path to get the hosts from')

    ap.add_argument(
        '-d', '--duration', type=int, default=DEFAULT_DURATION, metavar='secs',
        help='the duration how long the progress lasts (default: {})'.format(DEFAULT_DURATION))

    ap.add_argument(
        '-i', '--interval', type=float, default=0.0, metavar='secs',
        help='the max time to wait between pings in each thread (default: 0)')

    ap.add_argument(
        '-t', '--timeout', type=float, default=1.0, metavar='secs',
        help='the timeout for each single ping in each thread (default: 1.0)')

    ap.add_argument(
        '-a', '--all', action='store_true',
        help='show all results (default: top 10 results)'
             ', and note this option can be overridden by -S/--no_sort')

    ap.add_argument(
        '-q', '--quiet', action='store_true',
        help='do not print results while processing (default: print the top 10 hosts)'
    )

    ap.add_argument(
        '-S', '--do_not_sort', action='store_false', dest='sort',
        help='do not sort the results (default: sort by ping count in descending order)')

    args = ap.parse_args()

    hosts = None
    if not args.path and not args.hosts:
        ap.print_help()
    elif args.path:
        try:
            with open(args.path) as fp:
                hosts = json.load(fp)
        except IOError as e:
            print('Unable open file:\n{}'.format(e))
            exit(EXIT_CODE_IO_ERR)
        except json.JSONDecodeError:
            with open(args.path) as fp:
                hosts = re.findall(r'^\s*([a-z0-9\-.]+)\s*$', fp.read(), re.M)
    else:
        hosts = args.hosts

    if not hosts:
        exit()

    results = mping(
        hosts=hosts,
        duration=args.duration,
        timeout=args.timeout,
        interval=args.interval,
        quiet=args.quiet,
        sort=args.sort
    )

    if not args.all and args.sort:
        results = results[:10]

    if not args.quiet:
        print('\nFinal Results:\n')
    print(results_string(results))


if __name__ == '__main__':
    main()
