# test_raise.py

> 源文件：`chapter3/test_raise.py`

```python
import pytest

def myfunc():
    raise ValueError('Exception 123 raised')

def test_match1():
    with pytest.raises(ValueError):
        myfunc()

def test_match2():
    # excinfo 是 ExceptionInfo的一个实例，封装了 .type .value .traceback 等信息
    with pytest.raises(ValueError) as excinfo:
        myfunc()
    print("value: ", excinfo.value)
    print("type: ", excinfo.type)
    print("traceback: ", excinfo.traceback)
    assert '123' in str(excinfo.value)

def test_match3():
    with pytest.raises(ValueError) as excinfo:
        myfunc()
        assert '456' in str(excinfo.value)  # 该断言不会执行，用例必定成功

def test_match4():
    with pytest.raises((ValueError), match=r'.* 123 .*'):
        myfunc()

def test_match5():
    pytest.raises(ZeroDivisionError, lambda x: 1 / x, 0)

def test_match6():
    pytest.raises(ZeroDivisionError, lambda x: 1 / x, x = 0)

@pytest.mark.xfail(raises=IndexError)
def test_f1():
    raise IndexError('This is an Index Error')

@pytest.mark.xfail(raises=IndexError)
def test_f2():
    print('This is an Index Error')
```
