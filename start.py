#!/usr/bin/env python3
"""Local bootstrap. Copyright (c) 2026 Min SiThu (devminsithu). MIT."""
import os
from pathlib import Path
import subprocess
import sys
import venv

ROOT=Path(__file__).resolve().parent

def main():
    if sys.version_info < (3,11):
        print('Install Python 3.11 or newer from https://www.python.org/downloads/');return 1
    os.chdir(ROOT)
    env=ROOT/'.venv'
    python=env/('Scripts/python.exe' if os.name=='nt' else 'bin/python')
    if not python.exists(): venv.EnvBuilder(with_pip=True).create(env)
    def run(*args):subprocess.run([str(python),*args],check=True)
    run('-m','pip','install','-r','requirements.txt')
    run('manage.py','migrate','--noinput')
    run('manage.py','seed_demo')
    run('manage.py','check')
    if '--check' in sys.argv:return 0
    result=subprocess.run([str(python),'manage.py','shell','-c','from django.contrib.auth.models import User; print(User.objects.filter(is_superuser=True).exists())'],capture_output=True,text=True,check=True)
    if 'True' not in result.stdout:
        print('Create your academy owner account. Choose your own username and password.')
        run('manage.py','createsuperuser')
    print('Open http://127.0.0.1:8000 — press Control+C to stop. Local use only.')
    run('manage.py','runserver','127.0.0.1:8000','--noreload')
    return 0

if __name__=='__main__':
    try:sys.exit(main())
    except KeyboardInterrupt:print('Stopped.')
    except subprocess.CalledProcessError:
        print('Setup stopped. Check the error above. Internet is needed to install dependencies.');sys.exit(1)
