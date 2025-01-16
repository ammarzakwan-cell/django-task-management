# Project Setup
## Setup Environment
```pip install virtualenv
pip install virtualenv
python -m venv venv
Set-ExecutionPolicy Unrestricted -Scope Process
env/Scripts/Activate.ps1
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
### setup user
run in shell
> python manage.py shell
```
from django.contrib.auth.models import User
from django.utils.timezone import now


users = [
    {"username": "user1", "password": "password1", "email": "user1@example.com"},
    {"username": "user2", "password": "password2", "email": "user2@example.com"},
    {"username": "user3", "password": "password3", "email": "user3@example.com"},
    {"username": "user4", "password": "password4", "email": "user4@example.com"},
    {"username": "user5", "password": "password5", "email": "user5@example.com"},
    {"username": "user6", "password": "password6", "email": "user6@example.com"},
]

for user_data in users:
    User.objects.create_user(
        username=user_data["username"],
        password=user_data["password"],
        email=user_data["email"],
        is_active=True,
        date_joined=now(),
    )
```

### setup groups (not tested)
```
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from modules.task.models import Task

# Create groups
maker_group, created = Group.objects.get_or_create(name='maker')
checker_group, created = Group.objects.get_or_create(name='checker')

# Get the content type for the Task model
task_content_type = ContentType.objects.get_for_model(Task)

# Permissions for 'maker' group
permissions_maker = [
    Permission.objects.get(codename='add_task', content_type=task_content_type),
    Permission.objects.get(codename='change_task', content_type=task_content_type),
    Permission.objects.get(codename='delete_task', content_type=task_content_type),
    Permission.objects.get(codename='view_task', content_type=task_content_type),
]

# Permissions for 'checker' group
permissions_checker = [
    Permission.objects.get(codename='change_task', content_type=task_content_type),
    Permission.objects.get(codename='view_task', content_type=task_content_type),
]

# Add permissions to groups
maker_group.permissions.set(permissions_maker)
checker_group.permissions.set(permissions_checker)

```

### assign groups to user
```
from django.contrib.auth.models import User

# Assign users to groups
user1 = User.objects.get(username='user1')
user2 = User.objects.get(username='user2')
user3 = User.objects.get(username='user3')
user4 = User.objects.get(username='user4')
user5 = User.objects.get(username='user5')
user6 = User.objects.get(username='user6')

# Add users to 'maker' group
maker_group.user_set.add(user1, user2)

# Add users to 'checker' group
checker_group.user_set.add(user3, user4, user5, user6)

```
