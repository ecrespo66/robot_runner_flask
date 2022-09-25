import signal
import subprocess


if __name__ == "__main__":
#
    command = "python /Users/enriquecrespodebenito/Documents/GitHub/robot_runner_flask/test.py"

    p = subprocess.Popen(command,
                     shell=True,
                     bufsize=1,
                     stdout=subprocess.PIPE,
                     stderr=subprocess.STDOUT,
                     encoding='utf-8',
                     errors='replace')

    while True:
        realtime_output = p.stdout.readline()
        if realtime_output == '' and p.poll() is not None:
            break
        if realtime_output:
            print(realtime_output.strip())
            print(p.pid)
