import collections
from functools import wraps
import copy

from loki.utils import merge_dict

_templates = {}

_get_template_types = lambda x=None: _templates[x] if x else _templates


def get_template_types():
    """
    :rtype: dict[str, TemplateMeta]
    """
    return _get_template_types()


def get_template_by_type(_type):
    """
    :type _type: str
    :rtype: TemplateMeta
    """
    return _get_template_types(_type)


class Argument(collections.MutableMapping):
    def __init__(self, **kwargs):
        self._dict = kwargs

    def __setitem__(self, key, value):
        self._dict[key] = value

    def __getitem__(self, item):
        return self._dict[item]

    def __delitem__(self, key):
        del self._dict[key]

    def __iter__(self):
        return self._dict.__iter__()

    def __len__(self):
        return self._dict.__len__()

    def __unicode__(self):
        return repr(self._dict)

    def __str__(self):
        return str(self._dict)

    def __repr__(self):
        return repr(self._dict)

    # noinspection PyMethodMayBeStatic
    def get_value(self):
        raise NotImplemented

    def for_json(self):
        return self._dict


class TemplateMeta(type):
    def __init__(cls, cls_name, bases, dict_):
        for k in ("__arguments__",
                  "__context_hooks"):
            for base in bases:
                d = dict_.setdefault(k, {})
                if hasattr(base, k):
                    dict_[k] = merge_dict(d, getattr(base, k))

        type.__init__(cls, cls_name, bases, dict_)
        for k, v in sorted(dict_.iteritems(), key=lambda t: t[0]):
            cls._add_attribute(k, v)

        # register template in global _template dict
        template_name = getattr(cls, "__templatename__", None)
        if template_name:
            _templates[template_name] = cls

    def __setattr__(cls, key, value):
        cls._add_attribute(key, value)

    def _add_attribute(cls, key, value):
        """
        :type cls: TemplateMeta
        :type key: str
        :type value: Argument
        """
        if isinstance(value, Argument):
            cls.__arguments__[key] = value
            cls.__arguments__[key].update({"key": key})
            type.__delattr__(cls, key)
        elif callable(value) \
                and hasattr(value, "contexts") \
                and hasattr(value, "hooked_attr"):
            hooked_attr, contexts = value.hooked_attr, value.contexts
            for context in contexts:
                __context_hooks = getattr(cls, "__context_hooks")
                if context not in __context_hooks:
                    __context_hooks[context] = {}
                __context_hooks[context].update({hooked_attr: value})
        else:
            type.__setattr__(cls, key, value)


# noinspection PyNoneFunctionAssignment
class BaseTemplate(object):
    __metaclass__ = TemplateMeta
    _type_mapper = {
        "text": (str, unicode),
        "textarea": (str, unicode),
        "number": (int,),
        "select": (int, str, unicode),
        "checkbox": (bool,),
        "arrayinput": (list,),
        "servers_checkbox": (list,),
        "dictinput": (dict,),
    }

    def __init__(self, **kwargs):
        # self.__values__ = {}
        self.__arguments__ = copy.deepcopy(self.__class__.__arguments__)
        for name, attr in self.__arguments__.viewitems():
            value = attr.get('value')
            if value is not None:
                self._set_attribute(name, value)

        for k, v in kwargs.iteritems():
            if k in self._key_types:
                self._set_attribute(k, v)

    def __getattr__(self, item):
        ret = self._get_attribute(item)
        return ret

    def __getitem__(self, item):
        ret = self._get_attribute(item)
        if not ret:
            raise KeyError("key %s not exist" % item)
        return ret

    def _get_attribute(self, item):
        argument = self.__arguments__.get(item, None)
        if argument is not None:
            return argument.get_value()
        else:
            raise AttributeError(item)

    def __setattr__(self, key, value):
        ret = self._set_attribute(key, value)
        if not ret:
            return super(BaseTemplate, self).__setattr__(key, value)
        return ret

    def __setitem__(self, key, value):
        ret = self._set_attribute(key, value)
        if not ret:
            raise KeyError("key %s not exist" % key)
        return ret

    def _set_attribute(self, key, value):
        _type = self._key_types.get(key)
        if _type is None:
            return False

        _type_tuple = self._type_mapper.get(_type)
        if not _type_tuple:
            raise ValueError("type %s not exists in _type_mapper" % _type)

        if callable(value):
            value = value(self)

        if not isinstance(value, _type_tuple):
            try:
                value = _type_tuple[0](value)
            except Exception:
                raise TypeError("%s should be %s, but get %s" %
                                (key, _type_tuple, type(value)))

        self.__arguments__[key].update({'value': value})
        return True

    @classmethod
    def contexts_hook(cls, contexts, name):
        """
        :type contexts: int | collections.Iterable[int]
        :type name: str
        :rtype: collections.Callable
        """
        def factory(method):
            @wraps(method)
            def wrapper(self, *args, **kwargs):
                return method(self, *args, **kwargs)

            if isinstance(contexts, collections.Iterable):
                wrapper.contexts = contexts
            else:
                wrapper.contexts = [contexts]
            wrapper.hooked_attr = name
            return wrapper

        return factory

    def _get_context_hook(self, context):
        """
        :type context: int
        :rtype: dict[collections.Callable]
        """
        _context_hooks = getattr(self, "__context_hooks")
        if context in _context_hooks:
            return _context_hooks[context]
        else:
            return {}

    def render_form(self, context):
        """
        :type context: int
        :rtype: collections.Iterable[Argument]
        """
        data = []
        for k in self.__order__:
            d = self.__arguments__.get(k, None)
            if not d or d.set_context(context) is False:
                continue

            hook_method = self._get_context_hook(context).get(k)
            if isinstance(hook_method, collections.Callable):
                d = hook_method(self, d)
                assert d is not None, "hooked data should not be None"
            data.append(d)
        return data
