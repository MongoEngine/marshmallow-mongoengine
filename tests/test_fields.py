# -*- coding: utf-8 -*-
from __future__ import absolute_import
import datetime as dt
import decimal
from datetime import datetime

import mongoengine as me

from marshmallow import validate, Schema
from marshmallow.exceptions import ValidationError

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

    def test_FileField(self):
        class File(me.Document):
            name = me.StringField(primary_key=True)
            file = me.FileField()
        class FileSchema(ModelSchema):
            class Meta:
                model = File
        doc = File(name='test_file')
        data = b'1234567890' * 10
        doc.file.put(data, content_type='application/octet-stream')
        dumped_data = FileSchema().dump(doc)
        assert dumped_data
        assert dumped_data == {'name': 'test_file'}
        # Should not be able to load the file
        loaded_data = FileSchema().load({'name': 'bad_load', 'file': b'12345'})
        assert not loaded_data.file

    def test_ListField(self):
        class Doc(me.Document):
            list = me.ListField(me.StringField())
        fields_ = fields_for_model(Doc)
        assert type(fields_['list']) is fields.List
        class DocSchema(ModelSchema):
            class Meta:
                model = Doc
        list_ = ['A', 'B', 'C']
        doc = Doc(list=list_)
        dumped_data = DocSchema().dump(doc)
        assert dumped_data
        assert dumped_data == {'list': list_}
        loaded_data = DocSchema().load(dumped_data)
        assert loaded_data
        assert loaded_data.list == list_

    def test_ListSpecialField(self):
        class NestedDoc(me.EmbeddedDocument):
            field = me.StringField()
        class Doc(me.Document):
            list = me.ListField(me.EmbeddedDocumentField(NestedDoc))
        fields_ = fields_for_model(Doc)
        assert type(fields_['list']) is fields.List
        assert type(fields_['list'].container) is fields.Nested
        class DocSchema(ModelSchema):
            class Meta:
                model = Doc
        list_ = [{'field': 'A'}, {'field': 'B'}, {'field': 'C'}]
        doc = Doc(list=list_)
        dumped_data = DocSchema().dump(doc)
        assert dumped_data
        assert dumped_data == {'list': list_}
        loaded_data = DocSchema().load(dumped_data)
        assert loaded_data
        for i, elem in enumerate(list_):
            assert loaded_data.list[i].field == elem['field']

    def test_DictField(self):
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
        dumped_data = DocSchema().dump(doc)
        assert dumped_data
        assert dumped_data == {'data': data}
        loaded_data = DocSchema().load(dumped_data)
        assert loaded_data
        assert loaded_data.data == data

    def test_DynamicField(self):
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
        dumped_data = DocSchema().dump(doc)
        assert dumped_data
        assert dumped_data == {'dynamic': data}
        loaded_data = DocSchema().load(dumped_data)
        assert loaded_data
        assert loaded_data.dynamic == data

    def test_GenericReferenceField(self):
        class Doc(me.Document):
            id = me.StringField(primary_key=True, default='main')
            generic = me.GenericReferenceField()
        class SubDocA(me.Document):
            field_a = me.StringField(primary_key=True, default='doc_a_pk')
        class SubDocB(me.Document):
            field_b = me.IntField(primary_key=True, default=42)
        fields_ = fields_for_model(Doc)
        assert type(fields_['generic']) is fields.GenericReference
        class DocSchema(ModelSchema):
            class Meta:
                model = Doc
        # Test dump
        sub_doc_a = SubDocA().save()
        sub_doc_b = SubDocB().save()
        doc = Doc(generic=sub_doc_a)
        dumped_data = DocSchema().dump(doc)
        assert dumped_data
        assert dumped_data == {'generic': 'doc_a_pk', 'id': 'main'}
        doc.generic = sub_doc_b
        doc.save()
        dumped_data = DocSchema().dump(doc)
        assert dumped_data
        assert dumped_data == {'generic': 42, 'id': 'main'}
        # Test load
        for bad_generic in (
                {'id': str(sub_doc_a.id)}, {'_cls': sub_doc_a._class_name},
                {'id': str(sub_doc_a.id), '_cls': sub_doc_b._class_name},
                {'id': 'not_an_id', '_cls': sub_doc_a._class_name},
                {'id': 42, '_cls': sub_doc_a._class_name},
                {'id': 'main', '_cls': sub_doc_b._class_name},
                {'id': str(sub_doc_a.id), '_cls': 'not_a_class'},
                {'id': None, '_cls': sub_doc_a._class_name},
                {'id': str(sub_doc_a.id), '_cls': None},
            ):
            try:
                loaded_data = DocSchema().load({"generic": bad_generic})
            except ValidationError as err:
                loaded_data = None
            assert not loaded_data

        loaded_data = DocSchema().load({"generic": {"id": str(sub_doc_a.id),
                                             "_cls": sub_doc_a._class_name}})
        assert loaded_data
        assert loaded_data['generic'] == sub_doc_a
        loaded_data = DocSchema().load({"generic": {"id": str(sub_doc_b.id),
                                             "_cls": sub_doc_b._class_name}})
        assert loaded_data
        assert loaded_data['generic'] == sub_doc_b
        # Teste choices param
        class DocOnlyA(me.Document):
            id = me.StringField(primary_key=True, default='main')
            generic = me.GenericReferenceField(choices=[SubDocA])
        class DocOnlyASchema(ModelSchema):
            class Meta:
                model = DocOnlyA
        loaded_data = DocOnlyASchema().load({})
        assert loaded_data
        loaded_data = DocOnlyASchema().load({"generic": {"id": str(sub_doc_a.id),
                                                  "_cls": sub_doc_a._class_name}})
        assert loaded_data
        assert loaded_data['generic'] == sub_doc_a
        try:
            loaded_data = DocOnlyASchema().load({"generic": {"id": str(sub_doc_b.id),
                                                      "_cls": sub_doc_b._class_name}})
        except ValidationError as err:
            loaded_data = None
        assert not loaded_data

    @pytest.mark.skipif(
        not hasattr(me, 'GenericLazyReferenceField'),
        reason='GenericLazyReferenceField requires mongoengine>=0.15.0')
    def test_GenericLazyReferenceField(self):
        class Doc(me.Document):
            id = me.StringField(primary_key=True, default='main')
            generic = me.GenericLazyReferenceField()
        class SubDocA(me.Document):
            field_a = me.StringField(primary_key=True, default='doc_a_pk')
        class SubDocB(me.Document):
            field_b = me.IntField(primary_key=True, default=42)
        fields_ = fields_for_model(Doc)
        assert type(fields_['generic']) is fields.GenericReference
        class DocSchema(ModelSchema):
            class Meta:
                model = Doc
        # Test dump
        sub_doc_a = SubDocA().save()
        sub_doc_b = SubDocB().save()
        doc = Doc(generic=sub_doc_a)
        dumped_data = DocSchema().dump(doc)
        assert dumped_data
        assert dumped_data == {'generic': 'doc_a_pk', 'id': 'main'}
        doc.generic = sub_doc_b
        doc.save()
        dumped_data = DocSchema().dump(doc)
        assert dumped_data
        assert dumped_data == {'generic': 42, 'id': 'main'}
        # Test load
        for bad_generic in (
                {'id': str(sub_doc_a.id)}, {'_cls': sub_doc_a._class_name},
                {'id': str(sub_doc_a.id), '_cls': sub_doc_b._class_name},
                {'id': 'not_an_id', '_cls': sub_doc_a._class_name},
                {'id': 42, '_cls': sub_doc_a._class_name},
                {'id': 'main', '_cls': sub_doc_b._class_name},
                {'id': str(sub_doc_a.id), '_cls': 'not_a_class'},
                {'id': None, '_cls': sub_doc_a._class_name},
                {'id': str(sub_doc_a.id), '_cls': None},
            ):
            try:
                loaded_data = DocSchema().load({"generic": bad_generic})
            except ValidationError as err:
                loaded_data = None
            assert not loaded_data

        loaded_data = DocSchema().load({"generic": {"id": str(sub_doc_a.id),
                                             "_cls": sub_doc_a._class_name}})
        assert loaded_data
        assert loaded_data['generic'] == sub_doc_a
        loaded_data = DocSchema().load({"generic": {"id": str(sub_doc_b.id),
                                             "_cls": sub_doc_b._class_name}})
        assert loaded_data
        assert loaded_data['generic'] == sub_doc_b
        # Teste choices param
        class DocOnlyA(me.Document):
            id = me.StringField(primary_key=True, default='main')
            generic = me.GenericLazyReferenceField(choices=[SubDocA])
        class DocOnlyASchema(ModelSchema):
            class Meta:
                model = DocOnlyA
        loaded_data = DocOnlyASchema().load({})
        assert loaded_data
        loaded_data = DocOnlyASchema().load({"generic": {"id": str(sub_doc_a.id),
                                                  "_cls": sub_doc_a._class_name}})
        assert loaded_data
        assert loaded_data['generic'] == sub_doc_a
        try:
            loaded_data = DocOnlyASchema().load({"generic": {"id": str(sub_doc_b.id),
                                                      "_cls": sub_doc_b._class_name}})
        except ValidationError as err:
            loaded_data = None
        assert not loaded_data

    def test_GenericEmbeddedDocumentField(self):
        class Doc(me.Document):
            id = me.StringField(primary_key=True, default='main')
            embedded = me.GenericEmbeddedDocumentField()
        class EmbeddedA(me.EmbeddedDocument):
            field_a = me.StringField(default='field_a_value')
        class EmbeddedB(me.EmbeddedDocument):
            field_b = me.IntField(default=42)
        fields_ = fields_for_model(Doc)
        assert type(fields_['embedded']) is fields.GenericEmbeddedDocument
        class DocSchema(ModelSchema):
            class Meta:
                model = Doc
        doc = Doc(embedded=EmbeddedA())
        dumped_data = DocSchema().dump(doc)
        assert dumped_data
        assert dumped_data == {'embedded': {'field_a': 'field_a_value'}, 'id': 'main'}
        doc.embedded = EmbeddedB()
        doc.save()
        dumped_data = DocSchema().dump(doc)
        assert dumped_data
        assert dumped_data == {'embedded': {'field_b': 42}, 'id': 'main'}
        # TODO: test load ?

    def test_MapField(self):
        class MappedDoc(me.EmbeddedDocument):
            field = me.StringField()
        class Doc(me.Document):
            id = me.IntField(primary_key=True, default=1)
            map = me.MapField(me.EmbeddedDocumentField(MappedDoc))
            str = me.MapField(me.StringField())
        fields_ = fields_for_model(Doc)
        assert type(fields_['map']) is fields.Map
        class DocSchema(ModelSchema):
            class Meta:
                model = Doc
        doc = Doc(map={'a': MappedDoc(field='A'), 'b': MappedDoc(field='B')},
                  str={'a': 'aaa', 'b': 'bbbb'}).save()
        dumped_data = DocSchema().dump(doc)
        assert dumped_data
        assert dumped_data == {
            'map': {'a': {'field': 'A'}, 'b': {'field': 'B'}},
            'str': {'a': 'aaa', 'b': 'bbbb'}, 'id': 1
        }
        # Try the load
        loaded_data = DocSchema().load(dumped_data)
        assert loaded_data
        assert loaded_data.map == doc.map

    def test_ReferenceField(self):
        class ReferenceDoc(me.Document):
            field = me.IntField(primary_key=True, default=42)
        class Doc(me.Document):
            id = me.StringField(primary_key=True, default='main')
            ref = me.ReferenceField(ReferenceDoc)
        fields_ = fields_for_model(Doc)
        assert type(fields_['ref']) is fields.Reference
        class DocSchema(ModelSchema):
            class Meta:
                model = Doc
        ref_doc = ReferenceDoc().save()
        doc = Doc(ref=ref_doc)
        dumped_data = DocSchema().dump(doc)
        assert dumped_data
        assert dumped_data == {'ref': 42, 'id': 'main'}
        # Try the same with reference document type passed as string
        class DocSchemaRefAsString(Schema):
            id = fields.String()
            ref = fields.Reference('ReferenceDoc')
        dumped_data = DocSchemaRefAsString().dump(doc)
        assert dumped_data
        assert dumped_data == {'ref': 42, 'id': 'main'}
        # Test the field loading
        loaded_data = DocSchemaRefAsString().load(dumped_data)
        assert loaded_data
        assert isinstance(loaded_data['ref'], ReferenceDoc)
        # Try invalid loads
        for bad_ref in (1, 'NaN', None):
            try:
                dumped_data['ref'] = bad_ref
                loaded_data = DocSchemaRefAsString().load(dumped_data)
            except ValidationError as err:
                loaded_data = None
            assert loaded_data is None

    @pytest.mark.skipif(
        not hasattr(me, 'LazyReferenceField'),
        reason='LazyReferenceField requires mongoengine>=0.15.0')
    def test_LazyReferenceField(self):
        class ReferenceDoc(me.Document):
            field = me.IntField(primary_key=True, default=42)
        class Doc(me.Document):
            id = me.StringField(primary_key=True, default='main')
            ref = me.LazyReferenceField(ReferenceDoc)
        fields_ = fields_for_model(Doc)
        assert type(fields_['ref']) is fields.Reference
        class DocSchema(ModelSchema):
            class Meta:
                model = Doc
        ref_doc = ReferenceDoc().save()
        doc = Doc(ref=ref_doc)
        dumped_data = DocSchema().dump(doc)
        assert dumped_data
        assert dumped_data == {'ref': 42, 'id': 'main'}
        # Force ref field to be LazyReference
        doc.save()
        doc.reload()
        dumped_data = DocSchema().dump(doc)
        assert dumped_data
        assert dumped_data == {'ref': 42, 'id': 'main'}
        # Try the same with reference document type passed as string
        class DocSchemaRefAsString(Schema):
            id = fields.String()
            ref = fields.Reference('ReferenceDoc')
        dumped_data = DocSchemaRefAsString().dump(doc)
        assert dumped_data
        assert dumped_data == {'ref': 42, 'id': 'main'}
        # Test the field loading
        loaded_data = DocSchemaRefAsString().load(dumped_data)
        assert loaded_data
        assert isinstance(loaded_data['ref'], ReferenceDoc)
        # Try invalid loads
        for bad_ref in (1, 'NaN', None):
            try:
                dumped_data['ref'] = bad_ref
                loaded_data = DocSchemaRefAsString().load(dumped_data)
            except ValidationError as err:
                loaded_data = None
            assert loaded_data is None

    def test_PointField(self):
        class Doc(me.Document):
            point = me.PointField()
        class DocSchema(ModelSchema):
            class Meta:
                model = Doc
        doc = Doc(point={ 'type': 'Point', 'coordinates': [10, 20] })
        dumped_data = DocSchema().dump(doc)
        assert dumped_data
        assert dumped_data['point'] == { 'x': 10, 'y': 20 }
        load = DocSchema().load(dumped_data)
        assert load
        assert load.point == { 'type': 'Point', 'coordinates': [10, 20] }
        # Deserialize Point with coordinates passed as string
        data = {'point': { 'x': '10', 'y': '20' }}
        loaded_data = DocSchema().load(data)
        assert loaded_data
        assert loaded_data.point == { 'type': 'Point', 'coordinates': [10, 20] }
        # Try to load invalid coordinates
        data = {'point': { 'x': '10', 'y': '20foo' }}
        try:
            loaded_data = DocSchema().load(data)
        except ValidationError as err:
            loaded_data = None
        assert loaded_data is None
