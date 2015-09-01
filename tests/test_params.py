# -*- coding: utf-8 -*-
from __future__ import absolute_import
import datetime as dt
import decimal
from datetime import datetime

import mongoengine as me

import pytest
from marshmallow_mongoengine import ModelSchema


TEST_DB = 'marshmallow_mongoengine-test'
db = me.connect(TEST_DB)


class BaseTest(object):
    @classmethod
    def setup_method(self, method):
        # Reset database from previous test run
        db.drop_database(TEST_DB)


class TestParams(BaseTest):

    def test_required(self):
        class Doc(me.Document):
            field_not_required = me.StringField()
            field_required = me.StringField(required=True)
        class DocSchema(ModelSchema):
            class Meta:
                model = Doc
        doc, errors = DocSchema().load({'field_not_required': 'bad_doc'})
        assert errors
        # Now provide the required field
        doc, errors = DocSchema().load({'field_required': 'good_doc'})
        assert not errors
        assert doc.field_not_required is None
        assert doc.field_required == 'good_doc'
        # Update should not take care of the required fields
        doc, errors = DocSchema().update(doc, {'field_not_required': 'good_doc'})
        assert not errors
        assert doc.field_required == 'good_doc'
        assert doc.field_not_required == 'good_doc'

    def test_default(self):
        def generate_default_value():
            return 'default_generated_value'
        class Doc(me.Document):
            field_with_default = me.StringField(default='default_value')
            field_required_with_default = me.StringField(required=True,
                default=generate_default_value)
        class DocSchema(ModelSchema):
            class Meta:
                model = Doc
        # Make sure default doesn't shadow given values
        doc, errors = DocSchema().load({'field_with_default': 'custom_value',
                                        'field_required_with_default': 'custom_value'})
        assert not errors
        assert doc.field_with_default == 'custom_value'
        assert doc.field_required_with_default == 'custom_value'
        # Now use defaults
        doc, errors = DocSchema().load({})
        assert not errors
        assert doc.field_with_default == 'default_value'
        assert doc.field_required_with_default == 'default_generated_value'
