#!/usr/bin/env python3
import sys
import datetime
import re

epsilon = sys.float_info.epsilon
re_ip = r'(\d{1,3}.){3}\d{1,3}'
re_time = r'\S* \S*'
re_request = r'"(GET|PUT|POST|HEAD|OPTIONS|DELETE) [^\*]\S* HTTP/[1-2]\.[0-1]"'
re_code = r'\d{3}'
re_weight = r'\d*'
re_referrer = r'".*"'
re_user_agent = r'.*'
re_request_time = r'( \d*)?'
pattern = re.compile(' '.join([
    r'(?P<ip>' + re_ip + r')',
    r'-\s-',
    r'\[(?P<time>' + re_time + r')\]',
    r'(?P<answer>' + re_request + r')',
    re_code,
    re_weight,
    re_referrer,
    r'"(?P<agent>' + re_user_agent + r')"']
) + r'(?P<req_time>' + re_request_time + r')')


class Page:
    def __init__(self, name, req_time):
        self.name = name
        self.count = 1
        self.fast_req_t = int(req_time) if req_time else 0
        self.slow_req_t = int(req_time) if req_time else 0
        self.req_times = int(req_time) if req_time else 0
        self.avg = self.req_times if self.req_times > 0 else 1
        self.num = -1

    def upd_page(self, req_time):
        self.req_times += int(req_time) if req_time else 0
        self.count += 1
        self.avg = self.req_times / self.count
        if req_time:
            self.upd_times(int(req_time))

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
        self.most_active_client = None
        self.m_a_cs = []  # [{date: client}, ...]
        self.popular_browser = None

        self.num = 0

        self._pages = {}
        self._browsers = {}
        self._clients = {}
        self._days = {}  # {date: {name: count, ...}, ...}

        self.results()

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
        self.m_a_cs = [x for x in range(len(self._days))]
        i = 0
        for day in self._days.items():
            max_by_day_count = ('', 0)
            for name in day[1]:
                if day[1][name] > max_by_day_count[1]:
                    max_by_day_count = (name, day[1][name])
            self.m_a_cs[i] = (day[0], max_by_day_count[0])
            i += 1

    def _parse_line(self, line):
        log = pattern.fullmatch(line)
        if log:
            self._add_page(log)
            self._add_client(log)

    def _add_page(self, log):
        name = log.group('answer').split()[1]
        req_time = log.group('req_time')

        if name in self._pages:
            page = self._pages[name]
            page.upd_page(req_time)
        else:
            page = self._pages[name] = Page(name, req_time)

        if page.num == -1:
            page.num = self.num
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
        date = datetime.date(*self._get_date(log.group('time')))
        if date not in self._days:
            self._days[date] = {name: 0}

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

    def _get_date(self, log_time):
        date_array = log_time.split()[0].split('/')
        return [int(date_array[2].split(':')[0]),
                int(self._convert_to_month(date_array[1])),
                int(date_array[0])]

    @staticmethod
    def _convert_to_month(month):
        months = [
            'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
            'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'
        ]
        return months.index(month) + 1

    def results(self):
        for line in sys.stdin:
            self._parse_line(line[:-1])

        for page_name in self._pages:
            page = self._pages[page_name]
            self._upd_the_most_popular_page(page)

        for client_name in self._clients:
            client = self._clients[client_name]
            self._upd_the_most_active_client(client_name, client)

        for browser in self._browsers:
            self._upd_the_most_popular_browser(browser)

        self._get_the_most_active_clients_by_days()

        self._output()

    def _output(self):
        output = 'FastestPage: {0}\nMostActiveClient: {1}\nMostActiv' \
                 'eClientByDay:\n  {2} \n\nMostPopularBrowser: {3}' \
                 '\nMostPopularPage: {4}\nSlowestAveragePage: {5}' \
                 '\nSlowestPage: {6}\n\n'.format(
                    self.fastest.name,
                    self.most_active_client,
                    '\n  '.join(f'{x[0]}: {x[1]}' for x in self.m_a_cs),
                    self.popular_browser,
                    self.most_popular_page.name,
                    self.slowest_avg.name,
                    self.slowest.name
                    )
        print(output)


if __name__ == '__main__':
    LogStat()
