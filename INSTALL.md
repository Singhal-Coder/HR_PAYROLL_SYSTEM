# Installation Guide

This project uses pinned Python and dependency versions to ensure a stable,
reproducible setup across platforms.

IMPORTANT:
This project depends on face_recognition → dlib, which is sensitive to OS,
Python version, and system libraries. Follow the instructions for your OS only.

-------------------------------------------------------------------------------

SUPPORTED PLATFORMS

- Linux (Ubuntu / Mint) — Recommended
- Windows — Use WSL2 (Ubuntu)
- macOS (Intel / Apple Silicon) — Supported with extra steps

-------------------------------------------------------------------------------

COMMON REQUIREMENTS (ALL PLATFORMS)

- Python 3.10.x (NOT 3.12+)
- Virtual environment (.venv)
- Internet connection

The project enforces:
- Python >= 3.9, < 3.12
- numpy < 2
- opencv-python < 4.9

-------------------------------------------------------------------------------

LINUX (UBUNTU / MINT) — RECOMMENDED

1. Install system dependencies

sudo apt update
sudo apt install -y \
  cmake build-essential \
  libssl-dev zlib1g-dev libbz2-dev \
  libreadline-dev libsqlite3-dev \
  libncursesw5-dev libffi-dev \
  xz-utils tk-dev

Verify:
cmake --version

-------------------------------------------------------------------------------

2. Install pyenv

curl https://pyenv.run | bash

Add pyenv to shell startup:
nano ~/.bashrc

Append at the end:
export PYENV_ROOT="$HOME/.pyenv"
export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init - bash)"

Restart shell:
exec "$SHELL"

Verify:
pyenv --version

-------------------------------------------------------------------------------

3. Install Python 3.10

pyenv install 3.10.14
pyenv local 3.10.14

Verify:
python --version

-------------------------------------------------------------------------------

4. Create and activate virtual environment

python -m venv .venv
source .venv/bin/activate

-------------------------------------------------------------------------------

5. Install Python dependencies

pip install -r requirements.txt

-------------------------------------------------------------------------------

WINDOWS (USE WSL2 — RECOMMENDED)

Native Windows Python is NOT recommended.

1. Install WSL2 (PowerShell as Administrator)

wsl --install

Reboot when prompted.

-------------------------------------------------------------------------------

2. Install Ubuntu from Microsoft Store

Install Ubuntu 22.04 LTS and open Ubuntu terminal.

-------------------------------------------------------------------------------

3. Inside Ubuntu, follow ALL Linux steps above.

-------------------------------------------------------------------------------

MACOS (INTEL & APPLE SILICON)

1. Install Xcode Command Line Tools

xcode-select --install

-------------------------------------------------------------------------------

2. Install Homebrew (if not installed)

/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

-------------------------------------------------------------------------------

3. Install system dependencies

brew install cmake openssl readline sqlite3 xz zlib

-------------------------------------------------------------------------------

4. Install pyenv

brew install pyenv

Add to shell startup (~/.zshrc or ~/.bashrc):

export PYENV_ROOT="$HOME/.pyenv"
export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init -)"

Restart shell.

-------------------------------------------------------------------------------

5. Install Python 3.10

pyenv install 3.10.14
pyenv local 3.10.14

-------------------------------------------------------------------------------

6. Create virtual environment and install dependencies

python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

NOTE:
On Apple Silicon, dlib may compile from source and take time.

-------------------------------------------------------------------------------

VERIFICATION (ALL PLATFORMS)

pip list | grep -E "numpy|opencv|dlib|face-recognition"

Expected:
numpy            1.26.x
opencv-python    4.8.x
dlib             20.0.0
face-recognition 1.3.0

-------------------------------------------------------------------------------

NOTES

- Do NOT use Python 3.12+
- Do NOT upgrade dependencies blindly
- Do NOT commit .venv/

Add to .gitignore:
.venv/

-------------------------------------------------------------------------------

PHILOSOPHY

This setup is intentionally boring and conservative.
Stable environments > latest versions.