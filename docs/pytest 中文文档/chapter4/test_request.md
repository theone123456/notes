# test_request.py

> 源文件：`chapter4/test_request.py`

```python
smtp_server = ('mail.python.org', 587)

def test_163(smtp_connection_request):
    response, _ = smtp_connection_request.ehlo()
    assert response == 250
```
