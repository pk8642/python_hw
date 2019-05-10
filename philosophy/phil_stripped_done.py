#!/usr/bin/env python3
from urllib.request import urlopen
from urllib.parse import unquote, quote
from urllib.error import URLError, HTTPError
import re
import sys


def get_content(name):
    """
    Функция возвращает содержимое вики-страницы name из русской Википедии.
    В случае ошибки загрузки или отсутствия страницы возвращается None.
    """
    try:
        with urlopen(f'https://ru.wikipedia.org/wiki/{quote(name)}') as p:
            content = p.read().decode('utf-8')
    except (URLError, HTTPError):
        return None
    return content


def extract_content(page):
    """
    Функция принимает на вход содержимое страницы и возвращает 2-элементный
    tuple, первый элемент которого — номер позиции, с которой начинается
    содержимое статьи, второй элемент — номер позиции, на котором заканчивается
    содержимое статьи.
    Если содержимое отсутствует, возвращается (0, 0).
    """
    if not page:
        return 0, 0
    left = page.index('"content"')
    right = page.index('"mw-navigation"')
    return left, right


def extract_links(page, begin, end):
    """
    Функция принимает на вход содержимое страницы и начало и конец интервала,
    задающего позицию содержимого статьи на странице и возвращает все имеющиеся
    ссылки на другие вики-страницы без повторений и с учётом регистра.
    """
    if not page:
        return []
    return (re.findall(r'[\'"]/wiki/([\w+,%]+)[\'"]',
                       unquote(page)[begin: end]))


def find_chain(start, finish):
    """
    Функция принимает на вход название начальной и конечной статьи и возвращает
    список переходов, позволяющий добраться из начальной статьи в конечную.
    Первым элементом результата должен быть start, последним — finish.
    Если построить переходы невозможно, возвращается None.
    """
    visited = []
    links = set()
    links.add(start)
    parents = {start: start}
    while len(links) > 0:
        current = links.pop()
        if current not in visited:
            visited.append(current)
            content = get_content(current)
            begin, end = extract_content(content)
            links_to_see = set(extract_links(content, begin, end)) - links
            if finish in links_to_see:
                parents[finish] = current
                break
            for link in links_to_see - parents.keys():
                parents[link] = current
            links = links.union(links_to_see)

    if finish in parents.keys():
        t = finish
        way = [t]
        while t != start:
            t = parents[t]
            way.append(t)
        way.reverse()
        return way
    else:
        return None


def main():
    name = sys.argv[1]
    links = find_chain(name, 'Философия')
    if links:
        [print(link) for link in links]


if __name__ == '__main__':
    main()
