#!/usr/bin/env python3

import unittest
import re
import datetime


def merge(*iterables, key=lambda s: s):
    """Функция склеивает упорядоченные по ключу `key` и порядку «меньше»
    коллекции из `iterables`.

    Результат — итератор на упорядоченные данные.
    В случае равенства данных следует их упорядочить в порядке следования
    коллекций"""
    strings = []
    for iterable in iterables:
        if hasattr(iterable, '__next__'):
            while True:
                try:
                    strings.append(next(iterable))
                except StopIteration:
                    break
        else:
            strings.extend(iterable)

    return iter(sorted(strings, key=key))


def log_key(_str):
    """Функция по строке лога возвращает ключ для её сравнения по времени"""
    _time = re.search(r'\d{2}/\w{3}/\d{4}:\d{2}:\d{2}:\d{2}', _str)[0]
    key = datetime.datetime.strptime(_time, "%d/%b/%Y:%H:%M:%S")
    return key


class TestTest(unittest.TestCase):
    def start_tests(self, times, expected, *iterables):
        it = merge(*iterables, key=log_key)
        for i in range(times):
            if expected[i]:
                self.assertEqual(expected[i], next(it))
            else:
                with self.assertRaises(StopIteration):
                    next(it)

    def test_merge(self):
        iterable1 = [
            '127.0.0.1 - - [13/May/2011:06:33:17 +0600] "OPTIONS * HTTP/1.0" '
            '200 152 "-" "Apache/2.2.16 (Debian) (internal dummy '
            'connection)" 1784',  # 1
            '127.0.0.1 - - [13/May/2012:06:33:17 +0600] "OPTIONS * HTTP/1.0" '
            '200 152 "-" "Apache/2.2.16 (Debian) (internal dummy '
            'connection)" 1784',  # 4
            '127.0.0.1 - - [13/Dec/2013:06:33:17 +0600] "OPTIONS * HTTP/1.0" '
            '200 152 "-" "Apache/2.2.16 (Debian) (internal dummy '
            'connection)" 123'  # 5
        ]
        iterable2 = [
            '126.0.0.1 - - [13/May/2011:06:33:17 +0600] "OPTIONS * HTTP/1.1" '
            '200 152 "-" "Apache/2.2.16 (Debian) (internal dummy '
            'connection)" 1784',  # 2
            '127.0.0.1 - - [13/May/2013:06:33:17 +0600] "OPTIONS * HTTP/1.0" '
            '200 152 "-" "Apache/2.2.16 (Debian) (internal dummy '
            'connection)" 54',  # 6
            '127.0.0.1 - - [13/Feb/2014:06:33:17 +0600] "OPTIONS * HTTP/1.0" '
            '200 152 "-" "Apache/2.2.16 (Debian) (internal dummy '
            'connection)" 38'  # 7
        ]
        iterable3 = [
            '127.0.0.1 - - [13/May/2011:06:33:17 +0600] "OPTIONS * HTTP/2.0" '
            '200 152 "-" "Apache/2.2.16 (Debian) (internal dummy '
            'connection)" 1784'  # 3
        ]
        expect = [
            '127.0.0.1 - - [13/May/2011:06:33:17 +0600] "OPTIONS * '
            'HTTP/1.0" 200 152 "-" "Apache/2.2.16 (Debian) (internal '
            'dummy connection)" 1784',
            '126.0.0.1 - - [13/May/2011:06:33:17 +0600] "OPTIONS * '
            'HTTP/1.1" 200 152 "-" "Apache/2.2.16 (Debian) (internal '
            'dummy connection)" 1784',
            '127.0.0.1 - - [13/May/2011:06:33:17 +0600] "OPTIONS * '
            'HTTP/2.0" 200 152 "-" "Apache/2.2.16 (Debian) (internal '
            'dummy connection)" 1784'
        ]
        times = 3
        self.start_tests(times, expect, iterable1, iterable2, iterable3)

    def test_equal_elements(self):
        s = '127.0.0.1 - - [13/May/2011:06:33:17 +0600] "OPTIONS * ' \
            'HTTP/1.0" 200 152 "-" "Apache/2.2.16 (Debian) (internal ' \
            'dummy connection)" 1784'
        self.start_tests(1, [s], [s], [s])

    def test_one_sequence(self):
        iterable = [
            '127.0.0.1 - - [13/May/2011:06:33:17 +0600] "OPTIONS * HTTP/1.0" '
            '200 152 "-" "Apache/2.2.16 (Debian) (internal dummy '
            'connection)" 1784',  # 1
            '127.0.0.1 - - [13/May/2012:06:33:17 +0600] "OPTIONS * HTTP/1.0" '
            '200 152 "-" "Apache/2.2.16 (Debian) (internal dummy '
            'connection)" 1784',  # 2
            '127.0.0.1 - - [13/Dec/2013:06:33:17 +0600] "OPTIONS * HTTP/1.0" '
            '200 152 "-" "Apache/2.2.16 (Debian) (internal dummy '
            'connection)" 123'  # 3
        ]
        self.start_tests(3, [iterable[0], iterable[1], iterable[2]], iterable)

    def test_empty_sequence(self):
        iterable_1 = []
        iterable_2 = [
            '127.0.0.1 - - [13/May/2011:06:33:17 +0600] "OPTIONS * HTTP/1.0" '
            '200 152 "-" "Apache/2.2.16 (Debian) (internal dummy '
            'connection)" 1784'
        ]
        self.start_tests(1, [iterable_2[0]], iterable_1, iterable_2)

    def test_empty_sequence_2(self):
        iterable = []
        self.start_tests(1, [None], iterable)

    def test_iterators_given(self):
        iterable = [
            '127.0.0.1 - - [13/May/2011:06:33:17 +0600] "OPTIONS * HTTP/1.0" '
            '200 152 "-" "Apache/2.2.16 (Debian) (internal dummy '
            'connection)" 1784']
        iterator = iter(iterable)
        self.start_tests(1, [iterable[0]], iterator)

    def test_log_key(self):
        s = '127.0.0.1 - - [13/May/2011:06:33:17 +0600] "OPTIONS * ' \
            'HTTP/1.0" 200 152 "-" "Apache/2.2.16 (Debian) (internal ' \
            'dummy connection)" 1784'
        self.assertEqual(log_key(s), datetime.datetime(2011, 5, 13, 6, 33, 17))


if __name__ == '__main__':
    unittest.main()
