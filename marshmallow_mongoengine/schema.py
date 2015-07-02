# -*- coding: utf-8 -*-
import inspect

from mongoengine.base import BaseDocument
import marshmallow as ma
from marshmallow.compat import with_metaclass
from marshmallow_mongoengine.convert import ModelConverter


class SchemaOpts(ma.SchemaOpts):
    """Options class for `ModelSchema`.
    Adds the following options:

    - ``model``: The Mongoengine Document model to generate the `Schema`
        from (required).
    - ``model_fields_kwargs``: Dict of {field: kwargs} to provide as
        additionals argument during fields creation.
    - ``model_converter``: `ModelConverter` class to use for converting the
        Mongoengine Document model to marshmallow fields.
    - ``autogenerate_pk_dump_only``: In the document autogenerate it primary_key
        (default behaviour in Mongoengine), ignore it from the incomming data
    """

    def __init__(self, meta):
        super(SchemaOpts, self).__init__(meta)
        self.model = getattr(meta, 'model', None)
        if self.model and not issubclass(self.model, BaseDocument):
            raise ValueError("`model` must be a subclass of mongoengine.base.BaseDocument")
        self.model_fields_kwargs = getattr(meta, 'model_fields_kwargs', {})
        self.autogenerate_pk_dump_only = getattr(
            meta, 'autogenerate_pk_dump_only', True)
        self.model_converter = getattr(meta, 'model_converter', ModelConverter)


class SchemaMeta(ma.schema.SchemaMeta):
    """Metaclass for `ModelSchema`."""

    # override SchemaMeta
    @classmethod
    def get_declared_fields(mcs, klass, *args, **kwargs):
        """Updates declared fields with fields converted from the
        Mongoengine model passed as the `model` class Meta option.
        """
        declared_fields = kwargs.get('dict_class', dict)()
        # inheriting from base classes
        for base in inspect.getmro(klass):
            opts = klass.opts
            if opts.model:
                Converter = opts.model_converter
                converter = Converter()
                declared_fields = converter.fields_for_model(
                    opts.model,
                    fields=opts.fields,
                    fields_kwargs=opts.model_fields_kwargs
                )
                break
        base_fields = super(SchemaMeta, mcs).get_declared_fields(
            klass, *args, **kwargs
        )
        declared_fields.update(base_fields)
        if opts.autogenerate_pk_dump_only and opts.model:
            # If primary key is automatically generated (nominal case), we
            # must make sure this field is read-only
            if opts.model._auto_id_field is True:
                id_field = base_fields.get(opts.model._meta['id_field'])
                if id_field:
                    id_field.dump_only = True
        return declared_fields


class ModelSchema(with_metaclass(SchemaMeta, ma.Schema)):
    """Base class for Mongoengine model-based Schemas.

    Example: ::

        from marshmallow_mongoengine import ModelSchema
        from mymodels import User

        class UserSchema(ModelSchema):
            class Meta:
                model = User
    """
    OPTIONS_CLASS = SchemaOpts

    def make_object(self, data):
        return self.opts.model(**data)

    def update(self, obj, data):
        """Helper function to update an already existing document
    instead of creating a new one.
    :param obj: Mongoengine Document to update
    :param data: incomming payload to deserialize
    :return: an :class UnmarshallResult:

    Example: ::

        from marshmallow_mongoengine import ModelSchema
        from mymodels import User

        class UserSchema(ModelSchema):
            class Meta:
                model = User

        def update_obj(id, payload):
            user = User.objects(id=id).first()
            result = UserSchema().update(user, payload)
            result.data is user # True
        """
        # TODO: find a cleaner way to skip required validation on update
        required_fields = [k for k, f in self.fields.items() if f.required]
        for field in required_fields:
            self.fields[field].required = False
        loaded_data, errors = self._do_load(data, postprocess=False)
        for field in required_fields:
            self.fields[field].required = True
        if not errors:
            # Update the given obj fields
            for k, v in loaded_data.items():
                # Skip default values that have been automatically
                # added during unserialization
                if k in data:
                    setattr(obj, k, v)
        return ma.UnmarshalResult(data=obj, errors=errors)
