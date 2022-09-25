import json
from robot import Runner


class Server(Runner):
    def __init__(self):
        self.thread = None
        self.status = "free"
        kwargs = self.__get_config_data()
        super().__init__(**kwargs)
        self.data = None

    def run(self, data):
        self.data = data
        self.status = "running"
        self.set_robot(self.data)
        self.send_log("Execution Started")
        self.copy_repo()
        self.run_robot()
        self.status = "free"

    def pause(self):
        self.staus = "paused"
        try:
            self.pause_execution()
        except:
            print("Unable to pause execution.")

    def resume(self):
        self.status = "running"
        try:
            self.resume_execution()
        except:
            print("Unable to pause resume.")

    def stop(self):
        self.status = "free"
        try:
            self.stop_execution()
        except:
            print("Unable to stop execution.")

    def __get_config_data(self):
        kwargs = {}
        config_file = open('config.json', 'r')
        data = config_file.read()
        if data:
            json_data = json.loads(data)
            kwargs['token'] = json_data['token']
            kwargs['url'] = json_data['url']
            kwargs['machine_id'] = json_data['machine_id']
            kwargs['license_key'] = json_data['license_key']
            kwargs['folder'] = json_data['folder']
        else:
            kwargs['username'] = input("Enter username:")
            kwargs['password'] = input("Enter Password:")
            kwargs['url'] = input("Enter console url:")
            kwargs['machine_id'] = input("Enter machine id:")
            kwargs['license_key'] = input("Enter licenseKey:")
            kwargs['folder'] = input("Enter process folder:")
        kwargs['server'] = self

        return kwargs

