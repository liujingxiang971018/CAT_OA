# Generated by Django 2.1.5 on 2019-05-04 05:29

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('CAT_project', '0004_auto_20190504_0526'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='question',
            unique_together={('field', 'question_text')},
        ),
    ]
