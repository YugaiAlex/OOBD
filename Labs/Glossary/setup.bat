@echo off

REM Разрешить выполнение сценариев только для текущего процесса
powershell -Command "Set-ExecutionPolicy Bypass -Scope Process -Force"

REM Активировать существующее виртуальное окружение
call venv\Scripts\activate

REM Установить зависимости
pip install -r requirements.txt

REM Запустить Flask-приложение
flask run