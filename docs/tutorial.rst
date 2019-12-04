========
Tutorial
========

Marshmallow-Mongoengine is about bringing together a Mongoengine Document with a Marshmallow Schema.

Warming up
----------

First we need a Mongoengine Document:

.. code-block:: python

    import mongoengine as me


    class Task(me.EmbeddedDocument):
        content = me.StringField(required=True)
        priority = me.IntField(default=1)


    class User(me.Document):
        name = me.StringField()
        password = me.StringField(required=True)
        email = me.StringField()
        tasks = me.ListField(me.EmbeddedDocumentField(Task))


Great ! Now it's time for the Marshmallow Schema.
To keep things DRY, we use marshmallow-mongoengine to do the mapping:

.. code-block:: python

    import marshmallow_mongoengine as ma


    class UserSchema(ma.ModelSchema):
        class Meta:
            model = User


Finally it's time to use our schema to load/dump documents:

.. code-block:: python

    >>> user_schema = UserSchema()
    >>> u = user_schema.load({
    ...     "name": "John Doe", "email": "jdoe@example.com", "password": "123456",
    ...     "tasks": [{"content": "Find a proper password"}]})
    >>> u.save()
    <User: User object>
    >>> u.name
    "John Doe"
    >>> u.tasks
    [<Task: Task object>]
    >>> user_schema.dump(u)
    {"name": "John Doe", "email": "jdoe@example.com", "password": "123456", "tasks": [{"content": "Find a proper password", "priority": 1}]}


If the document already exists, we can update it using `update`

.. code-block:: python

    >>> u
    >>> u2 = user.schema.update(u, {"name": "Jacques Faite"})
    >>> u2 is u
    True
    >>> u2.name
    "Jacques Faite"

.. Note:: `required` argument in the fields is not taken into account when using update


Configuring the schema
----------------------


Let say we use `user_schema.dump` to send data to a client throught HTTP.
In this case, returning the `password` field seems a pretty bad idea !

We could solve this by using marshmallow's `Meta.exclude` list, but this means
the field would be also excluded loading.

The solution is to use the `Model.model_fields_kwargs` option to customize the field (de)seriliazers:


.. code-block:: python

    class UserSchemaNoPassword(ma.ModelSchema):
        class Meta:
            model = User
            model_fields_kwargs = {'password': {'load_only': True}}


No consider the loading process: for the moment we directly put the password in the password field.
This is not a good idea - this is also a really poor idea to use "123456" as password ;-) - we should
first hash and salt it.

To do that, we need to disable the build of the Mongoengine document by specifying `Model.model_build_obj`

.. code-block:: python

    class UserSchemaJSON(ma.ModelSchema):
        class Meta:
            model = User
            model_build_obj = False # default is True


Now the schema will do all the integrity checks, but after that will stop and return a dict:

.. code-block:: python

    >>> user_schema = UserSchemaJSON()
    >>> data = user_schema.load({"name": "John Doe", "email": "jdoe@example.com", "password": "123456"})
    >>> data
    {"name": "John Doe", "email": "jdoe@example.com", "password": "123456"}
    >>> data["password"] = hash_and_salt(data["password"]) # Alter the data
    >>> User(**data) # Finally build the Mongoengine document from the data
    <User: User object>


Customizing the schema
----------------------

Now let say we want to customize the way the tasks are dumped, for example
we want to return the field `priority` in a more understandably way than just a number
(1 => "High", 2 => "Medium", 3 => "Will see tomorrow").

Given we can shadow the auto-generated fields by defining our own in the Schema,
we only have to redefine the `property` field and we're done !

.. code-block:: python

    class UserSchemaCustomPriority(ma.ModelSchema):
        class Meta:
            model = User

        priority = ma.fields.Method(serialize="_priority_serializer", deserialize="_priority_deserializer")

        def _priority_serializer(self, obj):
            if obj.priority == 1:
                return "High"
            elif obj.priority == 2:
                return "Medium"
            else:
                return "Will do tomorrow"

.. code-block:: python

    >>> user_schema = UserSchemaCustomPriority()
    >>> user = User(name="John Doe", email="jdoe@example.com",
    ...             tasks=[{"content": "Find a proper password"},
    ...                    {"content": "Learn to cook", "priority": 2},
    ...                    {"content": "Fix issues", "priority": 3}])
    >>> dump = user_schema.dump(user)
    >>> dump
    {"name": "John Doe", "email": "jdoe@example.com", "tasks": [{"content": "Find a proper password", "priority": "High"}, {"content": "Learn to cook", "priority": "Medium"}, {"content": "Fix issues", "priority": "Will do tomorrow"}]}
