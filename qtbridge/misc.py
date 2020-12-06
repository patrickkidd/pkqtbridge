"""
Miscellaneous useful methods for Python and/or Qt apps.
"""


from .pyqt import *
import os, os.path, time, math, collections.abc
from .debug import *





def csToBool(cs):
    if cs == Qt.Checked:
        return True
    elif cs == Qt.PartiallyChecked:
        return True
    elif cs == Qt.Unchecked:
        return False

# https://stackoverflow.com/questions/596216/formula-to-determine-brightness-of-rgb-color
# https://www.w3.org/TR/AERT/#color-contrast
def luminanceOf(color):
    return ( 0.299 * color.redF() + 0.587 * color.greenF() + 0.114 * color.blueF() )

def isLightColor(color):
    return color.alphaF() < 1 or luminanceOf(color) >= .7

def contrastTo(color):
    if isLightColor(color):
        return QColor(Qt.black)
    else:
        return QColor(Qt.white)

# https://stackoverflow.com/questions/12228548/finding-equivalent-color-with-opacity
def lightenOpacity(c, a):
    w = QColor('white')
    r1, g1, b1 = c.red(), c.green(), c.blue()
    r2, g2, b2 = w.red(), w.green(), w.blue()
    r3 = r2 + (r1 - r2) * a
    g3 = g2 + (g1 - g2) * a
    b3 = b2 + (b1 - b2) * a
    return QColor(int(r3), int(g3), int(b3))


# https://www.qtcentre.org/threads/3205-Toplevel-widget-with-rounded-corners
def roundedRectRegion(rect, radius, parts):
    """ parts = ('bottom-left', 'top-right', ...)
    USAGE:
        self.setMask(util.roundedRectRegion(self.rect(), util.BORDER_RADIUS)) 
    """
    region = QRegion()
    # middle and borders
    region += rect.adjusted(radius, 0, -radius, 0)
    region += rect.adjusted(0, radius, 0, -radius)
    corner = QRect(QPoint(0, 0), QSize(radius * 2, radius * 2))
    if 'top-left' in parts:
        corner.moveTopLeft(rect.topLeft())
        region += QRegion(corner, QRegion.Ellipse)
    if 'top-right' in parts:
        corner.moveTopRight(rect.topRight())
        region += QRegion(corner, QRegion.Ellipse)
    if 'bottom-left' in parts:
        corner.moveBottomLeft(rect.bottomLeft())
        region += QRegion(corner, QRegion.Ellipse)
    if 'bottom-right' in parts:
        corner.moveBottomRight(rect.bottomRight())
        region += QRegion(corner, QRegion.Ellipse)
    return region


def deepMerge(d, u, ignore=[]):
    """ Recursively merge dict `u` in to dict `d`. """
    if not isinstance(ignore, list):
        ignore = [ignore]
    for k, v in u.items():
        if k in ignore:
            continue
        if isinstance(v, collections.abc.Mapping) and (k in d):
            d[k] = deepMerge(d.get(k, {}), v, ignore=ignore)
        else:
            d[k] = v
    return d

def invertPixmap(p):
    img = p.toImage()
    img.invertPixels()
    return QPixmap.fromImage(img)

def rindex(lst, val, start=None):
    if start is None:
        start = len(lst)-1
    for i in xrange(start,-1,-1):
        if lst[i] == val:
            return i

def rindex(li, x):
    for i in reversed(range(len(li))):
        if li[i] == x:
            return i
    raise ValueError("{} is not in list".format(x))

def suffix(s):
    if '.' in s:
        return s[s.rfind('.')+1:]
    else:
        return None

def fileName(filePath):
    return filePath[filePath.rfind(os.sep)+1:]


def newNameOf(items, tmpl, key):
    if not items:
        return tmpl % 1
    name = None
    for i in range(10000):
        name = tmpl % (i+1)
        found = False
        for row, item in enumerate(items):
            if key(item) == name:
                found = True
                break
        if not found:
            break
    return name
    



def printQObject(o):
    mo = o.metaObject()
    properties = []
    signals = []
    slots = []
    etc = []
    for i in range(mo.propertyCount()):
        properties.append(mo.property(i).name())
    for i in range(mo.methodCount()):
        meth = mo.method(i)
        if meth.methodType() == QMetaMethod.Signal:
            signals.append(bytes(meth.methodSignature()).decode())
        elif meth.methodType() == QMetaMethod.Slot:
            slots.append(bytes(meth.methodSignature()).decode())
        else:
            etc.append(bytes(meth.methodSignature()).decode())
    Debug(' ')
    Debug('QOBJECT:', o.__class__.__name__, 'objectName: "%s"' % o.objectName())
    for i in sorted(properties):
        Debug('    PROPERTY: ', i)
    for i in sorted(signals):
        Debug('    SIGNAL:   ', i)
    for i in sorted(slots):
        Debug('    SLOT:     ', i)
    for i in sorted(etc):
        Debug('    METHOD:   ', i)



def lelide(data, length):
    return ('...' + data[len(data) - (length-4):]) if len(data) > (length-4) else data

def ljust(data, length):
    if len(data) > length:
        data = lelide(data, length)
    return data.ljust(length)

def runModel(model, silent=True, columns=None):
    WIDTH = 25
    if not silent:
        Debug('MODEL:', model.__class__.__name__, 'objectName: "%s"' % model.objectName())
        sys.stdout.write(' %s|' % ljust('Column', 10))
    nCols = model.columnCount()
    for col in range(model.columnCount()):
        if columns is not None and not col in columns:
            continue
        header = model.headerData(col, Qt.Horizontal)
        if not silent:
            if col < nCols-1:
                sys.stdout.write(' %s|' % ljust(header, WIDTH))
            else:
                sys.stdout.write(' %ss' % ljust(header, WIDTH))
    if not silent:
        print()
    for row in range(model.rowCount()):
        if not silent:
            sys.stdout.write(' %s|' % ljust(str(row), 10))
        for col in range(model.columnCount()):
            if columns is not None and not col in columns:
                continue
            index = model.index(row, col)
            if -1 in (index.row(), index.column()):
                raise ValueError('invalid index: row: %s, col: %s' % (row, col))
            value = model.data(index, Qt.DisplayRole)
            if not silent:
                if col < nCols-1:
                    sys.stdout.write(' %s|' % ljust(str(value), WIDTH))
                else:
                    sys.stdout.write(' %s' % ljust(str(value), WIDTH))
        if not silent:
            print()


def printModel(model, columns):
    runModel(model, silent=False, columns=columns)



### Geometry functions


def distance(p1, p2):
    """ pythagorean """
    a = p1.x() - p2.x()
    b = p1.y() - p2.y()
    return math.sqrt(a*a + b*b)


def pointOnRay(orig, dest, distance):
    """ Calculate a point on ray (orig, dest) <distance> from orig """
    a = dest.x() - orig.x()
    b = dest.y() - orig.y()
    c = math.sqrt(pow(a, 2) + pow(b, 2)) # pythagorean
    if c > 0:
        p = distance / c
    else:
        p = 0
    return QPointF(orig.x() + p * a, orig.y() + p * b)


def perpendicular(pointA, pointB, reverse=False, width=None):
    """Return pointC such that ray
       (pointC, pointB) is perpendicular to ray (pointA, pointB).
    """
    if reverse:
        pointB, pointA = pointA, pointB
    x1 = pointA.x()
    x2 = pointB.x()
    y1 = pointA.y()
    y2 = pointB.y()
    a = x1 - x2
    b = y1 - y2
    if reverse is True:
        x3 = x2 - b
        y3 = y2 + a
    else:
        x3 = x2 + b
        y3 = y2 - a
    if width is None:
        return QPointF(x3, y3)
    else:
        return QPointF(pointOnRay(pointB, QPointF(x3, y3), width))


# def drawTextAroundPoint(painter, x, y, flags, text, boundingRect=None):
#     size = 32767.0
#     corner = QPointF(x, y - size)
#     if flags & Qt.AlignHCenter:
#         corner.setX(corner.x() - (size / 2.0))
#     elif flags & Qt.AlignRight:
#         corner.setX(corner.x() - size)
#     if flags & Qt.AlignVCenter:
#         corner.setY(corner.y() + size / 2.0)
#     elif flags & Qt.AlignTop:
#         corner.setY(corner.y() + size)
#     else:
#         flags |= Qt.AlignBottom
#     rect = QRectF(corner.x(), corner.y(), size, size)
#     painter.drawText(rect, flags, text, boundingRect)


def dateOverlap(startA, endA, startB, endB):
    if (not startA and not endA) or (not startB and not endB):
        return True
    if startA is None: startA = QDate()
    if endA is None: endA = QDate()
    if startB is None: startB = QDate()
    if endB is None: endB = QDate()
    return startA <= endB and endA >= startB



def checkHTTPReply(reply):
    """ Generic http code handling. """
    error = reply.error()
    ret = None
    if error == QNetworkReply.NoError:
        ret = True
    elif error == QNetworkReply.HostNotFoundError: # no internet connection
        Debug('No internet connection')
        ret = False
    elif error == QNetworkReply.ConnectionRefusedError:
        if IS_MOD_TEST:
            Debug('Connection refused:', reply.url().toString())
        ret = False
    elif error == QNetworkReply.ContentAccessDenied:
        Debug('Access Denied:', reply.url().toString())
        ret = False
    elif error == QNetworkReply.AuthenticationRequiredError:
        ret = True
    elif error == QNetworkReply.ContentNotFoundError:
        # if not IS_TEST:
        #     Debug('404 Not Found: ' + reply.url().toString())
        ret = False
    elif error == QNetworkReply.OperationCanceledError: # reply.abort() called
        ret = False
    elif error == QNetworkReply.SslHandshakeFailedError:
        Debug('SSL handshake with server failed.')
        ret = False
    else:
        if reply.operation() == QNetworkAccessManager.HeadOperation:
            verb = 'HEAD'
        elif reply.operation() == QNetworkAccessManager.GetOperation:
            verb = 'GET'
        elif reply.operation() == QNetworkAccessManager.PutOperation:
            verb = 'PUT'
        elif reply.operation() == QNetworkAccessManager.PostOperation:
            verb = 'POST'
        elif reply.operation() == QNetworkAccessManager.DeleteOperation:
            verb = 'DELETE'
        elif reply.operation() == QNetworkAccessManager.CustomOperation:
            verb = '<custom>'
        Debug('ERROR Qt reply:') # ', error)
        Debug('    URL:', reply.request().url().toString())
        Debug('    HTTP method:', verb)
        Debug('    HTTP code:', reply.attribute(QNetworkRequest.HttpStatusCodeAttribute))
        Debug('    RESPONSE HEADERS:')
        for k, v in reply.rawHeaderPairs():
            Debug('    ', str(k), str(v))
        ret = False
    return ret



def file_md5(fpath):
    import hashlib
    if not QFileInfo(fpath).isFile():
        return
    hash_md5 = hashlib.md5()
    f = QFile(fpath)
    if not f.open(QIODevice.ReadOnly):
        Debug('Could not open file for reading:', fpath)
        return
    for chunk in iter(lambda: f.read(4096), b""):
        hash_md5.update(chunk)
    return hash_md5.hexdigest()



def fileEquals(filePath1, filePath2):
    if not QFileInfo(filePath1).isFile() or not QFileInfo(filePath2).isFile():
        return False
    md5_1 = file_md5(filePath1)
    md5_2 = file_md5(filePath2)
    return md5_1 == md5_2


def copyFileOrDir(src, dst):
    """ cp -R <src> <dst> """
    Debug('copyFileOrDir: +++', src)
    Debug('copyFileOrDir: ---', dst)
    if QFileInfo(src).isFile():
        if not QFileInfo(dst).isFile() or not fileEquals(src, dst):
            dest_dir = os.path.dirname(dst)
            if not os.path.isdir(dest_dir):
                os.mkdir(dest_dir)
            if QFile.copy(src, dst):
                Debug('Wrote file', dst)
            else:
                Debug('Could not write file', dst)
    else:
        dir = QDir(src)

        for d in dir.entryList(QDir.Dirs | QDir.NoDotAndDotDot):
            dst_path = os.path.join(dst, d)
            dir.mkpath(dst_path)
            copyFileOrDir(os.path.join(src, d), dst_path)

        for f in dir.entryList(QDir.Files):
            dirPath = QFileInfo(os.path.join(dst, f)).absolutePath()
            if not QDir(dirPath).exists():
                if not QDir(dirPath).mkpath("."):
                    Debug("Could not create path", dirPath)
                    continue
            # Debug('>>>')
            copyFileOrDir(os.path.join(src, f), os.path.join(dst, f))
    # Debug('<<<')


def qenum(base, value):
    """Convert a Qt Enum value to its key as a string.

    Args:
        base: The object the enum is in, e.g. QFrame.
        value: The value to get.

    Return:
        The key associated with the value as a string, or None.
    """
    klass = value.__class__
    try:
        idx = klass.staticMetaObject.indexOfEnumerator(klass.__name__)
    except AttributeError:
        idx = -1
    keyName = None
    if idx != -1:
        keyName = klass.staticMetaObject.enumerator(idx).valueToKey(value)
    else:
        for name, obj in vars(base).items():
            if isinstance(obj, klass) and obj == value:
                keyName = name
                break
    if keyName:
        return '%s.%s' % (base.__name__, keyName)


def shouldFullScreen():
    IS_IPHONE = bool(CUtil.instance().operatingSystem() == CUtil.OS_iPhone)
    self.here(CUtil.instance().operatingSystem(), CUtil.OS_iPhone)
    return IS_IPHONE




#####################################################
##
##  Dev and Test utils
##
#####################################################

_profile = None
def startProfile():
    global _profile
        
    ### Std Python profiler
    import cProfile
    _profile = cProfile.Profile()
    _profile.enable()

    ### pyinstrument
    # import pyinstrument
    # self.profile = pyinstrument.Profiler()

    ### pycallgraph
    # from pycallgraph import PyCallGraph
    # from pycallgraph.output import GraphvizOutput
    # graphviz = GraphvizOutput(output_file='profile.png')
    # self.profiler = PyCallGraph(output=graphviz)
    # self.profiler.start()

def stopProfile():
    global _profile
    
    ### Std python profiler
    _profile.disable()
    import io, pstats
    s = io.StringIO()
    sortby = 'cumulative'
    ps = pstats.Stats(_profile, stream=s).sort_stats(sortby)
    ps.print_stats() # ('pksampler')
    Debug(s.getvalue())
    _profile = None

    ### pyinstrument
    # self.profiler.stop()
    # self.here(profiler.output_text(unicode=True, color=True))
    # self.profiler = None

    ### pycallgraph
    # self.profiler.done()
    # self.profiler = None # saves file
    # os.system('open profile.png')
    

def wait_for_attach():
    PORT = 3001
    Debug('Waiting for debugger to attach to port %i...' % PORT)
    # import ptvsd
    # ptvsd.enable_attach(address=('127.0.0.1', PORT)) #, redirect_output=True)
    # ptvsd.wait_for_attach()
    import debugpy
    debugpy.listen(PORT)
    debugpy.wait_for_client()


class Condition(Debug):
    """ Allows you to wait for a signal to be called. """
    def __init__(self, signal=None, only=None, condition=None, name=None):
        self.callCount = 0
        self.callArgs = []
        self.senders = []
        self.lastCallArgs  = None
        self.only = only
        self.condition = condition
        self.name = name
        self.signal = signal
        if signal:
            signal.connect(self)

    def __deinit__(self):
        if self.signal:
            self.signal.disconnect(self)

    def reset(self):
        self.callCount = 0
        self.callArgs = []
        self.senders = []
        self.lastCallArgs = None

    def test(self):
        """ Return true if the condition is true. """
        if self.condition:
            return self.condition()
        else:
            return self.callCount > 0

    def set(self, *args):
        """ Set the condition to true. Alias for condition(). """
        self.callCount += 1
        self.senders.append(QObject().sender())
        self.lastCallArgs = args
        self.callArgs.append(args)

    def __call__(self, *args):
        """ Called by whatever signal that triggers the condition. """
        if self.only:
            only = self.only
            if not only(*args):
                return
        self.set(*args)

    def wait(self, maxMS=1000, onError=None, interval=10):
        """ Wait for the condition to be true. onError is a callback. """
        startTime = time.time()
        success = True
        app = QApplication.instance()
        while app and not self.test():
            try:
                app.processEvents(QEventLoop.WaitForMoreEvents, interval)
            except KeyboardInterrupt as e:
                if onError:
                    onError()
                break
            elapsed = ((time.time() - startTime) * 1000)
            if elapsed >= maxMS:
                break
            # else:
            #     time.sleep(.1) # replace with some way to release loop directly from signal
        ret = self.test()
        return ret

    def assertWait(self, *args, **kwargs):
        assert self.wait(*args, **kwargs) == True


