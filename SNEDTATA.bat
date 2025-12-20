@echo off
set DATABASE_NAME=restored_db
set USER=postgres
set BACKUP_DIR=C:\backups
set EXTERNAL_SSD_DRIVE=F:




set BACKUP_FILE=%BACKUP_DIR%\backup.csv

echo Backing up database %DATABASE_NAME%...

REM Set PGPASSFILE environment variable to point to .pgpass file
set PGPASSFILE=C:\Users\Administrateur\pgpass.conf

"C:\Program Files\PostgreSQL\16\bin\psql.exe" -h localhost -U %USER% -d %DATABASE_NAME% -p 5432 -c "COPY main_produit TO '%BACKUP_FILE%' WITH CSV HEADER;"

py C:/backups/datatoserver.py
endlocal
