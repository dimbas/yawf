from yawf.utils import escape


def test_escape():
    assert escape() == ''
    assert escape(['some', 'interesting', 'data']) == "['some', 'interesting', 'data']"
    assert escape('one & two < three') == 'one &amp; two &lt; three'
