# Generated by Django 2.1.5 on 2019-05-13 06:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('CAT_project', '0006_auto_20190504_1457'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user_student',
            name='basetheta',
            field=models.CharField(max_length=256, verbose_name='心理能力值'),
        ),
    ]
