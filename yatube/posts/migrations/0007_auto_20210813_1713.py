# Generated by Django 2.2.19 on 2021-08-13 12:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0006_follow'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='comment',
            options={'ordering': ['created']},
        ),
        migrations.AddConstraint(
            model_name='follow',
            constraint=models.UniqueConstraint(fields=('user', 'author'), name='unique_follow'),
        ),
    ]
