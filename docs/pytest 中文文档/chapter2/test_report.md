# test_report.py

> 源文件：`chapter2/test_report.py`

```python
import pytest

@pytest.fixture
def error_fixture():
    assert False

def test_ok():
    print('ok')

def test_fail():
    assert True

def test_error(error_fixture):
    pass

def test_skip():
    pytest.skip("skipping this test")

def test_xfail():
    pytest.xfail("xfailing this test")

@pytest.mark.xfail(reason="always xfail")
def test_xpass():
    pass
```
