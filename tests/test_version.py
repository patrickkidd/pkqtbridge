import unittest
from qtbridge import version


def test_greaterThan():

    assert not version.greaterThan('1.0.0b4', '1.0.0b5')
    assert version.greaterThan('1.0.0b5', '1.0.0b4')
    assert not version.greaterThan('1.0.0b4', '1.0.0b4')

    assert version.greaterThan('1.0.1b4', '1.0.0b5')
    assert version.greaterThan('1.0.1', '1.0.0b5')
    assert not version.greaterThan('1.1.9', '1.2.3b4')


        
if __name__ == '__main__':
    test_util.main()

