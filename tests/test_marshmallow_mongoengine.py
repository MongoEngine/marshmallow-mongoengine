# -*- coding: utf-8 -*-
from __future__ import absolute_import
import datetime as dt
import decimal
from datetime import datetime

from marshmallow.exceptions import ValidationError
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


class AnotherIntegerField(me.IntField):

    """Use me to test if MRO works like we want"""
    pass


@pytest.fixture()
def models():

    class HeadTeacher(me.EmbeddedDocument):
        full_name = me.StringField(max_length=255, unique=True, default='noname')

    class Course(me.Document):
        id = me.IntField(primary_key=True)
        name = me.StringField()
        # These are for better model form testing
        cost = me.IntField()
        description = me.StringField()
        level = me.StringField(choices=('Primary', 'Secondary'))
        prereqs = me.DictField()
        started = me.DateTimeField()
        grade = AnotherIntegerField()
        students = me.ListField(me.ReferenceField('Student'))

    class School(me.Document):
        name = me.StringField()
        students = me.ListField(me.ReferenceField('Student'))
        headteacher = me.EmbeddedDocumentField(HeadTeacher)

    class Student(me.Document):
        full_name = me.StringField(max_length=255, unique=True, default='noname')
        age = me.IntField(min_value=10, max_value=99)
        dob = me.DateTimeField(null=True)
        date_created = me.DateTimeField(default=dt.datetime.utcnow,
                                        help_text='date the student was created')
        current_school = me.ReferenceField('School')
        courses = me.ListField(me.ReferenceField('Course'))
        email = me.EmailField(max_length=100)
        profile_uri = me.URLField(max_length=200)

    # So that we can access models with dot-notation, e.g. models.Course
    class _models(object):

        def __init__(self):
            self.HeadTeacher = HeadTeacher
            self.Course = Course
            self.School = School
            self.Student = Student
    return _models()


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

    # Again, so we can use dot-notation
    class _schemas(object):

        def __init__(self):
            self.CourseSchema = CourseSchema
            self.SchoolSchema = SchoolSchema
            self.StudentSchema = StudentSchema
    return _schemas()


class TestModelFieldConversion(BaseTest):

    def test_fields_for_model_types(self, models):
        fields_ = fields_for_model(models.Student)
        assert type(fields_['id']) is fields.ObjectId
        assert type(fields_['full_name']) is fields.Str
        assert type(fields_['dob']) is fields.DateTime
        assert type(fields_['current_school']) is fields.Reference
        assert type(fields_['date_created']) is fields.DateTime
        assert type(fields_['email']) is fields.Email
        assert type(fields_['profile_uri']) is fields.URL

    def test_dict_field(self, models):
        fields_ = fields_for_model(models.Course)
        assert type(fields_['prereqs']) is fields.Raw

    def test_embedded_document_field(self, models):
        fields_ = fields_for_model(models.School)
        assert type(fields_['headteacher']) is fields.Nested

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
        validator = contains_validator(fields_['email'], validate.Length)
        assert validator
        assert validator.max == 100
        validator = contains_validator(fields_['profile_uri'], validate.Length)
        assert validator
        assert validator.max == 200
        validator = contains_validator(fields_['age'], validate.Range)
        assert validator
        assert validator.max == 99
        assert validator.min == 10

    def test_sets_allow_none_for_nullable_fields(self, models):
        fields_ = fields_for_model(models.Student)
        assert fields_['dob'].allow_none is True

    def test_sets_enum_choices(self, models):
        fields_ = fields_for_model(models.Course)
        validator = contains_validator(fields_['level'], validate.OneOf)
        assert validator
        assert validator.choices == ('Primary', 'Secondary')

    def test_list_of_references(self, models):
        student_fields = fields_for_model(models.Student)
        assert type(student_fields['courses']) is fields.List
        assert type(student_fields['courses'].container) is fields.Reference

        course_fields = fields_for_model(models.Course)
        assert type(course_fields['students']) is fields.List
        assert type(course_fields['students'].container) is fields.Reference

    def test_reference(self, models):
        student_fields = fields_for_model(models.Student)
        assert type(student_fields['current_school']) is fields.Reference

        course_fields = fields_for_model(models.Course)
        assert type(course_fields['id']) is fields.Int


class TestFieldFor(BaseTest):

    def test_field_for(self, models):
        field = field_for(models.Student, 'full_name')
        assert type(field) == fields.Str

        field = field_for(models.Student, 'current_school')
        assert type(field) == fields.Reference


class TestModelSchema(BaseTest):

    @pytest.fixture
    def school(self, models):
        headteacher = models.HeadTeacher(full_name='John Doe')
        school_ = models.School(name='Univ. Of Whales',
                                headteacher=headteacher).save()
        return school_

    @pytest.fixture
    def student(self, models, school):
        student_ = models.Student(
            full_name='Monty Python',
            age=10,
            dob=datetime.utcnow(),
            current_school=school,
            email='terry.gilliam@montypython.com',
            profile_uri='http://www.imdb.com/name/nm0000416/').save()
        return student_

    @pytest.fixture
    def course(self, models, student):
        course = models.Course(id=4,
                               name='History of painting',
                               cost=100,
                               level='Primary',
                               prereqs={
                                    'age': 15,
                                    'knowledges': ['Painting', 'History'],
                                    'teachers': {
                                        'main': 'Mrs. Kensington',
                                        'assistant': 'Mr. Black'
                                    }
                               },
                               started=datetime(2015, 9, 22),
                               grade=3,
                               students=[student]).save()
        return course

    def test_update(self, schemas, student):
        dob = datetime(1956, 1, 30)
        payload = {'dob': dob.isoformat(), 'age': 59}
        full_name = student.full_name
        result = schemas.StudentSchema().update(student, payload)
        assert result
        assert result is student
        assert student.dob == dob
        assert student.age == 59
        # Make sure default values doesn't mess
        assert student.full_name == full_name

    def test_model_schema_dumping(self, schemas, student):
        schema = schemas.StudentSchema()
        result = schema.dump(student)
        assert result
        for field in ('id', 'full_name', 'age'):
            result.get(field, '<not_set>') == getattr(student, field)
        # related field dumps to pk
        assert result['current_school'] == str(student.current_school.pk)

    def test_model_schema_bad_loading(self, models, schemas, school):
        schema = schemas.StudentSchema()
        default_payload = {'full_name': 'John Doe', 'age': 25, 'dob': None,
                           'date_created': datetime.utcnow().isoformat(),
                           'current_school': school.pk,
                           'email': 'john@doe.com',
                           'profile_uri': 'http://www.perdu.com/'}
        # Make sure default_payload is valid
        result = schema.load(default_payload)
        assert result
        for key, value in (
            ('current_school', 'not an objectId'), ('current_school', None),
            ('current_school', '5578726b7a58012298a5a7e2'),
            ('age', 100), ('age', 'nan'),
            ('email', 'johndoe@badmail'), ('profile_uri', 'bad_uri')
        ):
            payload = default_payload.copy()
            payload[key] = value
            try:
                result = schema.load(payload)
            except ValidationError as err:
                assert err.messages[key]

    def test_model_schema_loading(self, models, schemas, student):
        schema = schemas.StudentSchema()
        dumped_data = schema.dump(student)
        assert dumped_data
        data = schema.load(dumped_data)
        assert data
        assert isinstance(data, models.Student)
        assert data.current_school == student.current_school
        data.age = 25
        data.save()
        student.reload()
        assert student.age == 25

    def test_model_schema_loading_no_load_id(self, models, schemas, student):
        # If specified, we don't load the id from the data
        class NoLoadIdStudentSchema(schemas.StudentSchema):

            class Meta:
                model = models.Student
                model_dump_only_pk = True
        schema = NoLoadIdStudentSchema()
        dumped_data = schema.dump(student)
        assert dumped_data
        # Don't skip id in serialization
        assert dumped_data.get('id', '<not_set>') == str(student.id)
        # Id is autogenerate, thus it cannot be loaded by the unmarshaller
        loaded_data = schema.load(dumped_data)
        assert loaded_data
        assert not loaded_data.id

    def test_model_schema_loading_school(self, models, schemas, school):
        schema = schemas.SchoolSchema()
        dumped_data = schema.dump(school)
        assert dumped_data
        loaded_data = schema.load(dumped_data)
        assert loaded_data
        assert isinstance(loaded_data, models.School)
        # Check embedded document
        assert isinstance(loaded_data.headteacher, models.HeadTeacher)
        assert loaded_data.headteacher.full_name == school.headteacher.full_name

    def test_model_schema_loading_course(self, models, schemas, course):
        schema = schemas.CourseSchema()
        dumped_data = schema.dump(course)
        assert dumped_data
        loaded_data = schema.load(dumped_data)
        assert loaded_data
        assert isinstance(loaded_data, models.Course)
        # Check dict field
        assert isinstance(loaded_data.prereqs, dict)
        assert loaded_data.prereqs == course.prereqs

    def test_fields_option(self, student, models):
        class StudentSchema(ModelSchema):

            class Meta:
                model = models.Student
                fields = ('full_name', 'date_created')

        schema = StudentSchema()
        data = schema.dump(student)
        assert data
        assert 'full_name' in data
        assert 'date_created' in data
        assert 'dob' not in data
        assert 'age' not in data
        assert 'id' not in data
        assert 'email' not in data
        assert 'profile_uri' not in data
        assert len(data.keys()) == 2

    def test_exclude_option(self, student, models):
        class StudentSchema(ModelSchema):

            class Meta:
                model = models.Student
                exclude = ('date_created', )

        schema = StudentSchema()
        data = schema.dump(student)
        assert data
        assert 'full_name' in data
        assert 'id' in data
        assert 'age' in data
        assert 'dob' in data
        assert 'email' in data
        assert 'profile_uri' in data
        assert 'date_created' not in data

    def test_additional_option(self, student, models):
        class StudentSchema(ModelSchema):
            uppername = fields.Function(lambda x: x.full_name.upper())

            class Meta:
                model = models.Student
                additional = ('date_created', )
        schema = StudentSchema()
        data = schema.dump(student)
        assert data
        assert 'full_name' in data
        assert 'uppername' in data
        assert data['uppername'] == student.full_name.upper()

    def test_field_override(self, student, models):
        class MyString(fields.Str):

            def _serialize(self, val, attr, obj):
                return val.upper()

        class StudentSchema(ModelSchema):
            full_name = MyString()

            class Meta:
                model = models.Student
        schema = StudentSchema()
        data = schema.dump(student)
        assert data
        assert 'full_name' in data
        assert data['full_name'] == student.full_name.upper()

    def test_class_inheritance(self, student, models, schemas):
        class CustomStudentSchema(schemas.StudentSchema):
            age = fields.Function(lambda v: 'custom-' + str(v.age))
            custom_field = fields.Function(lambda v: 'custom-field')

            class Meta:
                fields = ('full_name', 'age')
        data = CustomStudentSchema().dump(student)
        assert data
        assert sorted(list(data.keys())) == sorted(['age', 'full_name'])
        assert data['age'] == 'custom-' + str(student.age)

        class ChildCustomStudentSchema(CustomStudentSchema):
            age = fields.Function(lambda v: 'child-custom-' + str(v.age))

            class Meta:
                fields = ('full_name', 'age', 'custom_field')
                model_fields_kwargs = {'full_name': {'load_only': True}}
        data = ChildCustomStudentSchema().dump(student)
        assert data
        assert sorted(list(data.keys())) == sorted(['age', 'custom_field'])
        assert data['age'] == 'child-custom-' + str(student.age)
        assert data['custom_field'] == 'custom-field'

    def test_check_bad_model(self):
        class DummyClass:
            pass
        with pytest.raises(ValueError):
            class BadModelSchema(ModelSchema):

                class Meta:
                    model = DummyClass

    def test_model_schema_custom_skip_values(self, models, schemas):
        student = models.Student(
            full_name='Kevin Smith',
            age=None,
            dob=None,
            date_created=datetime(2016, 2, 14),
            courses=None).save()
        # If specified, we don't load the id from the data
        class CustomSkipValuesStudentSchema(schemas.StudentSchema):
            class Meta:
                model = models.Student
                model_skip_values = (str(student.id), 'Kevin Smith')
                model_fields_kwargs = {'age': {'allow_none': True}}
        schema = CustomSkipValuesStudentSchema()
        assert student.current_school is None
        assert student.dob is None
        dumped_data = schema.dump(student)
        assert dumped_data
        assert dumped_data == {
            'dob': None,
            'age': None,
            'courses': [],
            'date_created': '2016-02-14T00:00:00+00:00',
            'email': None,
            'profile_uri': None
        }
