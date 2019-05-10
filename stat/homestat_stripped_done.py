#!/usr/bin/env python3
import re


def make_stat(filename):
    """
    Функция вычисляет статистику по именам за каждый год с учётом пола.
    """
    stat = {}
    f = open(filename, encoding='cp1251')
    with f:
        i = 0
        line = f.readline()
        while line:
            if 'h3>' in line:
                i = (re.search(r'\d{4}', line)[0])  # год
                stat[i] = {}
            elif 'a href' in line:
                line.encode('cp1251')
                name = re.findall(r'[А-яё]+', line)[1]  # имя
                if name in stat[i]:
                    stat[i][name] += 1
                    # инкремент счетчика имени при его имении в словаре
                else:
                    stat[i][name] = 1
                    # инициализация счетчика
            line = f.readline()
    return stat


def extract_years(stat):
    """
    Функция принимает на вход вычисленную статистику и выдаёт список годов,
    упорядоченный по возрастанию.
    """
    return sorted(stat.keys())  # ключами являются года


def extract_general(stat):
    """
    Функция принимает на вход вычисленную статистику и выдаёт список tuple'ов
    (имя, количество) общей статистики для всех имён.
    Список должен быть отсортирован по убыванию количества.
    """
    all_names = {}
    for names_dict in stat.values():
        for name in names_dict:
            if name in all_names:
                all_names[name] = all_names[name] + names_dict[name]
                # имеющееся кол-во + новое
            else:
                all_names[name] = names_dict[name]
                # если не было имени, то положить первое кол-во за год
    return sorted(all_names.items(), key=lambda name_stat: 1/name_stat[1])
    # не совсем понял, как реверсить, сделал так


female_regexp = r'[^тв](а$)|(ета$)|(^[^И]*я$)|(вь$)'  # все девушки


def extract_general_male(stat):
    """
    Функция принимает на вход вычисленную статистику и выдаёт список tuple'ов
    (имя, количество) общей статистики для имён мальчиков.
    Список должен быть отсортирован по убыванию количества.
    """
    all_people = extract_general(stat)
    return [x for x in all_people if not re.search(female_regexp, x[0])]


def extract_general_female(stat):
    """
    Функция принимает на вход вычисленную статистику и выдаёт список tuple'ов
    (имя, количество) общей статистики для имён девочек.
    Список должен быть отсортирован по убыванию количества.
    """
    all_people = extract_general(stat)
    return [x for x in all_people if re.search(female_regexp, x[0])]


def extract_year(stat, year):
    """
    Функция принимает на вход вычисленную статистику и год.
    Результат — список tuple'ов (имя, количество) общей статистики для всех
    имён в указанном году.
    Список должен быть отсортирован по убыванию количества.
    """
    return extract_general({year: stat[year]})


def extract_year_male(stat, year):
    """
    Функция принимает на вход вычисленную статистику и год.
    Результат — список tuple'ов (имя, количество) общей статистики для всех
    имён мальчиков в указанном году.
    Список должен быть отсортирован по убыванию количества.
    """
    all_people = extract_year(stat, year)
    return [x for x in all_people if not re.search(female_regexp, x[0])]


def extract_year_female(stat, year):
    """
    Функция принимает на вход вычисленную статистику и год.
    Результат — список tuple'ов (имя, количество) общей статистики для всех
    имён девочек в указанном году.
    Список должен быть отсортирован по убыванию количества.
    """
    all_people = extract_year(stat, year)
    return [x for x in all_people if re.search(female_regexp, x[0])]


if __name__ == '__main__':
    pass
