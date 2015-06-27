# -*- coding: utf-8 -*-
from __future__ import absolute_import
import datetime as dt
import decimal
from datetime import datetime

import mongoengine as me

from marshmallow import validate

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


def contains_validator(field, v_type):
    for v in field.validators:
        if isinstance(v, v_type):
            return v
    return False


class TestFields(BaseTest):

    def test_field_files(self):
        class File(me.Document):
            name = me.StringField(primary_key=True)
            file = me.FileField()
        class FileSchema(ModelSchema):
            class Meta:
                model = File
        doc = File(name='test_file')
        data = b'1234567890' * 10
        doc.file.put(data, content_type='application/octet-stream')
        dump = FileSchema().dump(doc)
        assert not dump.errors
        assert dump.data == {'name': 'test_file'}
        # Should not be able to load the file
        load = FileSchema().load({'name': 'bad_load', 'file': b'12345'})
        assert not load.data.file

    def test_field_dict(self):
        class Doc(me.Document):
            data = me.DictField()
        fields_ = fields_for_model(Doc)
        assert type(fields_['data']) is fields.Raw
        class DocSchema(ModelSchema):
            class Meta:
                model = Doc
        data = {
            'int_1': 1,
            'nested_2': {
                'sub_int_1': 42,
                'sub_list_2': []
            },
            'list_3': ['a', 'b', 'c']
        }
        doc = Doc(data=data)
        dump = DocSchema().dump(doc)
        assert not dump.errors
        assert dump.data == {'data': data, 'id': None}
        del dump.data['id']
        load = DocSchema().load(dump.data)
        assert not load.errors
        assert load.data.data == data

    def test_field_dynamic(self):
        class Doc(me.Document):
            dynamic = me.DynamicField()
        fields_ = fields_for_model(Doc)
        assert type(fields_['dynamic']) is fields.Raw
        class DocSchema(ModelSchema):
            class Meta:
                model = Doc
        data = {
            'int_1': 1,
            'nested_2': {
                'sub_int_1': 42,
                'sub_list_2': []
            },
            'list_3': ['a', 'b', 'c']
        }
        doc = Doc(dynamic=data)
        dump = DocSchema().dump(doc)
        assert not dump.errors
        assert dump.data == {'dynamic': data, 'id': None}
        del dump.data['id']
        load = DocSchema().load(dump.data)
        assert not load.errors
        assert load.data.dynamic == data
