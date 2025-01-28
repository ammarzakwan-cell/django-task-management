# Project Setup
## Setup Environment
```pip install virtualenv
pip install virtualenv
python -m venv venv
Set-ExecutionPolicy Unrestricted -Scope Process
venv/Scripts/Activate.ps1
```

## Install requirements
```
pip install -r requirements.txt
```

## Migrations

### create table task_locking
field = id=PK, task_id=BIGINT, is_locked=BOOLEAN, loacked_at=DATETIME
create table.
```
// SQL
CREATE TABLE task_locking (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    task_id BIGINT NOT NULL,
    is_locked BOOLEAN NOT NULL DEFAULT FALSE,
    locked_at DATETIME DEFAULT NULL
);
```

### run migration
```
python manage.py makemigrations
python manage.py migrate
```

## Seeder
```
// goto seed folder
cd seed

// run user_seeder.py to setup user
python user_seeder.py

// run group_seeder.py to setup group and assign to user
python group_seeder.py
```

