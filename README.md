# 📂 Bulk File Renamer

[![Python Version](https://img.shields.io/badge/python-3.6+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Status](https://img.shields.io/badge/status-active-success.svg)](https://github.com/yourusername/bulk-file-renamer)

A powerful command-line tool for renaming multiple files at once. Supports pattern-based renaming, find-and-replace operations, regular expressions, automatic date formatting, incremental numbering, and more!

<div align="center">

![Demo Animation](https://via.placeholder.com/700x400?text=Bulk+File+Renamer+Demo)

</div>

## ✨ Features

- 📁 **Bulk Renaming**: Rename multiple files at once with a single command
- 🔍 **Flexible File Selection**: Select files by name, pattern, or custom criteria
- 🧩 **Pattern Templates**: Use variables like `{date}`, `{count}`, `{origname}` in file naming
- 🔄 **Find & Replace**: Simple string or powerful regex replacement options
- 🌲 **Recursive Mode**: Process files in subdirectories
- 👁️ **Preview Mode**: See changes before applying them
- 💾 **Backup System**: Automatic backup of files before renaming
- ⏪ **Rollback Support**: Easy undo of the last rename operation
- 📝 **Operation History**: Track all renaming operations with timestamps
- 🔒 **Safe Operations**: Checks for conflicts and duplicates


## 🚀 Installation

1. Clone this repository:
```bash
git clone https://github.com/yourusername/bulk-file-renamer.git
cd bulk-file-renamer
```

2. No external dependencies required! This tool uses only Python standard libraries.

## 📖 Quick Start

### Basic Renaming

```bash
# Rename all .jpg files to a numbered sequence
python main.py -p "*.jpg" -n "photo_{count:3}.jpg"

# Rename specific files
python main.py -f "img1.png" "img2.png" -n "image_{count}.png"

# Find and replace text in filenames
python main.py -p "*.txt" --find "old" --replace "new"
```

### Advanced Renaming

```bash
# Add date prefix to all text files
python main.py -p "*.txt" -n "{date}_{origname}.{ext}"

# Use regular expressions to remove numbers from filenames
python main.py -p "*" --find "[0-9]+" --replace "" --regex

# Recursively rename all PNG files in subdirectories
python main.py -p "*.png" -r -n "image_{count:4}.png"
```

### Safety Features

```bash
# Preview changes without renaming
python main.py -p "*.jpg" -n "new_{origname}.jpg" --preview

# Create backup before renaming
python main.py -f "file1.txt" "file2.txt" -n "{datetime}_{origname}.{ext}" --backup

# Rollback the last rename operation
python main.py --rollback
```

## 🎛️ Command Line Arguments

### File Selection

| Argument | Description | Example |
|----------|-------------|---------|
| `-f`, `--files` | Specific files to rename | `-f "img1.jpg" "img2.jpg"` |
| `-p`, `--pattern` | File patterns to match | `-p "*.jpg" "*.png"` |
| `-r`, `--recursive` | Search files recursively | `-r` |

### Renaming Options

| Argument | Description | Example |
|----------|-------------|---------|
| `-n`, `--name` | New filename pattern | `-n "photo_{count}.jpg"` |
| `--find` | String to find in filenames | `--find "old"` |
| `--replace` | String to replace with | `--replace "new"` |
| `--regex` | Use regex for find/replace | `--regex` |
| `-i`, `--case-insensitive` | Case insensitive find/replace | `-i` |

### Operation Options

| Argument | Description | Example |
|----------|-------------|---------|
| `--preview` | Preview changes without renaming | `--preview` |
| `--backup` | Create backup of files before renaming | `--backup` |
| `--backup-dir` | Custom backup directory | `--backup-dir "my_backups"` |
| `--log` | Custom log file path | `--log "rename_history.json"` |
| `--rollback` | Rollback the last rename operation | `--rollback` |
| `--history` | Show rename history | `--history` |
| `--clear-history` | Clear rename history | `--clear-history` |
| `--history-limit` | Limit history display to N entries | `--history-limit 20` |
| `-v`, `--verbose` | Verbose output | `-v` |

### Help Options

| Argument | Description | Example |
|----------|-------------|---------|
| `--patterns` | Show available special patterns | `--patterns` |
| `--examples` | Show usage examples | `--examples` |
| `--version` | Show version information | `--version` |

## 🧩 Special Patterns

Use these special patterns in your filename templates:

### Date/Time Patterns

| Pattern | Description | Example Output |
|---------|-------------|----------------|
| `{YYYY}` | Year | `2024` |
| `{MM}` | Month | `01` |
| `{DD}` | Day | `15` |
| `{hh}` | Hour | `21` |
| `{mm}` | Minute | `45` |
| `{ss}` | Second | `30` |
| `{date}` | Date in YYYY-MM-DD format | `2024-01-15` |
| `{time}` | Time in HH-MM-SS format | `21-45-30` |
| `{datetime}` | Full timestamp | `2024-01-15_21-45-30` |

### Special Value Patterns

| Pattern | Description | Example Output |
|---------|-------------|----------------|
| `{count}` | Incremental counter | `1`, `2`, `3`... |
| `{count:3}` | Zero-padded counter | `001`, `002`, `003`... |
| `{random}` | 5 random alphanumeric characters | `8fK2x` |
| `{random:10}` | 10 random alphanumeric characters | `a7Bz9X4c2Y` |
| `{ext}` | Original file extension | `jpg` |
| `{origname}` | Original filename without extension | `photo` |

## 🛠️ Examples with Results

### Example 1: Basic Numbering

Command:
```bash
python main.py -p "*.jpg" -n "photo_{count:3}.jpg"
```

Results:
```
Original files:
  IMG_1234.jpg
  vacation.jpg
  screenshot.jpg

Renamed to:
  photo_001.jpg
  photo_002.jpg
  photo_003.jpg
```

