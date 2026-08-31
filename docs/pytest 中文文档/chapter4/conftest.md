# conftest.py

> 源文件：`chapter4/conftest.py`

```python
import pytest
import sys
import smtplib

sys.dont_write_bytecode = True

@pytest.fixture(scope='module')
def smtp_connection():
    return smtplib.SMTP('smtp.163.com', 25, timeout=5)

@pytest.fixture(scope='package')
def smtp_connection_package():
    return smtplib.SMTP('smtp.163.com', 25, timeout=5)

@pytest.fixture
def smtp_connection_yield():
    smtp_connection = smtplib.SMTP('smtp.163.com', 25, timeout=5)
    yield smtp_connection
    print('close smtp connection')
    smtp_connection.close()

    # 支持 with 写法的对象，可以使用下列写法隐式执行清理操作
    # with smtplib.SMTP('smtp.163.com', 25, timeout=5) as smtp_connection:
    #     yield smtp_connection

@pytest.fixture
def smtp_connection_fin(request):
    smtp_connection = smtplib.SMTP('smtp.163.com', 25, timeout=5)

    def fin():
        smtp_connection.close()

    request.addfinalizer(fin)
    return smtp_connection

@pytest.fixture(scope='module')
def smtp_connection_request(request):
    server, port = getattr(request.module, 'smtp_server', ("smtp.163.com", 25))
    with smtplib.SMTP(server, port) as smtp_connection:
        yield smtp_connection
        print(f"close {server}: {port}")

@pytest.fixture(scope='module', params=['smtp.163.com', 'mail.python.org'])
def smtp_connection_params(request):
    server = request.param
    with smtplib.SMTP(server, 587, timeout=5) as smtp_connection:
        yield smtp_connection
```
