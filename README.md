# Baseband Log Analyzer (bbla)

Baseband Log Analyzer is a lightweight engineering tool for collecting
and summarizing Ericsson Baseband logs via MoShell.

It connects to a Baseband, collects key diagnostic logs, generates a
compact hardware-focused report, and optionally uploads the full case to
an SFTP server.

------------------------------------------------------------------------

## ✨ Features

-   Connects to MoShell and logs in (`lt all`)
-   Collects:
    -   `hwpid`
    -   `llog -l`
    -   `lga`
-   Stores raw command outputs
-   Generates a compact engineering report
-   Filters alarm noise via JSON configuration
-   Supports multiple Baseband passwords (sequential fallback)
-   Optional automatic SFTP upload
-   Fully modular Python architecture
-   Includes pytest-based unit tests

------------------------------------------------------------------------

## 📦 Installation

Clone the repository:

    git clone https://github.com/godswork/baseband-log-analyzer.git
    cd baseband-log-analyzer

Install in editable mode:

    python3 -m pip install -e .

For development (tests):

    python3 -m pip install -r requirements-dev.txt

------------------------------------------------------------------------

## 🚀 Usage

Run:

    bbla 169.254.2.2

Disable upload:

    bbla 169.254.2.2 --no-upload

Custom output directory:

    bbla 169.254.2.2 --out ~/cases

------------------------------------------------------------------------

## 📁 Output Structure

Case folder format:

    <Market>_<Revision>_<Serial>_<YYYYMMDD_HHMMSS>/

Inside:

    raw/
      hwpid.txt
      llog.txt
      lga.txt
    report.txt
    case.json

-   `raw/` --- unmodified command outputs\
-   `report.txt` --- compact engineering summary\
-   `case.json` --- metadata, timings, login status, upload result

------------------------------------------------------------------------

## ⚙ Configuration

All configuration files are located in:

    configs/

Copy example configs first:

    cp configs/secrets.example.json configs/secrets.json
    cp configs/sftp.example.json configs/sftp.json
    cp configs/alarm_filter.example.json configs/alarm_filter.json

### 🔐 secrets.json

Example:

{ "baseband": { "username": "rbs", "passwords": \["rbs", "rbs2",
"rbs3"\] }, "sftp": { "password": "your_sftp_password" } }

-   Supports multiple Baseband passwords\
-   Passwords are tried sequentially

### 📡 sftp.json

Example:

{ "enabled": true, "host": "sftp.example.com", "port": 22, "username":
"user", "remote_base_dir": "/upload/bb-cases" }

### 🚫 alarm_filter.json

Used to suppress known non-relevant alarms.

Example:

{ "noise_exact": \[ "SFP Not Present", "License Key File Fault" \],
"noise_prefix": \[ "Certificate Management" \] }

This allows dynamic tuning without modifying source code.

------------------------------------------------------------------------

## 🧠 Report Philosophy

The report is intentionally minimal.

It highlights:

-   Crash-like restarts (signal, program, PMD present)
-   Potentially important alarms (after filtering noise)

It is not meant to replace full manual log analysis.\
It is meant to provide immediate hardware-oriented insight.

------------------------------------------------------------------------

## 🧪 Running Tests

    pytest

Tests cover:

-   llog parser
-   lga parser
-   restart detection logic
-   alarm filtering
-   report rendering

------------------------------------------------------------------------

## 🛠 Requirements

-   Python ≥ 3.10
-   MoShell installed locally
-   Network access to Baseband (SSH port 22)
-   pexpect
-   paramiko (only if SFTP enabled)

------------------------------------------------------------------------

## ⚠ Common Issues

### "Unable to connect to `<IP>`{=html}:22"

The Baseband is unreachable or SSH is not available.

Check:

    ping <IP>
    nc -vz <IP> 22

------------------------------------------------------------------------

## 📜 License

MIT License

------------------------------------------------------------------------

## 👤 Author

godswork
