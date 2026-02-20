# Baseband Log Analyzer (bbla)

Baseband Log Analyzer is a lightweight engineering tool for collecting
and summarizing Ericsson Baseband logs via MoShell.

It connects to a Baseband, collects key diagnostic logs, generates a
compact hardware-focused report, and optionally uploads the full case to
an SFTP server.

---

## ✨ Features

- Connects to MoShell 
- Collects:
  - `hwpid`
  - `llog -l`
  - `lga`
- Stores raw command outputs
- Generates a compact engineering report
- Filters alarm noise via JSON configuration
- Supports multiple passwords
- Optional automatic SFTP upload
- Fully modular Python architecture
- Includes pytest-based unit tests

---

# 📦 Installation

## ✅ Recommended (User machine): pipx

Best option for production usage.

### 1) Install pipx (Debian/Ubuntu)

    sudo apt update
    sudo apt install -y pipx
    pipx ensurepath
    # restart terminal

### 2) Install bbla

    pipx install git+https://github.com/godswork/baseband-log-analyzer.git

### 3) Create configuration directory

    mkdir -p ~/.config/bbla

Create required `secrets.json`:

    cat > ~/.config/bbla/secrets.json <<'JSON'
    {
      "baseband": {
        "username": "rbs",
        "passwords": ["rbs", "rbs2", "rbs3"]
      },
      "sftp": {
        "password": ""
      }
    }
    JSON

Optional `sftp.json`:

    cat > ~/.config/bbla/sftp.json <<'JSON'
    {
      "enabled": false,
      "host": "",
      "port": 22,
      "username": "",
      "remote_base_dir": ""
    }
    JSON

Optional `alarm_filter.json`:

    cat > ~/.config/bbla/alarm_filter.json <<'JSON'
    {
      "noise_exact": [],
      "noise_prefix": []
    }
    JSON

### 4) Run

    bbla 169.254.2.2

### Update later

    pipx upgrade baseband-log-analyzer

---

## 🔧 Alternative: Development install (venv)

    git clone https://github.com/godswork/baseband-log-analyzer.git
    cd baseband-log-analyzer
    python3 -m venv .venv
    source .venv/bin/activate
    python -m pip install -U pip
    pip install -e .

Run:

    bbla 169.254.2.2

---

# ⚙ Configuration

bbla searches for configuration files in this order:

1. $BBLA_CONFIG_DIR  
2. $XDG_CONFIG_HOME/bbla  
3. ~/.config/bbla  

Override config directory:

    bbla 169.254.2.2 --config-dir /path/to/configs

Or:

    export BBLA_CONFIG_DIR=/path/to/configs
    bbla 169.254.2.2

Required file:

- secrets.json

Optional:

- sftp.json
- alarm_filter.json

---

# 🚀 Usage

Basic:

    bbla 169.254.2.2

Disable upload:

    bbla 169.254.2.2 --no-upload

Custom output directory:

    bbla 169.254.2.2 --out ~/cases

---

# 📁 Output Structure

Case folder format:

    <Market>_<Revision>_<Serial>_<YYYYMMDD_HHMMSS>/

Inside:

    raw/
      hwpid.txt
      llog.txt
      lga.txt
    report.txt
    case.json

---

# 🧪 Running Tests

    pytest

---

# 🛠 Requirements

- Python ≥ 3.10
- MoShell installed locally
- Network access to Baseband (SSH port 22)
- pexpect
- paramiko (only if SFTP enabled)

---

# 👤 Author

godswork
