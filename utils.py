import json

import requests
import psycopg2
from typing import Any


def get_employer_id_from_json_file(filename: str) -> list:
    """
    Функция для получения списка id работодателей из json-файла.
    """
    with open(filename, encoding='utf-8') as f:
        text = json.load(f)
        ids = []
        for employer in text:
            ids.append(employer['id'])

        return ids


def create_database(database_name: str, params: dict) -> None:
    """
    Создание базы данных и таблиц для сохранения данных о компаниях и вакансиях.
    """
    conn = psycopg2.connect(dbname='postgres', **params)
    conn.autocommit = True
    cur = conn.cursor()

    cur.execute(f'DROP DATABASE {database_name}')
    cur.execute(f'CREATE DATABASE {database_name}')

    cur.close()
    conn.close()

    conn = psycopg2.connect(dbname=database_name, **params)
    with conn.cursor() as cur:
        cur.execute("""
            CREATE TABLE employers (
                employer_id SERIAL PRIMARY KEY,
                title VARCHAR NOT NULL
            )
        """)

    with conn.cursor() as cur:
        cur.execute("""
            CREATE TABLE vacancies (
                vacancy_id SERIAL PRIMARY KEY,
                employer_id INT REFERENCES employers(employer_id),
                title VARCHAR NOT NULL,
                description VARCHAR,
                salary INT,
                vacancy_url TEXT
            )
        """)

    conn.commit()
    conn.close()


def save_data_to_database(data: list[dict[str, Any]], database_name: str, params: dict) -> None:
    """
    Сохранение данных о компаниях и вакансиях в базу данных.
    """
    conn = psycopg2.connect(dbname=database_name, **params)
    with conn.cursor() as cur:
        for employer in data:

            cur.execute(
                """
                INSERT INTO employers (title)
                VALUES (%s)
                RETURNING employer_id
                """,
                (employer['Компания'],)
            )
            employer_id = cur.fetchone()[0]

            for vacancy in employer['Вакансии']:

                cur.execute(
                    """
                    INSERT INTO vacancies (employer_id, title, description, salary, vacancy_url)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (employer_id, vacancy['Наименование'], vacancy['Описание'], vacancy['Зарплата'], vacancy['Ссылка'])
                )

    conn.commit()
    conn.close()


class HeadHunterAPI:
    """
    Класс для получения данных о работодателях и их вакансиях с сайта HeadHunter.
    """
    def get_employers(self, employer_name: str) -> None:
        """
        Метод для поиска работодателей по ключевым словам.
        Поиск производится только по работодателям, имеющим активные вакансии.
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
        """
        Метод для получения информации о компании по ее id
        """
        req = requests.get(f'https://api.hh.ru/employers/{employer_id}')
        data = req.content.decode()
        req.close()

        employer = json.loads(data)

        return employer

    def get_vacancies_from_employer(self, employer_id: int):
        """
        Метод для поиска вакансий от заданного работодателя.
        Поиск производится только по вакансиям, имеющим зарплату.
        """
        page = 0
        vacancies_data = []

        while True:
            params = {
                'employer_id': employer_id,
                'page': page,
                'only_with_salary': True
            }

            req = requests.get('https://api.hh.ru/vacancies', params)
            data = req.content.decode()
            req.close()
            vacancies = json.loads(data)

            if 'pages' in vacancies:
                num_of_pages = vacancies['pages']
            else:
                break

            if page == num_of_pages:
                break

            try:
                for vacancy in vacancies['items']:
                    if vacancy['salary']['to'] is None:
                        vacancy_dict = {
                            'Наименование': vacancy['name'],
                            'Описание': vacancy['snippet']['responsibility'],
                            'Зарплата': vacancy['salary']['from'],
                            'Ссылка': vacancy['alternate_url']
                        }
                    else:
                        vacancy_dict = {
                            'Наименование': vacancy['name'],
                            'Описание': vacancy['snippet']['responsibility'],
                            'Зарплата': vacancy['salary']['to'],
                            'Ссылка': vacancy['alternate_url']
                        }
                    vacancies_data.append(vacancy_dict)
            except KeyError:
                continue

            page += 1

        return vacancies_data


class DBManager:

    def get_companies_and_vacancies_count(self, database_name: str, params: dict):
        """
        Метод для получения списка всех компаний и количества вакансий у каждой компании
        """
        conn = psycopg2.connect(dbname=database_name, **params)
        with conn.cursor() as cur:
            cur.execute("""
                SELECT employers.title AS employer, COUNT(*) AS vacancies_amount
                FROM vacancies
                INNER JOIN employers USING(employer_id)
                GROUP BY employers.title
            """)

        conn.commit()
        conn.close()

    def get_all_vacancies(self, database_name: str, params: dict):
        """
        Метод для получения списка всех вакансий с указанием названия компании,
        названия вакансии и зарплаты и ссылки на вакансию.
        """
        conn = psycopg2.connect(dbname=database_name, **params)
        with conn.cursor() as cur:
            cur.execute("""
                        SELECT employers.title AS employer, vacancies.title, salary, vacancy_url
                        FROM vacancies
                        INNER JOIN employers USING(employer_id)
                    """)

        conn.commit()
        conn.close()

    def get_avg_salary(self, database_name: str, params: dict):
        """
        Метод для получения средней зарплаты по вакансиям.
        """
        conn = psycopg2.connect(dbname=database_name, **params)
        with conn.cursor() as cur:
            cur.execute("""
                        SELECT AVG(salary)
                        FROM vacancies
                    """)

        conn.commit()
        conn.close()

    def get_vacancies_with_higher_salary(self, database_name: str, params: dict):
        """
        Метод для получения списка всех вакансий, у которых зарплата выше средней по всем вакансиям.
        """
        conn = psycopg2.connect(dbname=database_name, **params)
        with conn.cursor() as cur:
            cur.execute("""
                        SELECT title, salary
                        FROM vacancies
                        GROUP BY title, salary
                        HAVING salary > (SELECT AVG(salary) FROM vacancies)
                    """)

        conn.commit()
        conn.close()

    def get_vacancies_with_keyword(self, database_name: str, params: dict, text: str):
        """
        Метод для получения списка всех вакансий, в названии которых содержатся переданные в метод слова.
        """
        conn = psycopg2.connect(dbname=database_name, **params)
        with conn.cursor() as cur:
            cur.execute("""
                        SELECT *
                        FROM vacancies
                        WHERE title LIKE 
                        """ + f"'%{text}%'"
                        )

        conn.commit()
        conn.close()
