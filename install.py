import subprocess
import sys

def install(package):
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])

packages = [
    "psutil",
    "pyperclip",
    "python-whois",
]

for package in packages:
    install(package)
