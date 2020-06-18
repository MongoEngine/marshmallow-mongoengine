=======
History
=======

0.30.0 (2019-TBR)
-------------------
 - Add support for marshmallow v3
 - Remove support for python2 since mm-v3 needs >= p35.
 - Removed support for toasted since doesn't support mm-v3

0.11.0 (2020-05-30)
-------------------
 - Drop support for Python 2.7
 - Fix requirement on marshmallow (version 3 is not supported)

0.10.0 (2017-11-06)
-------------------
 - Add support for mongoengine.LazyReferenceField and mongoengine.GenericLazyReferenceField

0.9.1 (2017-10-25)
-------------------
 - Correct error on release

0.9.0 (2017-10-25)
-------------------
 - Add support for `toastedmarshamallow <https://pypi.python.org/pypi/toastedmarshmallow>`_
   BREAKING CHANGE: marshmallow is no more installed by default, should use
   ``pip install marshmallow_mongoengine[marshmallow]`` or ``pip install marshmallow_mongoengine[toasted]``
   depending of your favorite implementation.
 - ``HISTORY.rst`` file introduced
