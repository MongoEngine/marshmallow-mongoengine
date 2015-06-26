from marshmallow import validate

class MetaParam(object):
    def apply(self, params):
        raise NotImplementedError()


class MaxMinParam(MetaParam):
    def __init__(self, field):
        # Add a length validator for max_length/min_length
        self.maxmin_args = {}
        if hasattr(field_me, 'max_length'):
            self.maxmin_args['max'] = field_me.max_length
        if hasattr(field_me, 'min_length'):
            self.maxmin_args['min'] = field_me.min_length

    def apply(self, params):
        if not self.maxmin_args:
            return
        if 'validate' not in params:
            params['validate'] = []
        kwargs['validate'].append(validate.Length(**maxmin_args))
