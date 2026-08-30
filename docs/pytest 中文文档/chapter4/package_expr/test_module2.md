# test_module2.py

> 源文件：`chapter4/package_expr/test_module2.py`

```python
def test_ehlo_in_module2(smtp_connection_package):
    response, _ = smtp_connection_package.ehlo()
    assert response == 250
    assert 0
```
