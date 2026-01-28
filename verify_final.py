import time
import requests

def test_flow():
    print("Adding patient...")
    resp = requests.post('http://127.0.0.1:5000/api/queue/add', json={
        'name': 'Audit Test',
        'phone': '000',
        'complaint': 'Test',
        'address': 'Blok X'
    })
    print("Add response:", resp.json())

    print("Checking audit log...")
    page = requests.get('http://127.0.0.1:5000/audit-log').text
    if 'Added patient Audit Test' in page:
        print("Audit Log SUCCESS")
    else:
        print("Audit Log FAILED")

if __name__ == '__main__':
    try:
        test_flow()
    except Exception as e:
        print(e)
