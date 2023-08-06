from utils import get_employer_id_from_json_file, HeadHunterAPI


def main():
    hh = HeadHunterAPI()
    filename = 'employers.json'
    ids = get_employer_id_from_json_file(filename)
    data = []
    for i in ids:
        employer_name = hh.get_employer_info(i)['name']
        vacancies_by_employer = hh.get_vacancies_from_employer(i)

        data.append({
            'Компания': employer_name,
            'Вакансии': vacancies_by_employer
        })

    print(data)


if __name__ == '__main__':
    main()
