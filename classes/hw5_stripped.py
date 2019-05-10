#!/usr/bin/env python3
import sys
import datetime
import re
import time
import unittest
import bz2
import urllib.request

epsilon = sys.float_info.epsilon
months = [
    'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
    'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'
]

re_ip = r'^\S*'
re_time = r'(?P<time>[\d\w/]*):\S* \S*'
re_request = r'"(GET|PUT|POST|HEAD|OPTIONS|DELETE) (?P<name>[^\*]\S*) \S*"'
re_code = r'\d{3}'
re_weight = r'\d*'
re_referrer = r'".*"'
re_user_agent = r'.*'
re_request_time = r'( \d*)?$'
pattern = re.compile(' '.join([
    r'(?P<ip>' + re_ip + r')',
    r'- -',
    r'\[' + re_time + r'\]',
    re_request,
    re_code,
    re_weight,
    re_referrer,
    r'"(?P<agent>' + re_user_agent + r')"']
) + r'(?P<req_time>' + re_request_time + r')')


class Page:
    def __init__(self, name, req_time, num):
        self.name = name
        self.count = 1
        if req_time:
            r_t = int(req_time)
            self.fast_req_t = r_t
            self.slow_req_t = r_t
            self.req_times = r_t
            self.avg = r_t
        self.num = num

    def upd_page(self, req_time):
        if req_time:
            self.upd_times(int(req_time))
            self.req_times += int(req_time)
        self.count += 1
        self.avg = self.req_times / self.count

    def upd_times(self, req_t):
        if req_t < self.fast_req_t:
            self.fast_req_t = req_t
        elif req_t > self.slow_req_t:
            self.slow_req_t = req_t


class LogStat:
    def __init__(self):
        self.fastest = None  # Page
        self.slowest = None  # Page
        self.slowest_avg = None  # Page
        self.most_popular_page = None  # Page
        self.most_active_client = None  # ip
        self.macs = {}  # {date: client, ...}
        self.popular_browser = None

        self.num = 0

        self._pages = {}
        self._browsers = {}
        self._clients = {}
        self._days = {}  # {date: {name: count, ...}, ...}

    def _upd_the_fastest_page(self, page):
        if self.fastest:
            if self.fastest.fast_req_t < page.fast_req_t:
                return

        self.fastest = page

    def _upd_the_slowest_page(self, page):
        if self.slowest:
            if self.slowest.slow_req_t > page.slow_req_t:
                return

        self.slowest = page

    def _upd_the_slowest_avg_page(self, page):
        if self.slowest_avg is None:
            self.slowest_avg = page
            return

        if page.avg > self.slowest_avg.avg:
            self.slowest_avg = page
        elif abs(page.avg - self.slowest_avg.avg) < \
                max(abs(page.avg), abs(self.slowest_avg.avg)) * epsilon:
            if page.num < self.slowest_avg.num:
                self.slowest_avg = page

    def _upd_the_most_popular_page(self, page):
        if self.most_popular_page is None:
            self.most_popular_page = page
            return

        if page.count > self.most_popular_page.count:
            self.most_popular_page = page
        elif page.count == self.most_popular_page.count:
            if page.name < self.most_popular_page.name:
                self.most_popular_page = page

    def _upd_the_most_active_client(self, name, client):
        if self.most_active_client is None:
            self.most_active_client = name
            return

        if client['count'] > self._clients[self.most_active_client]['count']:
            self.most_active_client = name
        elif client['count'] == \
                self._clients[self.most_active_client]['count']:
            if name < self.most_active_client:
                self.most_active_client = name

    def _upd_the_most_popular_browser(self, browser):
        if self.popular_browser is None:
            self.popular_browser = browser
            return

        if self._browsers[browser] > self._browsers[self.popular_browser]:
            self.popular_browser = browser
        elif self._browsers[browser] == \
                self._browsers[self.popular_browser]:
            if browser < self.popular_browser:
                self.popular_browser = browser

    def _get_the_most_active_clients_by_days(self):
        for day in self._days.items():
            self.macs[day[0]] = max(day[1], key=lambda n: day[1][n])

    def add_from_stdin(self):
        for line in sys.stdin:
            self.add_line(line)

    def add_line(self, line):
        log = pattern.match(line[:-1])
        if log:
            self._add_page(log)
            self._add_client(log)

    def _add_page(self, log):
        name = log.group('name')
        req_time = log.group('req_time')

        if name in self._pages:
            page = self._pages[name]
            page.upd_page(req_time)
        else:
            page = self._pages[name] = Page(name, req_time, self.num)
            self.num += 1

        if req_time:
            self._upd_the_fastest_page(page)
            self._upd_the_slowest_page(page)
            self._upd_the_slowest_avg_page(page)

        browser = log.group('agent')

        if browser in self._browsers:
            self._browsers[browser] += 1
        else:
            self._browsers[browser] = 1

    def _add_client(self, log):
        name = log.group('ip')
        date = self._get_date(log.group('time'))
        if date not in self._days:
            self._days[date] = dict()

        if name in self._clients:
            client = self._clients[name]
            client['count'] += 1
        else:
            self._clients[name] = {
                'count': 1
            }

        self._add_to_days(name, date)

    def _add_to_days(self, name, date):
        if name in self._days[date]:
            self._days[date][name] += 1
        else:
            self._days[date][name] = 1

    @staticmethod
    def _get_date(log_time):
        date_array = log_time.split('/')
        return datetime.date(int(date_array[2]),
                             int(months.index(date_array[1])) + 1,
                             int(date_array[0]))

    def results(self):
        if self.fastest is None:
            self.add_from_stdin()

        for page_name in self._pages:
            page = self._pages[page_name]
            self._upd_the_most_popular_page(page)

        for client_name in self._clients:
            client = self._clients[client_name]
            self._upd_the_most_active_client(client_name, client)

        for browser in self._browsers:
            self._upd_the_most_popular_browser(browser)

        self._get_the_most_active_clients_by_days()

        return {
            'FastestPage': self.fastest.name,
            'MostActiveClient': self.most_active_client,
            'MostActiveClientByDay': self.macs,
            'MostPopularBrowser': self.popular_browser,
            'MostPopularPage': self.most_popular_page.name,
            'SlowestAveragePage': self.slowest_avg.name,
            'SlowestPage': self.slowest.name
        }


def make_stat():
    return LogStat()


class LogStatTests(unittest.TestCase):
    def setUp(self):
        self.stat = make_stat()

    def test_from_example(self):
        with (urllib.request.urlopen('ftp://shannon.usu.edu.ru/python/hw4/v2'
                                     '/examples/example_1.log.bz2')) as f:
            with bz2.open(f) as g:
                self.data = g.read().decode('ASCII').split('\n')

        for line in self.data:
            self.stat.add_line(line)

        self.assertDictEqual(
            self.stat.results(),
            {
                'FastestPage': '/css/main.css',
                'MostActiveClient': '192.168.74.151',
                'MostActiveClientByDay':
                    {datetime.date(2013, 2, 17): '192.168.74.151'},
                'MostPopularBrowser': 'Mozilla/4.0 (compatible; MSIE 7.0; '
                                      'Windows NT 6.1; WOW64; Trident/5.0; '
                                      'SLCC2; .NET CLR 2.0.50727; .NET CLR '
                                      '3.5.30729; .NET CLR 3.0.30729; Media '
                                      'Center PC 6.0; InfoPath.3; .NET4.0C; '
                                      '.NET4.0E)',
                'MostPopularPage': '/pause/ajaxPause?pauseConfigId=&admin=0',
                'SlowestAveragePage': '/lib/callider/graph.registr_tel.php'
                                      '?auto=0',
                'SlowestPage': '/pause/ajaxPause?pauseConfigId=&admin=0'
            }
        )

    def test_from_example_2(self):
        with urllib.request.urlopen('ftp://shannon.usu.edu.ru/python/hw4/v2'
                                    '/test.log') as f:
            self.data = f.read().decode('utf-8').split('\n')

        for line in self.data:
            self.stat.add_line(line)

        self.assertDictEqual(
            self.stat.results(),
            {
                'FastestPage': '/img/r.png',
                'MostActiveClient': '192.168.12.155',
                'MostActiveClientByDay': {
                    datetime.date(2012, 7, 8): '192.168.12.155'},
                'MostPopularBrowser': 'Mozilla/4.0 (compatible; MSIE 8.0; '
                                      'Windows NT 6.1; Trident/4.0; SLCC2; '
                                      '.NET CLR 2.0.50727; .NET CLR '
                                      '3.5.30729; .NET CLR 3.0.30729; Media '
                                      'Center PC 6.0; Tablet PC 2.0; '
                                      '.NET4.0C; .NET4.0E; InfoPath.3; '
                                      'MS-RTC LM 8)',
                'MostPopularPage': '/img/ao.gif',
                'SlowestAveragePage': '/call_centr.php',
                'SlowestPage': '/menu-top.php'
            }
        )

    def test_get_date(self):
        self.assertEqual(self.stat._get_date('17/Feb/2013'),
                         datetime.date(2013, 2, 17))

    def test_get_date_2(self):
        self.assertEqual(self.stat._get_date('1/Mar/2015'),
                         datetime.date(2015, 3, 1))

    def test_page(self):
        s = '192.168.65.56 - - [17/Feb/2013:06:37:21 +0600] "GET ' \
            '/pause/ajaxPause?pauseConfigId=all&admin=1 HTTP/1.1" 200 1047 ' \
            '"http://192.168.65.101/pause/index" "Mozilla/5.0 (Windows NT ' \
            '5.1; rv:15.0) Gecko/20100101 Firefox/15.0" 3376692'
        log = pattern.match(s)
        self.assertTrue(log)

        page = Page(log.group('name'), log.group('req_time'), 4)
        self.assertEqual(page.name, '/pause/ajaxPause?pauseConfigId=all'
                                    '&admin=1')
        self.assertEqual(page.count, 1)
        self.assertTrue(page.avg == page.req_times == 3376692)

    def test_slowest_avg(self):
        self.stat.slowest_avg = Page('fast', 170, 1)
        slow_page = Page('slow', 170, 0)

        self.stat._upd_the_slowest_avg_page(slow_page)

        self.assertEqual(self.stat.slowest_avg.name, 'slow')

    # def test_from_example_3(self):
    #     self.make_data('ftp://shannon.usu.edu.ru/python/hw4/v2/examples'
    #                    '/example_2.log.bz2')
    #
    #     self.assertDictEqual(
    #         self.stat.results(),
    #         {
    #             'FastestPage': '/images/box/6.png',
    #             'MostActiveClient': '192.168.65.56',
    #             'MostActiveClientByDay': {
    #                 datetime.date(2013, 2, 17): '192.168.65.56',
    #                 datetime.date(2013, 2, 18): '192.168.65.56',
    #                 datetime.date(2013, 2, 19): '192.168.65.56'
    #             },
    #             'MostPopularBrowser': 'Mozilla/4.0 (compatible; MSIE 7.0; '
    #                                   'Windows NT 6.1; WOW64; Trident/5.0; '
    #                                   'SLCC2; .NET CLR 2.0.50727; .NET CLR '
    #                                   '3.5.30729; .NET CLR 3.0.30729; Media '
    #                                   'Center PC 6.0; InfoPath.3; .NET4.0C; '
    #                                   '.NET4.0E)',
    #             'MostPopularPage': '/pause/ajaxPause?pauseConfigId=&admin=0',
    #             'SlowestAveragePage': '/lib/icq/mlICQ2.php',
    #             'SlowestPage': '/lib/icq/mlICQ2.php'
    #         }
    #     )
    #
    # def test_from_example_4(self):
    #     self.make_data('ftp://shannon.usu.edu.ru/python/hw4/v2/examples'
    #                    '/example_3.log.bz2')
    #
    #     self.assertDictEqual(
    #         self.stat.results(),
    #         {
    #             'FastestPage': '/images/sun.gif',
    #             'MostActiveClient': '192.168.12.65',
    #             'MostActiveClientByDay': {
    #                 datetime.date(2013, 1, 13): '192.168.12.65',
    #                 datetime.date(2013, 1, 14): '192.168.12.65',
    #                 datetime.date(2013, 1, 15): '192.168.12.111',
    #                 datetime.date(2013, 1, 16): '192.168.12.65',
    #                 datetime.date(2013, 1, 17): '192.168.12.65',
    #                 datetime.date(2013, 1, 18): '192.168.12.65',
    #                 datetime.date(2013, 1, 19): '192.168.12.65',
    #                 datetime.date(2013, 1, 20): '192.168.12.65',
    #                 datetime.date(2013, 1, 21): '192.168.12.65',
    #                 datetime.date(2013, 1, 22): '192.168.12.65',
    #                 datetime.date(2013, 1, 23): '192.168.12.65',
    #                 datetime.date(2013, 1, 24): '192.168.12.65',
    #                 datetime.date(2013, 1, 25): '192.168.12.111',
    #                 datetime.date(2013, 1, 26): '192.168.12.111',
    #                 datetime.date(2013, 1, 27): '192.168.12.111',
    #                 datetime.date(2013, 1, 28): '192.168.12.65',
    #                 datetime.date(2013, 1, 29): '192.168.12.111',
    #                 datetime.date(2013, 1, 30): '192.168.12.111',
    #                 datetime.date(2013, 1, 31): '192.168.12.65',
    #                 datetime.date(2013, 2, 1): '192.168.12.65',
    #                 datetime.date(2013, 2, 2): '192.168.12.111',
    #                 datetime.date(2013, 2, 3): '192.168.12.111',
    #                 datetime.date(2013, 2, 4): '192.168.12.111',
    #                 datetime.date(2013, 2, 5): '192.168.12.65',
    #                 datetime.date(2013, 2, 6): '192.168.12.65',
    #                 datetime.date(2013, 2, 7): '192.168.74.151',
    #                 datetime.date(2013, 2, 8): '192.168.12.65',
    #                 datetime.date(2013, 2, 9): '192.168.12.208',
    #                 datetime.date(2013, 2, 10): '192.168.12.208',
    #                 datetime.date(2013, 2, 11): '192.168.12.65',
    #                 datetime.date(2013, 2, 12): '192.168.12.65',
    #                 datetime.date(2013, 2, 13): '192.168.12.65',
    #                 datetime.date(2013, 2, 14): '192.168.12.65',
    #                 datetime.date(2013, 2, 15): '192.168.12.65',
    #                 datetime.date(2013, 2, 16): '192.168.12.65',
    #                 datetime.date(2013, 2, 17): '192.168.74.151',
    #                 datetime.date(2013, 2, 18): '192.168.12.65',
    #                 datetime.date(2013, 2, 19): '192.168.12.65',
    #                 datetime.date(2013, 2, 20): '192.168.12.65',
    #                 datetime.date(2013, 2, 21): '192.168.12.65',
    #                 datetime.date(2013, 2, 22): '192.168.12.65',
    #                 datetime.date(2013, 2, 23): '192.168.12.65',
    #                 datetime.date(2013, 2, 24): '192.168.12.9'
    #             },
    #             'MostPopularBrowser': 'Mozilla/5.0 (Windows NT 6.1; WOW64) '
    #                                   'AppleWebKit/537.17 (KHTML, '
    #                                   'like Gecko) Chrome/24.0.1312.57 '
    #                                   'Safari/537.17',
    #             'MostPopularPage': '/tv/useUser',
    #             'SlowestAveragePage': '/graph/excel?dateCount=31&info=%D1%8F'
    #                                   '%D0%BD%D0%B2%D0%B0%D1%80%D1%8C+2013'
    #                                   '&date_b=01.01.2013&date_e=31.01.2013',
    #             'SlowestPage': '/graph/excel?dateCount=31&info=%D1%8F%D0%BD'
    #                            '%D0%B2%D0%B0%D1%80%D1%8C+2013&date_b=01.01'
    #                            '.2013&date_e=31.01.2013'
    #         }
    #     )


if __name__ == '__main__':
    LogStat().results()
