# conftest.py

> 源文件：`chapter3/conftest.py`

```python
from test_foo_compare_with_conftest import Foo

def pytest_assertrepr_compare(op, left, right):
    if isinstance(left, Foo) and isinstance(right, Foo) and op == '==':
        return [
            "比较两个Foo实例:",
            "    值: {} != {}".format(left.val, right.val),
        ]
```
