# ⚡ ZORA SNIPPER

Zora Snipper is a Python-based automation tool that runs multiple sniping modes.
This guide explains how to install, set up, and run the project step by step
using terminal commands only.

---

# ================================
# 1. UPDATE SYSTEM & INSTALL PYTHON
# ================================

apt update && apt upgrade -y

# Install Python 3
apt install python3 -y

# Install pip (if not installed)
apt install python3-pip -y

# Install git (if not installed)
apt install git

# Install script
git clone https://github.com/0xvans/zorasnipper
# ================================
# 2. VERIFY INSTALLATION
# ================================

python3 --version
pip3 --version


# ================================
# 3. CREATE VIRTUAL ENVIRONMENT
# ================================

python3 -m venv venv


# ================================
# 4. ACTIVATE VIRTUAL ENVIRONMENT
# ================================

source venv/bin/activate

# After activation, your terminal should look like:
# (venv) root@server:~#


# ================================
# 5. INSTALL PROJECT DEPENDENCIES
# ================================

pip install -r requirements.txt


# ================================
# 6. RUN ZORA SNIPPER
# ================================

# Choose ONE of the following commands:

# Run target snipping mode
python3 target.py

# Run random snipping mode
python3 randomsnip.py

# Run target post snipping mode
python3 targetpost.py


# ================================
# 7. STOP RUNNING SCRIPT
# ================================

# Press:
CTRL + C


# ================================
# 8. EXIT VIRTUAL ENVIRONMENT
# ================================

deactivate
