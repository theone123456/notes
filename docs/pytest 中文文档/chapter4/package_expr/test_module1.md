# test_module1.py

> 源文件：`chapter4/package_expr/test_module1.py`

```python
def test_ehlo_in_module1(smtp_connection_package):
    response, _ = smtp_connection_package.ehlo()
    assert response == 250
    assert 0

def test_noop_in_module1(smtp_connection_package):
    response, _ = smtp_connection_package.noop()
    assert response == 250
    assert 0
```
