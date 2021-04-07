# -*- coding: utf-8 -*-
from __future__ import absolute_import
import datetime as dt
import decimal
from datetime import datetime

import mongoengine as me

from marshmallow import validate, Schema

import pytest
from marshmallow_mongoengine import (fields, fields_for_model, ModelSchema,
                                     ModelConverter, convert_field, field_for)


TEST_DB = 'marshmallow_mongoengine-test'
db = me.connect(TEST_DB)


class BaseTest(object):
    @classmethod
    def setup_method(self, method):
        # Reset database from previous test run
        db.drop_database(TEST_DB)


class TestSkip(BaseTest):

    def test_skip_none_field(self):
        class Doc(me.Document):
            field_not_empty = me.StringField(default='value')
            field_empty = me.StringField()
            list_empty = me.ListField(me.StringField())

        class DocSchema(ModelSchema):
            class Meta:
                model = Doc
        doc = Doc()
        dump_data = DocSchema().dump(doc)
        assert dump_data == {'field_not_empty': 'value'}

    def test_disable_skip_none_field(self):
        class Doc(me.Document):
            field_empty = me.StringField()
            list_empty = me.ListField(me.StringField())

        class DocSchema(ModelSchema):
            class Meta:
                model = Doc
                model_skip_values = ()
        doc = Doc()
        dump_data = DocSchema().dump(doc)
        assert dump_data == {'field_empty': None, 'list_empty': []}
