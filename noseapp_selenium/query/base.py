# -*- coding: utf-8 -*-


class QueryObject(object):
    """
    Structure of css query.

    Use instance of this class with
    from_object method of QueryProcessor.
    """

    def __init__(self, tag, **selector):
        self.tag = tag
        self.selector = selector

    def __unicode__(self):
        return u'<{} {}>'.format(
            self.tag,
            u' '.join(
                [u'{}="{}"'.format(k, v) for k, v in self.selector.items()]
            ),
        )


class _Contains(object):
    """
    Marker for use contains inside css query
    """

    def __init__(self, value):
        self.value = value

    def __repr__(self):
        return self.value

    def __str__(self):
        return str(self.value)

    def __unicode__(self):
        return unicode(self.value)


contains = _Contains
