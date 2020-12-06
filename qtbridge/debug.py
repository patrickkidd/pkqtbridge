## NO deps outside std lib!
##

import os, sys
import pprint, traceback, inspect


def get_class_that_defined_method(meth):
    if inspect.ismethod(meth):
        for cls in inspect.getmro(meth.__self__.__class__):
           if cls.__dict__.get(meth.__name__) is meth:
                return cls
        meth = meth.__func__  # fallback to __qualname__ parsing
    if inspect.isfunction(meth):
        cls = getattr(inspect.getmodule(meth),
                      meth.__qualname__.split('.<locals>', 1)[0].rsplit('.', 1)[0])
        if isinstance(cls, type):
            return cls
    return getattr(meth, '__objclass__', None)  # handle special descriptor objects

class Debug:

    DEBUG = True

    WRITE = print # Avoid PyQt dependency

    __pp = pprint.PrettyPrinter(indent=4)

    def __init__(self, *args, **kwargs):
        if args:
            self.here(*args, **kwargs, ctor=True)
        self._saying = False

    def setDebug(self, on):
        self.DEBUG = on

    def here(self, *args, newline=True, frame=True, ctor=False):
        if hasattr(self, '_saying') and self._saying:
            return
        self._saying = True
        if not self.DEBUG:
            return

        cleanArgs = Debug.cleanArgs(*args)

        # Calling frame

        if frame:

            stack = inspect.stack()
            parent_locals = stack[1][0].f_locals['self']
            parent_func_name = stack[1][3]
            if hasattr(parent_locals, parent_func_name):
                parent_func_attr = getattr(parent_locals, parent_func_name)
                if inspect.ismethod(parent_func_attr) and parent_func_attr.__qualname__ != 'blocked.<locals>.go': # property
                    the_class_name = parent_func_attr.__qualname__.split('.')[-2]
                else:
                    the_class_name = self.__class__.__name__
            else:
                fpath = inspect.getframeinfo(stack[1][0]).filename
                the_class_name = os.path.splitext(os.path.basename(fpath))[0]
            if ctor:
                frame = stack[2][0]
                lineno = stack[2][2]
            else:
                frame = stack[1][0]
                lineno = stack[1][2]
            if inspect.getmodule(frame):
                filename = os.path.basename(inspect.getmodule(frame).__file__)
            else:
                filename = '<embedded>'
            # the_class = frame.f_locals["self"].__class__.__name__
            the_method = frame.f_code.co_name
            # the_lineno = frame.f_code.co_firstlineno

            parts = (('%s(%s) [%s.%s] ' % (filename, lineno, the_class_name, the_method)).ljust(35),) + cleanArgs
            finalS = ' '.join(parts)

        else: # not frame

            finalS = ' '.join(cleanArgs)

        # if newline:
        #     finalS = finalS + '\n'
        
        Debug.WRITE(finalS)

        self._saying = False

    @staticmethod
    def repr(x):
        """ Return a clean representation of an object. """
        if type(x) == str:
            return x
            # return "'%s'" % x
        elif type(x) == type:
            return x
        else:
            return x.__repr__().replace('PyQt5.QtCore.', '').replace('PyQt5.QtGui.', '')

    @staticmethod
    def cleanArgs(*args):
        """ Return a cleaned up string from a list of args. """
        ret = ()
        for index, i in enumerate(args):
            if isinstance(i, dict) or isinstance(i, list):
                if index == 0:
                    ret += ('\n' + Debug.__pp.pformat(i) + '\n',)
                else:
                    ret += (Debug.__pp.pformat(i),)
            else:
                ret += (Debug.repr(i),)
        return ret
    
    @staticmethod
    def pretty(x, exclude=[], noNone=True):
        if not isinstance(exclude, list):
            exclude = [exclude]
        s = ''
        if isinstance(x, dict):
            parts = []
            for k, v in x.items():
                if k not in exclude and (noNone and v is not None):
                    parts.append('%s: %s' % (k, Debug.repr(v)))
            s += ', '.join(parts)
        return s

    def stack(self):
        if not self.DEBUG:
            return
        traceback.print_stack()
        print()

    @staticmethod
    def showPoint(path, point, name, coords=False):
        OFFSET = 2.0
        def S(p):
            return '(%.1f, %.1f)' % (point.x(), point.y())
        dot = QRectF(0, 0, OFFSET, OFFSET)
        dot.moveCenter(point)
        path.addRoundedRect(dot, OFFSET / 2, OFFSET / 2)
        if coords is True:
            s = name + ': ' + S(point)
        else:
            s = name
        path.addText(point + QPointF(OFFSET, OFFSET), QFont('Helvetica', 6, 0), s)
