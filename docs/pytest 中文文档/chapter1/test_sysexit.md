# test_sysexit.py

> 源文件：`chapter1/test_sysexit.py`

```python
import pytest

def f():
    # 解释器请求退出
    raise SystemExit(1)

def test_sysexit():
    with pytest.raises(SystemExit):
        f()
```
