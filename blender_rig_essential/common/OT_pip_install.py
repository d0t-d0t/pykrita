# coding=utf-8
# SPDX-FileCopyrightText: 2025 Marco Melletti <mellotanica@gmail.com>
#
# SPDX-License-Identifier: GPL-2.0-or-later

import sys
import platform
import ssl
import subprocess
from pathlib import Path
import runpy
from urllib import request
import json
from PyQt5.QtWidgets import QMessageBox

from krita import Krita


def _get_local_pip_path():
    local_pip_path = str(
        Path(Krita.instance().getAppDataLocation()) / "local_python" / "site-package"
    )
    print(local_pip_path)
    return local_pip_path


def setup_python_path():
    sys.path.insert(0, _get_local_pip_path())

def ensure_requirements_are_installed(package_name):
    sonicvisionsdir =Path(r'C:\Users\d0t\AppData\Roaming\krita\pykrita') #Path(__file__).parent

    # search for an already downloaded pip wheel
    pip = None
    for file in sonicvisionsdir.iterdir():
        if file.name.startswith("pip-") and file.suffix == ".whl":
            pip = file
            break

    # retrieve pip wheel from the internet
    if pip is None:
        ctx = None
        if platform.system() == "Darwin":
            pemfile = str(Path(Krita.instance().getAppDataLocation()) /"SystemRootCerts.pem")
            subprocess.run(["security", "export", "-t", "certs", "-f", "pemseq", "-k", "/System/Library/Keychains/SystemRootCertificates.keychain",  "-o", pemfile])
            ctx = ssl.create_default_context(cafile=str(pemfile))
        resp = request.urlopen("https://pypi.org/pypi/pip/json", context=ctx)
        jdata = json.loads(resp.read())
        for url in jdata["urls"]:
            if url["packagetype"] == "bdist_wheel":
                pipurl = url["url"]
                resp = request.urlopen(pipurl, context=ctx)
                pip = sonicvisionsdir / Path(pipurl).name
                with open(pip, "wb") as pipwheel:
                    pipwheel.write(resp.read())

    # add pip wheel to the python path
    sys.path.append(str(pip))

    def exit_func(exit_code=0):
        return exit_code

    # store original exit function and argument vector
    orig_argv = sys.argv
    orig_exit = sys.exit

    # update args to install requirements
    sys.exit = exit_func
    sys.argv = [
        "pip",
        "install",
        "-t",
        _get_local_pip_path(),
        package_name,
    ]

    runpy.run_module("pip", run_name="__main__")

    # restore proper environment
    sys.exit = orig_exit
    sys.argv = orig_argv

    # notify the user that another restart is required
    messageBox = QMessageBox()
    messageBox.setWindowTitle(f"{package_name} Install")
    messageBox.setText(f"{package_name} required dependencies has been installed.")
    messageBox.setInformativeText(
        "Please restart Krita to start using the plugin."
    )
    messageBox.setStandardButtons(QMessageBox.Close)
    messageBox.setIcon(QMessageBox.Information)
    messageBox.exec()
  
ensure_requirements_are_installed('svgpathtools')