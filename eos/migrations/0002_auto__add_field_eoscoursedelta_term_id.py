# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'EOSCourseDelta.term_id'
        db.add_column(u'eos_eoscoursedelta', 'term_id',
                      self.gf('django.db.models.fields.CharField')(default='2015-autumn', max_length=20),
                      keep_default=False)


    def backwards(self, orm):
        # Deleting field 'EOSCourseDelta.term_id'
        db.delete_column(u'eos_eoscoursedelta', 'term_id')


    models = {
        u'eos.eoscoursedelta': {
            'Meta': {'object_name': 'EOSCourseDelta'},
            'changed_since_date': ('django.db.models.fields.DateTimeField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'provisioned_date': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'query_date': ('django.db.models.fields.DateTimeField', [], {}),
            'queue_id': ('django.db.models.fields.CharField', [], {'max_length': '30', 'null': 'True'}),
            'term_id': ('django.db.models.fields.CharField', [], {'max_length': '20'})
        }
    }

    complete_apps = ['eos']