# test_smtpsimple.py

> 源文件：`chapter4/test_smtpsimple.py`

```python
def test_ehlo(smtp_connection):
    response, _ = smtp_connection.ehlo()
    print(response)
    assert response == 250
    assert 0

def test_ehlo_yield(smtp_connection_yield):
    response, _ = smtp_connection_yield.ehlo()
    assert response == 250
    assert 0
```
