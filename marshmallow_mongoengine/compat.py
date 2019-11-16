
def compact_with_marshmallow(ma_field_cls):

    @wrap(fn=ma_field_cls._deserialize)
    def new_fn(*arg, **kwarg):
        return fn(*arg)
        
    ma_field_cls.__deserialize = new_fn 
    return ma_field_cls