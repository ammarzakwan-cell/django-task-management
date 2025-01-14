# Generated by Django 5.1.4 on 2025-01-14 14:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('task', '0003_remove_logging_is_lock_logging_is_locked_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='Locking',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('task_id', models.BigIntegerField()),
                ('is_locked', models.BooleanField(default=False)),
                ('locked_at', models.DateTimeField(blank=True, null=True)),
            ],
            options={
                'db_table': 'task_locking',
                'managed': False,
            },
        ),
        migrations.DeleteModel(
            name='Logging',
        ),
    ]
