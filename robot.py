import datetime
import random
import signal
import string
import subprocess
import sys

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
        self.run_robot_process = None
        self.branch = None
        self.url = self.__clean_url(kwargs.get("url"))
        self.machine_id = kwargs.get("machine_id")
        self.license_key = kwargs.get("license_key")
        self.folder = kwargs.get("folder")
        self.server = kwargs.get("server")
        self.token = kwargs.get("token")
        self.headers = {'Authorization': f'Token {self.token}'}
        self.http_protocol = self.__get_http_protocol()
        self.__get_network()
        self.port = 8088
        self.set_machine_ip()

    def __get_network(self):
        """ This method is used to get the ip network of the robot. """
        self.ip = os.popen('curl -s ifconfig.me').readline()

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
        self.branch = data["branch"]

        if data['params']:
            self.robot_params = data['params']
        else:
            self.robot_params = "None"

        self.get_robot_data()

        self.set_robot_folder()


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
        self.robot = Robot(RobotData.json())
        return self.robot

    def pause_execution(self):
        """ This method is used to pause the execution. """
        if self.run_robot_process.poll() is None:
            os.killpg(self.run_robot_process.pid, signal.SIGSTOP)
            self.send_log("Execution Paused")

    def resume_execution(self):
        """ This method is used to resume the execution. """
        if self.run_robot_process.poll() is None:
            os.killpg(self.run_robot_process.pid, signal.SIGCONT)
            self.send_log("Execution Resumed")

    def stop_execution(self):
        """ This method is used to stop the execution. """

        if self.run_robot_process.poll() is None:
            os.killpg(self.run_robot_process.pid, signal.SIGKILL)
            self.send_log("Execution Stopped")

    def copy_repo(self):
        """ This method is used to copy the robot repository. """

        endpoint = f'{self.http_protocol}{self.url}/api/git'

        gitData = requests.get(endpoint, headers=self.headers)

        git_username = gitData.json()[0]['git_username']
        git_token = gitData.json()[0]['git_token']
        account = self.robot.repoUrl.split("/")[-2]
        repo = self.robot.repoUrl.split("/")[-1]
        self.remote = f"https://{git_username}:{git_token}@github.com/{account}/{repo}"
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
            self.send_log(e.__str__(), "syex")
            raise Exception(e)

    def run_robot(self):
        """
        Create a subprocess that run robot process with the given arguments
        """
        self.send_log("Running the process")
        args = {"RobotId": self.robot_id,
                "url": self.http_protocol + self.url,
                "token": self.token,
                "ExecutionId": self.execution_id,
                'params': self.robot_params}

        WIN_commands = [f"py -m venv {self.robot_folder}\\venv",
                        f"{self.robot_folder}\\venv\\Scripts\\activate",
                        f"py -m pip install -r {self.robot_folder}\\requirements.txt",
                        f"python {self.robot_folder}\\main.py \"{args}\""]

        OS_commands = [f"python3 -m venv {self.robot_folder}/venv",
                       f"{self.robot_folder}/venv/bin/pip3 install -r {self.robot_folder}/requirements.txt",
                       f"{self.robot_folder}/venv/bin/python3 {self.robot_folder}/main.py \"{args}\""]

        command = " && ".join(OS_commands)
        self.run_robot_process = subprocess.Popen(command,
                                                  shell=True,
                                                  bufsize=1,
                                                  stdout=subprocess.PIPE,
                                                  stderr=subprocess.STDOUT,
                                                  encoding='utf-8',
                                                  errors='replace',
                                                  preexec_fn=os.setsid)
        while True:
            realtime_output = self.run_robot_process.stdout.readline()
            if realtime_output == '' and self.run_robot_process.poll() is not None:
                break
            if realtime_output:
                if "error" in realtime_output.strip().lower():
                    self.send_log(realtime_output.strip(), "syex")
                else:
                    pass
                    #self.send_log(realtime_output.strip())
                sys.stdout.flush()
        self.finish_execution()
        if self.run_robot_process.returncode != 0:
            raise Exception("Error in the execution")

    def finish_execution(self):
        """
        finish robot execution and send the result to the server
        """

        self.robot_id = None
        self.send_log("Execution Finished")

    def set_status(self, status: str):
        """Set status of robot execution in the robot manager"""
        endpoint = f'{self.http_protocol}{self.url}/api/executions/{self.execution_id}/set_status/'

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
            raise e
