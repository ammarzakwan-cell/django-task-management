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