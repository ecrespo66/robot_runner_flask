import requests


if __name__ == "__main__":
    endpoint = f'http://127.0.0.1:8000/api/git/'

    data = {'ExecutionStatus': "Running", "RobotId": "5WS478T1COW7"}
    response = requests.get(endpoint,
                            headers={'Authorization': f'Token 87ff1a91798e45bb616a86634277c2d5f224098a'})
