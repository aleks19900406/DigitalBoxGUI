import subprocess

subprocess.run(
    "conda activate NewDasVersion && python -m tester.executables.test", shell=True
)