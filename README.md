# Team Formation System

An intelligent team formation system that assigns students to teams of 5-6 people and assigns each team to a project based on their preferences and constraints.

## Overview

The system processes student preferences and forms optimal teams while respecting:
- **Subteam preferences**: Students who want to work together stay together
- **Project preferences**: Teams are assigned to projects in everyone's top 5 choices
- **Team size constraints**: All teams have exactly 5-6 members
- **Preference optimization**: Maximizes overall satisfaction

### Algorithm Features

1. **Mutual Subteam Detection**: Identifies groups where all members mutually list each other
2. **Smart Merging**: Combines smaller subteams based on compatible project preferences
3. **Fuzzy Matching**: Handles typos and case inconsistencies in netIDs
4. **Optimal Assignment**: Assigns each team to their best possible project
5. **Comprehensive Validation**: Tests data quality and output format

## Input Format

The input is a CSV file (`cse403-preferences.csv`) with:
- **Column D**: Student netID (unique identifier)
- **Columns E-AY**: Project preferences (47 projects, ranked 1-5)
- **Columns AZ-BE**: Subteam member preferences (up to 6 members)

## Output Format

The system generates three files:

1. **`out.csv`**: Team assignments in format: `project_name,[member1, member2, ...]`
2. **`report.txt`**: Detailed summary with statistics and analysis
3. **`team_formation.log`**: Complete processing log with timestamps

## Quick Start

### Local Execution

```bash
# Simple run (uses defaults)
./run.sh

# Or run Python directly
python3 team_formation.py cse403-preferences.csv out.csv

# With verbose logging
python3 team_formation.py -v cse403-preferences.csv out.csv

# Run tests only
python3 team_formation.py --test cse403-preferences.csv
```

### Command Line Options

```
python3 team_formation.py [options] [input_file] [output_file]

Positional Arguments:
  input_file          Input CSV file (default: cse403-preferences.csv)
  output_file         Output CSV file (default: out.csv)

Optional Arguments:
  -i, --input FILE    Input CSV file (alternative to positional)
  -o, --output FILE   Output CSV file (alternative to positional)
  -v, --verbose       Enable verbose (DEBUG level) logging
  --test              Run validation tests before processing
  --no-report         Skip generating report.txt
  -h, --help          Show help message
```

## How It Works

### Processing Pipeline

1. **Parse Input**: Read CSV and extract netIDs, project preferences, subteam preferences
2. **Validate Data**: Check for duplicates, missing data, format issues (with fuzzy matching)
3. **Identify Subteams**: Find groups where all members mutually list each other
4. **Classify Teams**: Separate complete (5-6) from incomplete (1-4) subteams
5. **Merge Subteams**: Combine smaller subteams with compatible project preferences
6. **Assign Projects**: Assign each team to their most preferred common project
7. **Optimize & Validate**: Verify assignments are optimal and satisfy all constraints
8. **Generate Output**: Write CSV, report, and log files

### Key Features

- **Fuzzy Matching**: Automatically corrects case differences and typos in netIDs
- **Data Cleaning**: Normalizes email formats, handles inconsistent formatting
- **Quality Tracking**: Logs all data issues and how they were resolved
- **Optimality Verification**: Confirms assignments minimize aggregate preference scores
- **Comprehensive Testing**: Built-in test suite validates pipeline at each stage

### Expected Results

With the provided `cse403-preferences.csv`:
- **~12-15 teams** formed successfully
- **~65-75%** of students placed in teams
- **~25-35%** unmatched (no compatible preferences with others)
- **~60-70%** of students get their #1 choice
- **~85-90%** get their top 3 choices

## Generated Files

After running, you'll find:

1. **`out.csv`**: Team assignments (required output)
   - Format: `project_name,[member1, member2, member3, ...]`
   - Example: `ShelterLink,[amarto, azitab, cbither, elijoshi, spenj]`
   - Validated to be readable by pandas DataFrame

2. **`report.txt`**: Detailed summary report including:
   - Overall statistics (teams formed, students placed/unmatched)
   - Preference satisfaction distribution
   - Assignment optimization analysis
   - Data quality issues found and resolved
   - Complete team assignments with scores
   - List of unmatched students

3. **`team_formation.log`**: Processing log with timestamps
   - INFO: Progress messages
   - WARNING: Data quality issues, unmatched students
   - ERROR: Constraint violations
   - DEBUG: Detailed processing (use `--verbose` flag)

## Docker Execution

The `run.sh` script is designed to work in Docker containers.

### Output Schema

`out.csv` has the schema: `(project_name, [member1, member2, ...])`

Example row:
```csv
CookiesShallNotPass,"[m1, m2, m3, m4, m5, m6]"
```

This means team `[m1, m2, m3, m4, m5, m6]` is assigned to project `CookiesShallNotPass`.

**Note**: The output is validated using pandas DataFrame to ensure it can be parsed correctly.

### Linux or macOS (bash/zsh)

You should be able to run the following cmd.
Your `run.sh` should generate an `out.csv` and save it at your `/workspace/out.csv`.
Try the following command and see if you can access the `out.csv` after run.

```bash
docker run --rm -it -v "$(pwd)":/workspace -w /workspace ubuntu bash -lc "\
export DEBIAN_FRONTEND=noninteractive && \
apt-get update && apt-get install -y unzip python3 && \
unzip -o a3.zip && \
cd a3 && \
chmod +x run.sh && \
./run.sh"
```

### Windows (PowerShell)

```powershell
docker run --rm -it -v "${PWD}:/workspace" -w /workspace ubuntu bash -lc "\
export DEBIAN_FRONTEND=noninteractive && \
apt-get update && apt-get install -y unzip python3 && \
unzip -o a3.zip && \
cd a3 && \
chmod +x run.sh && \
./run.sh"
```

The resulting `out.csv` will be written next to `a3.zip` on the host machine.

## Project Structure

```
a3/
├── team_formation.py      # Main Python script (2000+ lines)
├── run.sh                 # Setup and execution script
├── cse403-preferences.csv # Input data (student preferences)
├── README.md              # This file
├── out.csv                # Generated: team assignments
├── report.txt             # Generated: detailed report
└── team_formation.log     # Generated: processing log
```

## Dependencies

- **Python 3.x** (tested with Python 3.13)
- **pandas** (for CSV processing)

Dependencies are automatically installed by `run.sh`.

## Algorithm Details

### Subteam Validation

A subteam is valid when **all members mutually list each other**. For example, if persons A, B, and C want to form a subteam:
- A must list [B, C]
- B must list [A, C]
- C must list [A, B]

### Team Merging Strategy

1. Size 4 subteams + Size 2/1 → Teams of 6/5
2. Size 3 subteams + Size 3/2 → Teams of 6/5
3. Size 2 subteams + Size 2 + Size 2/1 → Teams of 6/5
4. Individuals grouped if compatible (5-6 together)

### Project Assignment

- Each team assigned to project with **lowest aggregate score**
- Aggregate score = sum of individual rankings
- Lower score = better (closer to everyone's top choice)
- Example: Rankings [1,1,1,1,1] → score 5 (perfect!)

### Data Quality Handling

The system automatically handles:
- **Case sensitivity**: `pfg1995` vs `Pfg1995` → normalized
- **Typos**: Fuzzy matching with 80% similarity threshold
- **Email formats**: `netid@uw.edu` → `netid`
- **Unknown netIDs**: Logged but doesn't break processing
- **Inconsistent formatting**: Multiple member name formats supported

## Troubleshooting

**Issue**: Tests fail
- **Solution**: Check `team_formation.log` for details
- Run with `--verbose` flag for more information

**Issue**: Many students unmatched
- **Solution**: This is expected when students have no overlapping project preferences
- Check `report.txt` for list of unmatched students

**Issue**: Dependencies not installing
- **Solution**: On macOS with externally-managed Python, use:
  ```bash
  pip3 install --break-system-packages pandas
  ```

**Issue**: Permission denied
- **Solution**: Make scripts executable:
  ```bash
  chmod +x run.sh team_formation.py
  ```

## Validation

The system includes built-in validation at multiple levels:
1. **Input validation**: Tests CSV structure and data quality
2. **Runtime assertions**: Verifies constraints during processing
3. **Output validation**: Confirms CSV can be read by pandas

Run validation tests:
```bash
python3 team_formation.py --test cse403-preferences.csv
```

## Performance

- **Processing time**: ~1-2 seconds for 87 students
- **Memory usage**: <50MB
- **Scalability**: Handles hundreds of students efficiently

## License

Created for CSE 490 A2 - Autumn 2025
