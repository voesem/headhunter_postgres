import json

import requests


def get_employer_id_from_json_file(filename: str) -> list:
    """
    Функция для получения списка id работодателей из json-файла.

    :param filename: Файл с наименованиями и id работодателей, поиск вакансий
    которых будет осуществляться далее
    :return: Список id
    """
    with open(filename, encoding='utf-8') as f:
        text = json.load(f)
        ids = []
        for employer in text:
            ids.append(employer['id'])

        return ids


class HeadHunterAPI:
    """
    Класс для получения данных о работодателях и их вакансиях с сайта HeadHunter.
    """

    def get_employers(self, employer_name: str) -> None:
        """
        Метод для поиска работодателей по ключевым словам.
        Поиск производится только по работодателям, имеющим активные вакансии.

        :param employer_name: Ключевые слова для поиска
        """
        params = {
            'text': employer_name,
            'only_with_vacancies': True
        }

        req = requests.get('https://api.hh.ru/employers', params)
        data = req.content.decode()
        req.close()

        employers = json.loads(data)

        print(employers)

    def get_employer_info(self, employer_id: int):
        req = requests.get(f'https://api.hh.ru/employers/{employer_id}')
        data = req.content.decode()
        req.close()

        employer = json.loads(data)

        return employer

    def get_vacancies_from_employer(self, employer_id: int):
        """
        Метод для поиска вакансий от заданного работодателя.
        Поиск производится только по вакансиям, размещенным в России и имеющим зарплату.

        :param employer_id: Id работодателя
        """
        page = 0
        vacancies_data = []
        params = {
            'employer_id': employer_id,
            'page': page,
            'area': 113,
            'only_with_salary': True
        }

        req = requests.get('https://api.hh.ru/vacancies', params)
        data = req.content.decode()
        req.close()
        vacancies = json.loads(data)

        num_of_pages = vacancies['pages']

        for i in range(num_of_pages):
            req = requests.get('https://api.hh.ru/vacancies', params)
            data = req.content.decode()
            req.close()
            vacancies = json.loads(data)

            vacancies_data.extend(vacancies['items'])

        return vacancies_data
