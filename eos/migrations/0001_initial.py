# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'EOSCourseDelta'
        db.create_table(u'eos_eoscoursedelta', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('queue_id', self.gf('django.db.models.fields.CharField')(max_length=30, null=True)),
            ('changed_since_date', self.gf('django.db.models.fields.DateTimeField')()),
            ('query_date', self.gf('django.db.models.fields.DateTimeField')()),
            ('provisioned_date', self.gf('django.db.models.fields.DateTimeField')(null=True)),
        ))
        db.send_create_signal(u'eos', ['EOSCourseDelta'])


    def backwards(self, orm):
        # Deleting model 'EOSCourseDelta'
        db.delete_table(u'eos_eoscoursedelta')


    models = {
        u'eos.eoscoursedelta': {
            'Meta': {'object_name': 'EOSCourseDelta'},
            'changed_since_date': ('django.db.models.fields.DateTimeField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'provisioned_date': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'query_date': ('django.db.models.fields.DateTimeField', [], {}),
            'queue_id': ('django.db.models.fields.CharField', [], {'max_length': '30', 'null': 'True'})
        }
    }

    complete_apps = ['eos']