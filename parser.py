from classes.database import Database
from bs4 import BeautifulSoup as bs
from requests_futures import sessions
from datetime import datetime
from utils.date_functions import get_dates_list
from utils.default_patterns import TEACHER_ANNOTATIONS, TEACHER_ANNOTATIONS_INVERSED

class Parser():
    def __init__(self, data):
        self.database = Database()
        self.data = data
        self.database_info = self.database.get_note(self.data['chat_id'])

        self.data['mode'] = '1'
        if self.data['type'] == 'teachers':
            self.data['mode'] = '2'

        self.result_value = data['data']
        self.data['data'] = self.remake_value(self.data['data'], self.data['type'], 'parse')

    def remake_value(self, value, _type, mode):
        '''Обработка ошибок сайта'''

        if mode == 'parse':
            if _type == 'groups' and value.startswith('23'):
                temp = self.data['data']
                value = temp[:2] + ' ' + temp[2:]
            elif _type == 'teachers' and value in list(TEACHER_ANNOTATIONS.keys()):
                value = TEACHER_ANNOTATIONS[value]
        elif mode == 'send':
            if _type == 'groups' and value.startswith('23'):
                value = value.replace(' ', '', 1)
            elif _type == 'teachers' and value in list(TEACHER_ANNOTATIONS_INVERSED.keys()):
                value = TEACHER_ANNOTATIONS_INVERSED[value]

        return value

    def sort_auditories_lessons():
        pass

    def transform_result(self, pages_dict):
        self.database_value = self.remake_value(self.result_value, self.data['type'], 'send')
        annotations = {'auditories': 'аудитории', 'groups': 'группы', 'teachers': 'преподавателя'}
        auditory_lessons = list()
        text = f'Расписание для {annotations[self.data["type"]]} {self.database_value}      '

        offset = 2
        if self.data['type'] == 'teachers':
            offset = 0

        mode = 'teachers'
        if self.data['type'] == 'teachers':
            mode = 'groups' 

        for date, pages in pages_dict.items():
            for page in pages:
                lessons = bs(page, 'lxml').find_all('td')
                
                if not len(lessons):
                    continue

                if self.data['type'] != 'auditories':
                    text += f'{date.split("-")[0]}.{date.split("-")[1]} {date.split()[1]}   '
                
                for j in range(offset, len(lessons), 4):
                    if self.data['type'] in ['groups', 'teachers']:
                        text += f'{lessons[j].text}: {lessons[j+1].text} | {lessons[j+2].text} | {self.remake_value(lessons[j+3].text, mode, "send")}   '
                    elif self.data['type'] == 'auditories' and lessons[j+2].text == self.data['data']:
                        auditory_lessons.append(f'{lessons[j].text}: {lessons[j+1].text} | {lessons[1].text} | {lessons[j+3].text}   ')

            if self.data['type'] != 'auditories':
                text += '   '
            else:
                if len(auditory_lessons) == 0:
                    '''СДЕЛАТЬ ОШИБКУ ОТСУТСТВИЯ ПАР'''
                    print('ПАР НЕТ')
                    return
                

                '''СДЕЛАТЬ СОРТИРОВКУ ПО ПОРЯДКУ ПАР'''
                print(auditory_lessons)

        print(text)

        '''ТАКЖЕ НУЖНО СДЕЛАТЬ ОШИБКУ ПАРСИНГА, ЕСЛИ ОТСУТСТВУЮТ ЗНАЧЕНИЯ!!! ПО ДЛИНЕ ТЕКСТА'''
        '''ТУТ НУЖНО ОТПРАВЛЯТЬ СООБЩЕНИЕ ВК И ПОЛУЧАТЬ ЕГО ИДЕНТИФИКАТОР ДЛЯ СОХРАНЕНИЯ В БАЗУ ДАННЫХ'''

        self.database_info[self.data['type']] = self.database_value
        self.database.create_note(self.database_info)

    def parse(self):
        week_day = datetime.weekday(datetime.strptime(self.data['date'], '%d-%m-%Y'))
        if week_day == 6:
            '''СДЕЛАТЬ RAISE WEEKEND_ERROR ДЛЯ ДАЛЬНЕЙШЕЙ ОБРАБОТКИ'''
            return 'ОШИБКА_ВЫХОДНОЙ'
        
        if self.data['type'] == 'auditories':
            self.dates_list = get_dates_list(self.data['date'], week_day, week_day)
        else:
            self.dates_list = get_dates_list(self.data['date'], week_day, 5)
        
        session = sessions.FuturesSession(max_workers = 4)
        
        result_dict = {date: session.post('https://www.uc.osu.ru/back_parametr.php', data = {'type_id': self.data['mode'], 'data': date.split()[0]}).result().json() for date in self.dates_list}
        
        temp_dict = dict()
        try:
            for date, page in result_dict.items():
                if self.data['type'] != 'auditories':
                    key, self.result_value = [[k, v] for k, v in page.items() if self.data['data'] in v][0]
                    key = [key]
                else:
                    key = list(page.keys())
            
                temp_dict[date] = key
            if not temp_dict:
                raise ValueError
        except Exception as e:
            print(e)

        result_dict = dict()

        result_dict = {date: [session.post('https://www.uc.osu.ru/generate_data.php', data = {'type': self.data['mode'], 'data': date.split()[0], 'id': key}).result().text for key in \
            keys] for date, keys in temp_dict.items()}
        
        self.transform_result(result_dict)








days = ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота']

def get_dates_list(date, week_day, edge):
    dates_list = [date + f' {days[week_day]}']
    for i in range(week_day, edge):
        date = return_date(date, 1)
        dates_list.append(date + f' {days[i+1]}')

    return dates_list



'''ОНИ НЕ ПОЛНЫЕ, ДОПИШЕШЬ САМ!!!!'''
TEACHER_ANNOTATIONS = {
    'Лукерина О.А.': 'ЛукеринаО.А.',
}

TEACHER_ANNOTATIONS_INVERSED = {
    'ЛукеринаО.А.': 'Лукерина О.А.',
}
