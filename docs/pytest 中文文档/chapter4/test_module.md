# test_module.py

> 源文件：`chapter4/test_module.py`

```python
def test_ehlo(smtp_connection):
    response, _ = smtp_connection.ehlo()
    assert response == 250
    smtp_connection.extra_attr = 'test'
    assert 0

def test_noop(smtp_connection):
    response, _ = smtp_connection.noop()
    print(smtp_connection.extra_attr)
    assert response == 250
    assert smtp_connection.extra_attr == 0
```
