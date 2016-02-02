# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='EOSCourseDelta',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('queue_id', models.CharField(max_length=30, null=True)),
                ('term_id', models.CharField(max_length=20)),
                ('changed_since_date', models.DateTimeField()),
                ('query_date', models.DateTimeField()),
                ('provisioned_date', models.DateTimeField(null=True)),
            ],
            options={
                'get_latest_by': 'query_date',
            },
            bases=(models.Model,),
        ),
    ]
