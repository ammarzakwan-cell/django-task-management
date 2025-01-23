from django.contrib.auth.models import Group, Permission, User
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