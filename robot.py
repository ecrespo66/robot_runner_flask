import datetime
import random
import signal
import socket
import string
import subprocess
import time
import git
from git import Repo
import requests
import os


class Robot:
    def __init__(self, data):
        self.repoUrl = data['repo_url'] + '.git'
        self.RobotId = data['RobotId']
        self.RobotName = data['Name']


class Runner:
    def __init__(self, **kwargs):

        self.remote = None
        self.robot_id = None
        self.token = None
        self.robot = None
        self.execution_id = None
        self.robot_folder = None
        self.robot_params = None
        self.install_packages_process = None
        self.run_robot_process = None
        self.create_virtuaenv_process = None
        self.url = self.__clean_url(kwargs.get("url"))
        self.machine_id = kwargs.get("machine_id")
        self.license_key = kwargs.get("license_key")
        self.folder = kwargs.get("folder")
        self.server = kwargs.get("server")
        self.branch = kwargs.get("branch")
        self.token = kwargs.get("token")
        self.headers = {'Authorization': f'Token {self.token}'}
        self.http_protocol = self.__get_http_protocol()
        self.__get_network()
        self.port = 5000
        self.set_machine_ip()

    def __get_network(self):
        """ This method is used to get the ip network of the robot. """
        self.ip = socket.gethostbyname(socket.gethostname())

    @staticmethod
    def __clean_url(url):
        """
        This method is used to clean the url of the robot manager console API.
        """
        if "https://" in url:
            url = url.replace("https://", "")
        elif "http://" in url:
            url = url.replace("http://", "")
        if url[-1] == "/":
            url = url[:-1]
        return url

    def __get_http_protocol(self):
        """
        This method is used to get the protocol of the iBott API.
        Returns:
            http_protocol: str
        """
        if "https://" in self.url:
            return "https://"
        return "http://"

    def set_robot_folder(self):
        """
        This method is used to set the folder of the robot
        where the robot will be installed.
        """
        self.robot_folder = f"{self.folder}/{self.robot_id}"
        if not os.path.exists(self.robot_folder):
            os.makedirs(self.robot_folder)

    def set_robo_params(self, params):
        """
        This method is used to set the robot parameters sent from the robot manager console.
        """
        if len(params) > 0:
            self.robot_params = params
        else:
            self.robot_params = "None"

    def set_robot(self, data):
        """
        This method is used to set the robot.
        """
        self.robot_id = data['robot']
        self.execution_id = data['execution']

        if data['params']:
            self.robot_params = data['params']
        else:
            self.robot_params = "None"

        self.get_robot_data()
        self.set_robot_folder()

    def __get_token(self):
        """
        This method is used to get the token of the robot manager console API.
        """
        endpoint = f'{self.http_protocol}{self.url}/api-token-auth/'
        data = {'username': self.username, 'password': self.password}
        response = requests.post(endpoint, data)
        return response.json()['token']


    def set_machine_ip(self):
        """
        This method is used to set the machine ip
        """

        endpoint = f"{self.http_protocol}{self.url}/api/machines/{self.machine_id}/set_machine/"
        data = {'LicenseKey': self.license_key, "ipAddress": self.ip, 'port': self.port, 'status': 'free'}
        try:
            requests.put(endpoint, data, headers=self.headers)
        except Exception as e:
            raise ConnectionError(e)

    def get_robot_data(self):
        """
        This method is used to get the robot data.
        """
        endpoint = f'{self.http_protocol}{self.url}/api/robots/{self.robot_id}'
        RobotData = requests.get(endpoint, headers=self.headers)
        print(RobotData.json())
        self.robot = Robot(RobotData.json())
        return self.robot

    def pause_execution(self):
        """ This method is used to pause the execution. """

        if self.create_virtual_env.poll() is None:
            self.create_virtual_env.send_signal(signal.SIGSTOP)
        if self.install_packages_process.poll() is None:
            self.install_packages_process.send_signal(signal.SIGSTOP)
        if self.run_robot_process.poll() is None:
            self.run_robot_process.send_signal(signal.SIGSTOP)

        self.send_log("Execution Paused")

    def resume_execution(self):
        """ This method is used to resume the execution. """

        if self.create_virtual_env.poll() is None:
            self.create_virtual_env.send_signal(signal.SIGCONT)
        if self.install_packages_process.poll() is None:
            self.install_packages_process.send_signal(signal.SIGCONT)
        if self.run_robot_process.poll() is None:
            self.run_robot_process.send_signal(signal.SIGCONT)
        self.send_log("Execution Resumed")

    def stop_execution(self):
        """ This method is used to stop the execution. """

        if self.create_virtual_env.poll() is None:
            self.create_virtual_env.send_signal(signal.SIGKILL)
        if self.install_packages_process.poll() is None:
            self.install_packages_process.send_signal(signal.SIGKILL)
        if self.run_robot_process.poll() is None:
            self.run_robot_process.send_signal(signal.SIGKILL)
        self.send_log("Execution Stopped")

    def create_virtual_env(self):
        """ This method is used to create the virtual environment. """

        if not os.path.exists(f"{self.robot_folder}/venv"):
            os.makedirs(f"{self.robot_folder}/venv")

        command = f"python3 -m venv {self.robot_folder}/venv"
        self.create_virtuaenv_process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                                         shell=True)
        out, err = self.create_virtuaenv_process.communicate()
        if err:
            self.send_log(err.decode(), "systemException")
            self.finish_execution()
        else:
            self.send_log("Packages installed successfully")

    def copy_repo(self):
        """ This method is used to copy the robot repository. """

        endpoint = f'{self.http_protocol}{self.url}/api/git'
        gitData = requests.get(endpoint, headers=self.headers)
        print()
        git_username = gitData.json()[0]['git_username']
        git_token = gitData.json()[0]['git_token']
        account = self.robot.repoUrl.split("/")[-2]
        repo = self.robot.repoUrl.split("/")[-1]
        self.remote = f"https://{git_username}:{git_token}@github.com/{account}/{repo}"
        print(self.remote)
        try:
            if os.path.exists(f"{self.robot_folder}/.git"):
                self.send_log(f"Pulling repo from {self.robot.repoUrl}")
                git.cmd.Git(self.robot_folder).pull(self.robot.repoUrl, self.branch)
                self.send_log("Repo pulled successfully")
            else:
                self.send_log(f"Cloning repo from {self.robot.repoUrl}")
                Repo.clone_from(self.remote, self.robot_folder, branch=self.branch)
                self.send_log("Repo cloned successfully")
        except Exception as e:
            self.send_log(e, "systemException")
            self.send_log("Execution Failed", "systemException")

    def install_packages(self):
        """ This method is used to install the packages from requirements.txt robot file """

        while True:
            # wait for the virtual enviroment to be created
            if os.path.exists(f'{self.robot_folder}/venv/bin/pip3'):
                break
            time.sleep(1)

        command = f'{self.robot_folder}/venv/bin/pip3 install -r {self.robot_folder}/requirements.txt'
        self.install_packages_process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                                         shell=True, encoding='utf-8', errors='replace')
        out, err = self.install_packages_process.communicate()
        if err:
            self.send_log(err.decode(), "systemException")
            self.finish_execution()
        else:
            self.send_log("Packages installed successfully")

    def run_robot(self):
        """
        Create a subprocess that run robot process with the given arguments
        """
        args = {"RobotId": self.robot_id,
                "url": self.url,
                "token": self.token,
                "ExecutionId": self.execution_id,
                'params': self.robot_params}

        command = f"{self.robot_folder}/venv/bin/python3 {self.robot_folder}/main.py \"{args}\""

        self.run_robot_process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = self.run_robot_process.communicate()
        if err:
            self.send_log(err.decode(), "systemException")
            self.finish_execution()

    def finish_execution(self):
        """
        finish robot execution and send the result to the server
        """
        self.robot_id = None
        self.send_log("Execution Finished")

    def set_status(self, status: str):
        """Set status of robot execution in the robot manager"""
        endpoint = f'{self.http_protocol}{self.url}/api/executions/{self.execution_id}'

        requests.put(endpoint, data={'status': status}, headers=self.headers)

    def send_log(self, message, log_type="log"):
        """
        send log to robot manage console
        Arguments:
            message {string} -- message to send
            log_type {string} -- type of the log
        """

        endpoint = f'{self.http_protocol}{self.url}/api/logs/'
        log_data = {
            "LogType": log_type,
            "LogData": message,
            "ExecutionId": self.execution_id,
            "LogId": ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(64)),
            "DateTime": datetime.datetime.now()
        }
        try:
            requests.post(endpoint, log_data, headers=self.headers)
        except Exception as e:
            print(e)

