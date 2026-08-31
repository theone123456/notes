# test_params.py

> 源文件：`chapter4/test_params.py`

```python
def test_params(smtp_connection_params):
    response, _ = smtp_connection_params.ehlo()
    assert response == 250
```
