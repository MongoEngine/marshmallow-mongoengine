=======
History
=======

0.9.0 (2017-10-25)
-------------------
 - Add support for `toastedmarshamallow <https://pypi.python.org/pypi/toastedmarshmallow>`_
   BREAKING CHANGE: marshmallow is no more installed by default, should use
   ``pip install marshmallow_mongoengine[marshmallow]`` or ``pip install marshmallow_mongoengine[toasted]``
   depending of your favorite implementation.
 - ``HISTORY.rst`` file introduced