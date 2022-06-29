import requests


if __name__ == "__main__":
    endpoint = f'http://127.0.0.1:8000/api/executions/5WS478T1COW78UJZOJ0EAU27WVYNAFEFN4CP/set_execution/'

    data = {'ExecutionStatus': "Running", "RobotId": "5WS478T1COW7"}
    response = requests.put(endpoint, data=data,
                            headers={'Authorization': f'Token b116e341408f0ecd515b63603b412b54d74f4819'})

    print(response.text)