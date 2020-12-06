from qtbridge import misc
from qtbridge.pyqt import QDate, QRect, QMessageBox, QTimer


def test_dates():
    bday = QDate(1980, 5, 11)
    assert bday == misc.toDate('05/11/1980')

    assert misc.fromDate(bday) == '05/11/1980'

def test_date_overlap():

    def date(x):
        return QDate(x, 1, 1)
    
    # inside
    assert misc.dateOverlap(date(2000), date(2003),
                            date(2001), date(2002))
    # before + inside
    assert misc.dateOverlap(date(2000), date(2002),
                            date(1999), date(2001))
    # inside + after
    assert misc.dateOverlap(date(2000), date(2002),
                            date(2001), date(2004))
    # before
    assert not misc.dateOverlap(date(2000), date(2001),
                                date(1998), date(1999))
    # after
    assert not misc.dateOverlap(date(2000), date(2001),
                                date(2002), date(2003))
    

def test_qenum():
    assert misc.qenum(QMessageBox, QMessageBox.No) == 'QMessageBox.No'



def test_fblocked():
    class A:
        def __init__(self):
            self.count = 0

        def one(self):
            self.count += 1
            self.two()

        @misc.fblocked
        def two(self):
            """ Block just one method call. """
            self.count += 1
            self.one()

        @misc.fblocked
        def three(self):
            """ Block self but not two(). """
            self.count += 1
            self.two()
            
    a = A()
    a.one()
    assert a.count == 3
    
    a.two()
    assert a.count == 5 # would be three if not fblocked
    
    a.three()
    assert a.count == 8


    
def test_Condition_lambda_condition(qApp):
    cond = misc.Condition(condition=lambda: cond.callCount > 0)
    timer = QTimer()
    timer.setInterval(0)
    timer.timeout.connect(cond)
    # Zero-length timer shouldn't run until first idle frame
    # opened up by the &.wait() call below.
    timer.start()
    
    # Should block until the very next idle frame after condition is met,
    # i.e. after the first time the timer times out.
    # Timeout exception should not be raised in the meantime.
    # So call count should only be 1 when wait returns.
    cond.wait()
    assert cond.callCount == 1

    timer.stop()


