# -*- coding: utf-8 -*-
from __future__ import absolute_import
import datetime as dt
import decimal

import mongoengine as me

from marshmallow import fields, validate

import pytest
from marshmallow_mongoengine import (
    fields_for_model, ModelSchema, ModelConverter, convert_field, field_for
)


me.connect('marshmallow_mongoengine-test')


def contains_validator(field, v_type):
    for v in field.validators:
        if isinstance(v, v_type):
            return v
    return False


class AnotherIntegerField(me.IntField):
    """Use me to test if MRO works like we want"""
    pass


@pytest.fixture()
def models():

    # # models adapted from https://github.com/wtforms/wtforms-sqlalchemy/blob/master/tests/tests.py
    # student_course = sa.Table(
    #     'student_course', Base.metadata,
    #     sa.Column('student_id', sa.Integer, sa.ForeignKey('student.id')),
    #     sa.Column('course_id', sa.Integer, sa.ForeignKey('course.id'))
    # )

    class Course(me.Document):
        id = me.IntField(primary_key=True)
        name = me.StringField()
        # These are for better model form testing
        cost = me.IntField()
        description = me.StringField()
        level = me.StringField(choices=('Primary', 'Secondary'))
        has_prereqs = me.BooleanField()
        started = me.DateTimeField()
        grade = AnotherIntegerField()

        @property
        def url(self):
            return '/courses/{}'.format(self.id)

    class School(me.Document):
        name = me.StringField()

        @property
        def url(self):
            return '/schools/{}'.format(self.id)

    class Student(me.Document):
        full_name = me.StringField(max_length=255, unique=True, default='noname')
        dob = me.DateTimeField(null=True)
        date_created = me.DateTimeField(default=dt.datetime.utcnow,
                help_text='date the student was created')
        current_school = me.ReferenceField('School')
        courses = me.ListField(me.ReferenceField('Course'))

        @property
        def url(self):
            return '/students/{}'.format(self.id)

    # So that we can access models with dot-notation, e.g. models.Course
    class _models(object):
        def __init__(self):
            self.Course = Course
            self.School = School
            self.Student = Student
    return _models()


def hyperlink_keygetter(obj):
    return obj.url


@pytest.fixture()
def schemas(models):
    class CourseSchema(ModelSchema):
        class Meta:
            model = models.Course

    class SchoolSchema(ModelSchema):
        class Meta:
            model = models.School

    class StudentSchema(ModelSchema):
        class Meta:
            model = models.Student

    class HyperlinkStudentSchema(ModelSchema):
        class Meta:
            model = models.Student
            keygetter = hyperlink_keygetter

    # Again, so we can use dot-notation
    class _schemas(object):
        def __init__(self):
            self.CourseSchema = CourseSchema
            self.SchoolSchema = SchoolSchema
            self.StudentSchema = StudentSchema
            self.HyperlinkStudentSchema = HyperlinkStudentSchema
    return _schemas()


class TestModelFieldConversion:

    def test_fields_for_model_types(self, models):
        fields_ = fields_for_model(models.Student)
        assert type(fields_['id']) is fields.Str
        assert type(fields_['full_name']) is fields.Str
        assert type(fields_['dob']) is fields.DateTime
        # assert type(fields_['current_school']) is fields.Int
        assert type(fields_['date_created']) is fields.DateTime

    def test_fields_for_model_handles_custom_types(self, models):
        fields_ = fields_for_model(models.Course)
        assert type(fields_['grade']) is fields.Int
        assert type(fields_['id']) is fields.Int

    def test_fields_for_model_saves_doc(self, models):
        fields_ = fields_for_model(models.Student)
        assert fields_['date_created'].metadata['description'] == 'date the student was created'

    def test_length_validator_set(self, models):
        fields_ = fields_for_model(models.Student)
        validator = contains_validator(fields_['full_name'], validate.Length)
        assert validator
        assert validator.max == 255

    def test_sets_allow_none_for_nullable_fields(self, models):
        fields_ = fields_for_model(models.Student)
        assert fields_['dob'].allow_none is True

    def test_sets_enum_choices(self, models):
        fields_ = fields_for_model(models.Course)
        validator = contains_validator(fields_['level'], validate.OneOf)
        assert validator
        assert validator.choices == ('Primary', 'Secondary')

    def test_many_to_many_relationship(self, models):
        student_fields = fields_for_model(models.Student)
        assert type(student_fields['courses']) is fields.QuerySelectList

        course_fields = fields_for_model(models.Course)
        assert type(course_fields['students']) is fields.QuerySelectList

    def test_many_to_one_relationship(self, models):
        student_fields = fields_for_model(models.Student)
        assert type(student_fields['current_school']) is fields.QuerySelect

        school_fields = fields_for_model(models.School)
        assert type(school_fields['students']) is fields.QuerySelectList

    def test_custom_keygetter(self, models):
        student_fields = fields_for_model(
            models.Student,
            keygetter=hyperlink_keygetter
        )
        assert student_fields['current_school'].keygetter == hyperlink_keygetter

    def test_include_fk(self, models):
        student_fields = fields_for_model(models.Student, include_fk=False)
        assert 'current_school_id' not in student_fields

        student_fields2 = fields_for_model(models.Student, include_fk=True)
        assert 'current_school_id' in student_fields2

def make_property(*column_args, **column_kwargs):
    return column_property(sa.Column(*column_args, **column_kwargs))

class TestPropertyFieldConversion:

    @pytest.fixture()
    def converter(self):
        return ModelConverter()

    def test_convert_String(self, converter):
        prop = make_property(sa.String())
        field = converter.convert_field(prop)
        assert type(field) == fields.Str

    def test_convert_Unicode(self, converter):
        prop = make_property(sa.Unicode())
        field = converter.convert_field(prop)
        assert type(field) == fields.Str

    def test_convert_Binary(self, converter):
        prop = make_property(sa.Binary())
        field = converter.convert_field(prop)
        assert type(field) == fields.Str

    def test_convert_LargeBinary(self, converter):
        prop = make_property(sa.LargeBinary())
        field = converter.convert_field(prop)
        assert type(field) == fields.Str

    def test_convert_Text(self, converter):
        prop = make_property(sa.types.Text())
        field = converter.convert_field(prop)
        assert type(field) == fields.Str

    def test_convert_Date(self, converter):
        prop = make_property(sa.Date())
        field = converter.convert_field(prop)
        assert type(field) == fields.Date

    def test_convert_DateTime(self, converter):
        prop = make_property(sa.DateTime())
        field = converter.convert_field(prop)
        assert type(field) == fields.DateTime

    def test_convert_Boolean(self, converter):
        prop = make_property(sa.Boolean())
        field = converter.convert_field(prop)
        assert type(field) == fields.Boolean

    def test_convert_primary_key(self, converter):
        prop = make_property(sa.Integer, primary_key=True)
        field = converter.convert_field(prop)
        assert field.dump_only is True

    def test_convert_Numeric(self, converter):
        prop = make_property(sa.Numeric(scale=2))
        field = converter.convert_field(prop)
        assert type(field) == fields.Decimal
        assert field.places == decimal.Decimal((0, (1,), -2))

    def test_convert_Float(self, converter):
        prop = make_property(sa.Float(scale=2))
        field = converter.convert_field(prop)
        assert type(field) == fields.Float

    def test_convert_SmallInteger(self, converter):
        prop = make_property(sa.SmallInteger())
        field = converter.convert_field(prop)
        assert type(field) == fields.Int

    def test_convert_UUID(self, converter):
        prop = make_property(postgresql.UUID())
        field = converter.convert_field(prop)
        assert type(field) == fields.UUID

    def test_convert_MACADDR(self, converter):
        prop = make_property(postgresql.MACADDR())
        field = converter.convert_field(prop)
        assert type(field) == fields.Str

    def test_convert_INET(self, converter):
        prop = make_property(postgresql.INET())
        field = converter.convert_field(prop)
        assert type(field) == fields.Str

    def test_convert_ARRAY_String(self, converter):
        prop = make_property(postgresql.ARRAY(sa.String()))
        field = converter.convert_field(prop)
        assert type(field) == fields.List
        assert type(field.container) == fields.Str

    def test_convert_ARRAY_Integer(self, converter):
        prop = make_property(postgresql.ARRAY(sa.Integer))
        field = converter.convert_field(prop)
        assert type(field) == fields.List
        assert type(field.container) == fields.Int

class TestPropToFieldClass:

    def convert_test_field(self):
        prop = make_property(sa.Integer())
        field = convert_field(prop, instance=True)

        assert type(field) == fields.Int

        field_cls = convert_field(prop, instance=False)
        assert field_cls == fields.Int

    def test_can_pass_extra_kwargs(self):
        prop = make_property(sa.String())
        field = convert_field(prop, instance=True, description='just a string')
        assert field.metadata['description'] == 'just a string'

class TestColumnToFieldClass:

    def test_column2field(self):
        column = sa.Column(sa.String(255))
        field = column2field(column, instance=True)

        assert type(field) == fields.String

        field_cls = column2field(column, instance=False)
        assert field_cls == fields.String

    def test_can_pass_extra_kwargs(self):
        column = sa.Column(sa.String(255))
        field = column2field(column, instance=True, description='just a string')
        assert field.metadata['description'] == 'just a string'

class TestFieldFor:

    def test_field_for(self, models):
        field = field_for(models.Student, 'full_name')
        assert type(field) == fields.Str

        field = field_for(models.Student, 'current_school')
        assert type(field) == fields.QuerySelect

class TestModelSchema:

    @pytest.fixture()
    def school(self, models, session):
        school_ = models.School(name='Univ. Of Whales')
        session.add(school_)
        return school_

    @pytest.fixture()
    def student(self, models, school, session):
        student_ = models.Student(full_name='Monty Python', current_school=school)
        session.add(student_)
        return student_

    def test_model_schema_dumping(self, schemas, student, session):
        session.commit()
        schema = schemas.StudentSchema()
        result = schema.dump(student)
        # fk excluded by default
        assert 'current_school_id' not in result.data
        # related field dumps to pk
        assert result.data['current_school'] == student.current_school.id

    def test_model_schema_overridden_keygeter(self, schemas, student, session):
        session.commit()
        schema = schemas.HyperlinkStudentSchema()
        result = schema.dump(student)
        assert result.data['current_school'] == student.current_school.url

    def test_model_schema_loading(self, models, schemas, student, session):
        session.commit()
        schema = schemas.StudentSchema()
        dump_data = schema.dump(student).data
        result = schema.load(dump_data)

        assert type(result.data) == models.Student
        assert result.data.id is None

    def test_fields_option(self, student, models, session):
        class StudentSchema(ModelSchema):
            class Meta:
                model = models.Student
                sqla_session = session
                fields = ('full_name', 'date_created')

        session.commit()
        schema = StudentSchema()
        data, errors = schema.dump(student)

        assert 'full_name' in data
        assert 'date_created' in data
        assert 'dob' not in data
        assert len(data.keys()) == 2

    def test_exclude_option(self, student, models, session):
        class StudentSchema(ModelSchema):
            class Meta:
                model = models.Student
                sqla_session = session
                exclude = ('date_created', )

        session.commit()
        schema = StudentSchema()
        data, errors = schema.dump(student)

        assert 'full_name' in data
        assert 'date_created' not in data

    def test_additional_option(self, student, models, session):
        class StudentSchema(ModelSchema):
            uppername = fields.Function(lambda x: x.full_name.upper())

            class Meta:
                model = models.Student
                sqla_session = session
                additional = ('date_created', )

        session.commit()
        schema = StudentSchema()
        data, errors = schema.dump(student)
        assert 'full_name' in data
        assert 'uppername' in data
        assert data['uppername'] == student.full_name.upper()

    def test_field_override(self, student, models, session):
        class MyString(fields.Str):
            def _serialize(self, val, attr, obj):
                return val.upper()

        class StudentSchema(ModelSchema):
            full_name = MyString()

            class Meta:
                model = models.Student
                sqla_session = session

        session.commit()
        schema = StudentSchema()
        data, errors = schema.dump(student)
        assert 'full_name' in data
        assert data['full_name'] == student.full_name.upper()
