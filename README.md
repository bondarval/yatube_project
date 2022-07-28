# Проект Yatube
### Описание
Благодаря этому проекту зарегристрированные пользователи получат возможность опубликовать личные дневники, подписаться на авторов других дневников и комментировать их записи.
### Технологии
- Python 3.7
- Django 2.2.19
- PyTest
- Pillow
### Инструкции по запуску
- Установить и активировать виртуальное окружение
```bash
python -m venv venv
source venv/Scripts/activate
``` 
- Установить зависимости из файла requirements.txt
```bash
pip install -r requirements.txt
``` 
- В папке с файлом manage.py выполнить последовательность команд:
```bash
python manage.py makemigrations
python manage.py migrate
python manage.py collectstatic
```
- Для запуска сервера разработчика выполнить команду:
```bash
python manage.py runserver
```
### Автор
Валерий А. Бондарь