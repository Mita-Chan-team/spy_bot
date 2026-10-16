@echo off
cd /d "%~dp0"

REM Активируем виртуальное окружение и запускаем бота без консольного окна
if exist "venv\Scripts\pythonw.exe" (
    start "" "venv\Scripts\pythonw.exe" main.py
) else (
    start "" pythonw main.py
)

echo Бот запущен в фоне (pythonw).
echo Чтобы остановить - Диспетчер задач → pythonw.exe → Снять задачу.
timeout /t 3 >nul
