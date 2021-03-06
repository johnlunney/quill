""" Base class that contains all the methods on W_Root which is the root
objects of everything wrapped and presented to the user
"""


class W_Root(object):
    cls_w_type = None

    def int_w(self, space):
        raise space.apperr(space.w_typeerror, 'expected integer')

    def utf8_w(self, space):
        raise space.apperr(space.w_typeerror, 'expected string')

    def listview(self, space):
        raise space.apperr(space.w_typeerror, 'expected list')

    def dictview(self, space):
        raise space.apperr(space.w_typeerror, 'expected dict')

    def hash(self, space):
        raise space.apperr(space.w_typeerror, 'unhashable type')

    def getattr(self, space, attrname):
        return space.w_NotImplemented

    def bind(self, space, w_obj):
        return self

    def gettype(self, space):
        return self.cls_w_type


class W_None(W_Root):
    pass
