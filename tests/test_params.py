# -*- coding: utf-8 -*-
from __future__ import absolute_import
import datetime as dt
import decimal
from datetime import datetime

from marshmallow.exceptions import ValidationError
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
        try:
            doc = DocSchema().load({'field_not_required': 'bad_doc'})
        except ValidationError as err:
            assert err.messages == {'field_required': ['Missing data for required field.']}

        # Now provide the required field
        doc = DocSchema().load({'field_required': 'good_doc'})
        assert doc
        assert doc.field_not_required is None
        assert doc.field_required == 'good_doc'
        # Update should not take care of the required fields
        doc = DocSchema().update(doc, {'field_not_required': 'good_doc'})
        assert doc
        assert doc.field_required == 'good_doc'
        assert doc.field_not_required == 'good_doc'

    def test_required_with_default(self):
        class Doc(me.Document):
            basic = me.IntField(required=True, default=42)
            cunning = me.BooleanField(required=True, default=False)
        class DocSchema(ModelSchema):
            class Meta:
                model = Doc
        doc = DocSchema().load({})
        assert doc
        assert doc.basic == 42
        assert doc.cunning is False

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
        doc = DocSchema().load({'field_with_default': 'custom_value',
                                'field_required_with_default': 'custom_value'})
        assert doc
        assert doc.field_with_default == 'custom_value'
        assert doc.field_required_with_default == 'custom_value'
        # Now use defaults
        doc = DocSchema().load({})
        assert doc
        assert doc.field_with_default == 'default_value'
        assert doc.field_required_with_default == 'default_generated_value'

    def test_choices(self):
        class Doc(me.Document):
            CHOICES = (
                (0, 'zero'),
                (1, 'one'),
            )
            basic = me.IntField(choices=CHOICES)

        class DocSchema(ModelSchema):
            class Meta:
                model = Doc
        try:
            doc = DocSchema().load({'basic': 0})
        except ValidationError as err:
            err.messages == {'basic': 0}

        try:
            doc = DocSchema().load({'basic': 3})
        except ValidationError as err:
            err.messages == {'basic': ['Not a valid choice.']}

    def test_regex(self):
        class Doc(me.Document):
            basic = me.StringField(regex=r'^[1-9]{6}$')

        class DocSchema(ModelSchema):
            class Meta:
                model = Doc

        doc = DocSchema().load({'basic': '112233'})
        assert doc
        assert doc.basic == '112233'

        try:
            doc = DocSchema().load({'basic': '1A2B3CDD'})
        except ValidationError as err:
            err.messages == {'basic': ['String does not match expected pattern.']}
