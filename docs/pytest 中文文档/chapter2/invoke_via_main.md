# invoke_via_main.py

> 源文件：`chapter2/invoke_via_main.py`

```python
import sys
import time

def test_one():
    time.sleep(10)

if __name__ == '__main__':
    import pytest
    ret = pytest.main(["-q", __file__])
    print(__file__)
    print("pytest.main() returned pytest.ExitCode.INTERRUPTED: ", + ret == pytest.ExitCode.INTERRUPTED)
```
