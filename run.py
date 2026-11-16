"""Single-command cross-platform setup and launch: python run.py"""
from pathlib import Path
import subprocess, sys
ROOT=Path(__file__).resolve().parent

def run(args):
    subprocess.run(args,cwd=ROOT,check=True)

if __name__=='__main__':
    run([sys.executable,'-m','pip','install','-r','requirements.txt'])
    run([sys.executable,'-m','src.ingest'])
    run([sys.executable,'-m','streamlit','run','app.py'])
