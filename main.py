from utils import get_employer_id_from_json_file, HeadHunterAPI, create_database, save_data_to_database, DBManager

from config import config


def main():
    hh = HeadHunterAPI()
    filename = 'employers.json'
    ids = get_employer_id_from_json_file(filename)
    data = []
    database_name = 'headhunter'
    params = config()
    for i in ids:
        employer_name = hh.get_employer_info(i)['name']

        data.append({
            'Компания': employer_name,
            'Вакансии': hh.get_vacancies_from_employer(i)
        })

    create_database(database_name, params)
    save_data_to_database(data, database_name, params)


if __name__ == '__main__':
    main()
