# Generated by Django 2.1.5 on 2019-05-15 06:34

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('CAT_project', '0007_auto_20190513_0637'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='student_question_result',
            options={'ordering': ['question_num'], 'verbose_name': '学生答题表', 'verbose_name_plural': '学生答题表'},
        ),
    ]