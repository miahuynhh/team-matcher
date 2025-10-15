#!/usr/bin/env python3
"""
Team Formation System
Assigns students to teams based on their preferences and constraints.

LOGGING:
  The system uses Python's logging module with multiple levels:
  - INFO: Normal progress messages (default)
  - WARNING: Data quality issues, edge cases, unmatched students
  - ERROR: Constraint violations, critical issues
  - DEBUG: Detailed processing information (use --verbose flag)
  
  Logs are written to:
  - Console: Simple format for readability
  - team_formation.log: Detailed format with timestamps
  
  Usage:
    python3 team_formation.py input.csv output.csv          # Normal logging
    python3 team_formation.py -v input.csv output.csv       # Verbose (DEBUG)
    python3 team_formation.py --test input.csv              # Run tests only
"""

import sys
import os
import argparse
import pandas as pd
import re
import logging
from difflib import SequenceMatcher


def setup_logging(verbose=False, log_file='team_formation.log'):
    """
    Configure logging for the application.
    
    Args:
        verbose (bool): If True, set DEBUG level; otherwise INFO
        log_file (str): Path to log file
    """
    # Determine log level
    log_level = logging.DEBUG if verbose else logging.INFO
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    simple_formatter = logging.Formatter('%(message)s')
    
    # Configure root logger
    logger = logging.getLogger()
    logger.setLevel(log_level)
    
    # Remove existing handlers
    logger.handlers = []
    
    # Console handler (simple format)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(simple_formatter)
    logger.addHandler(console_handler)
    
    # File handler (detailed format)
    file_handler = logging.FileHandler(log_file, mode='w')
    file_handler.setLevel(logging.DEBUG)  # Always log everything to file
    file_handler.setFormatter(detailed_formatter)
    logger.addHandler(file_handler)
    
    logging.info(f"Logging configured: level={logging.getLevelName(log_level)}, file={log_file}")
    logging.debug(f"Verbose logging enabled")


def run_tests(input_filepath):
    """
    Run comprehensive tests on the team formation pipeline.
    
    Args:
        input_filepath: Path to input CSV file
        
    Returns:
        bool: True if all tests pass, False otherwise
    """
    print("=" * 70)
    print("RUNNING TEAM FORMATION PIPELINE TESTS")
    print("=" * 70)
    
    test_passed = 0
    test_failed = 0
    
    try:
        # Test 1: CSV Parsing
        print("\n[Test 1] CSV Parsing...")
        df = pd.read_csv(input_filepath, encoding='utf-8')
        
        # Check expected columns exist
        required_columns = ['Timestamp', 'Email Address', 'Name', 'Your UW NetId']
        for col in required_columns:
            assert col in df.columns, f"Missing required column: {col}"
        
        # Check we have project columns
        project_cols = [col for col in df.columns if '[' in col and ']' in col]
        assert len(project_cols) > 0, "No project columns found"
        
        # Check we have team member columns
        team_cols = [col for col in df.columns if 'Team Member' in col]
        assert len(team_cols) > 0, "No team member columns found"
        
        print(f"  ✓ CSV parsed successfully")
        print(f"  ✓ Found {len(df)} rows")
        print(f"  ✓ Found {len(project_cols)} project columns")
        print(f"  ✓ Found {len(team_cols)} team member columns")
        test_passed += 1
        
    except AssertionError as e:
        print(f"  ✗ FAILED: {e}")
        test_failed += 1
        return False
    except Exception as e:
        print(f"  ✗ FAILED: {e}")
        test_failed += 1
        return False
    
    try:
        # Test 2: Data Extraction
        print("\n[Test 2] Data Extraction...")
        netids = df.iloc[:, 3].tolist()
        initial_count = len(df)
        extracted_count = len(netids)
        
        assert initial_count == extracted_count, f"Data loss: {initial_count} rows -> {extracted_count} netids"
        assert all(netid for netid in netids if not pd.isna(netid)), "Some netIDs are missing"
        
        print(f"  ✓ All {extracted_count} rows processed")
        print(f"  ✓ No data loss detected")
        test_passed += 1
        
    except AssertionError as e:
        print(f"  ✗ FAILED: {e}")
        test_failed += 1
    except Exception as e:
        print(f"  ✗ FAILED: {e}")
        test_failed += 1
    
    try:
        # Test 3: Project Preferences
        print("\n[Test 3] Project Preferences...")
        
        # Extract preferences (simplified version)
        project_columns = []
        project_names = []
        for i in range(4, len(df.columns)):
            col_name = df.columns[i]
            if 'Team Member' in col_name:
                break
            project_name = extract_project_name(col_name)
            if project_name:
                project_columns.append(i)
                project_names.append(project_name)
        
        # Check each person has preferences
        for row_idx in range(len(df)):
            netid = df.iloc[row_idx, 3]
            prefs = []
            for col_idx in project_columns:
                cell_value = df.iloc[row_idx, col_idx]
                ranking = parse_preference_value(cell_value)
                if ranking is not None:
                    prefs.append(ranking)
            
            # Most people should have 5 preferences
            if len(prefs) not in [0, 5]:
                print(f"  ⚠ {netid} has {len(prefs)} preferences (expected 5)")
        
        print(f"  ✓ Project preferences extracted")
        print(f"  ✓ Found {len(project_names)} projects")
        test_passed += 1
        
    except Exception as e:
        print(f"  ✗ FAILED: {e}")
        test_failed += 1
    
    try:
        # Test 4: Subteam Validation
        print("\n[Test 4] Subteam Identification...")
        
        # This is a simplified test - full validation happens in main pipeline
        team_member_cols = []
        for i in range(len(df.columns)):
            if 'Team Member' in df.columns[i]:
                team_member_cols.append(i)
        
        assert len(team_member_cols) > 0, "No team member columns found"
        
        print(f"  ✓ Team member columns identified: {len(team_member_cols)}")
        test_passed += 1
        
    except AssertionError as e:
        print(f"  ✗ FAILED: {e}")
        test_failed += 1
    except Exception as e:
        print(f"  ✗ FAILED: {e}")
        test_failed += 1
    
    try:
        # Test 5: Data Consistency
        print("\n[Test 5] Data Consistency...")
        
        # Check no completely empty rows
        empty_rows = 0
        for i in range(len(df)):
            if df.iloc[i].isna().all():
                empty_rows += 1
        
        assert empty_rows == 0, f"Found {empty_rows} completely empty rows"
        
        # Check netIDs are reasonable (alphanumeric, reasonable length)
        for netid in netids:
            if not pd.isna(netid):
                netid_str = str(netid).strip()
                assert len(netid_str) > 0, "Empty netID found"
                assert len(netid_str) < 50, f"Suspiciously long netID: {netid_str}"
        
        print(f"  ✓ No empty rows")
        print(f"  ✓ All netIDs are reasonable")
        test_passed += 1
        
    except AssertionError as e:
        print(f"  ✗ FAILED: {e}")
        test_failed += 1
    except Exception as e:
        print(f"  ✗ FAILED: {e}")
        test_failed += 1
    
    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    print(f"Passed: {test_passed}")
    print(f"Failed: {test_failed}")
    
    if test_failed == 0:
        print("\n✓ ALL TESTS PASSED")
        print("=" * 70 + "\n")
        return True
    else:
        print(f"\n✗ {test_failed} TEST(S) FAILED")
        print("=" * 70 + "\n")
        return False


class DataQualityTracker:
    """Track data quality issues and warnings throughout processing."""
    
    def __init__(self):
        self.issues = {
            'duplicate_netids': [],
            'invalid_project_counts': [],
            'missing_data': [],
            'unknown_netids_in_subteams': [],
            'fuzzy_matched_netids': [],
            'asymmetric_subteam_prefs': [],
            'no_common_preferences': [],
            'case_normalization': []
        }
    
    def add_issue(self, category, message):
        """Add an issue to track."""
        if category in self.issues:
            self.issues[category].append(message)
    
    def has_issues(self):
        """Check if any issues were found."""
        return any(len(issues) > 0 for issues in self.issues.values())
    
    def print_summary(self):
        """Print a summary of all issues found."""
        logging.info("\n--- Data Quality Issues Summary ---")
        total_issues = sum(len(issues) for issues in self.issues.values())
        
        if total_issues == 0:
            logging.info("✓ No data quality issues found!")
            return
        
        logging.warning(f"Found {total_issues} issue(s):\n")
        
        for category, issues in self.issues.items():
            if issues:
                category_name = category.replace('_', ' ').title()
                logging.warning(f"{category_name}: {len(issues)}")
                for issue in issues[:3]:  # Show first 3
                    logging.warning(f"  - {issue}")
                if len(issues) > 3:
                    logging.warning(f"  ... and {len(issues) - 3} more")
                logging.warning("")


def validate_input_data(df, netids, project_prefs, quality_tracker):
    """
    Validate input data quality and log issues.
    
    Args:
        df: The parsed DataFrame
        netids: List of netIDs
        project_prefs: Dictionary of project preferences
        quality_tracker: DataQualityTracker instance
    """
    print("\n--- Validating Input Data ---")
    
    # Check for duplicate netIDs
    seen_netids = set()
    for netid in netids:
        if netid in seen_netids:
            quality_tracker.add_issue('duplicate_netids', f"Duplicate netID: {netid}")
        seen_netids.add(netid)
    
    if quality_tracker.issues['duplicate_netids']:
        print(f"⚠ Found {len(quality_tracker.issues['duplicate_netids'])} duplicate netID(s)")
    else:
        print(f"✓ No duplicate netIDs")
    
    # Check project preference counts
    invalid_count = 0
    for netid, prefs in project_prefs.items():
        if len(prefs) != 5:
            quality_tracker.add_issue('invalid_project_counts', 
                                     f"{netid}: has {len(prefs)} preferences (expected 5)")
            invalid_count += 1
    
    if invalid_count > 0:
        print(f"⚠ {invalid_count} student(s) don't have exactly 5 project preferences")
    else:
        print(f"✓ All students have exactly 5 project preferences")
    
    # Check for missing required data
    missing_count = 0
    for i, netid in enumerate(netids):
        if pd.isna(netid) or str(netid).strip() == '':
            quality_tracker.add_issue('missing_data', f"Row {i+1}: Missing netID")
            missing_count += 1
    
    if missing_count > 0:
        print(f"⚠ {missing_count} row(s) have missing netIDs")
    else:
        print(f"✓ All rows have netIDs")
    
    print(f"\nValidation complete. Found {sum(len(v) for v in quality_tracker.issues.values())} total issue(s).")


def fuzzy_match_netid(netid, known_netids, threshold=0.8):
    """
    Try to fuzzy match a netID against known netIDs.
    
    Args:
        netid: The netID to match
        known_netids: Set of known valid netIDs
        threshold: Similarity threshold (0-1)
        
    Returns:
        tuple: (matched_netid, similarity_score) or (None, 0) if no match
    """
    netid_lower = str(netid).lower().strip()
    
    best_match = None
    best_score = 0
    
    for known in known_netids:
        known_lower = str(known).lower().strip()
        similarity = SequenceMatcher(None, netid_lower, known_lower).ratio()
        
        if similarity > best_score and similarity >= threshold:
            best_score = similarity
            best_match = known
    
    return (best_match, best_score)


def parse_input_csv(filepath):
    """
    Parse the input CSV file containing student preferences.
    
    Args:
        filepath (str): Path to the CSV file
        
    Returns:
        pd.DataFrame: Parsed DataFrame with student data
        
    Raises:
        FileNotFoundError: If the file doesn't exist
        Exception: If the file can't be read or parsed
    """
    try:
        print(f"\n--- Parsing CSV file ---")
        
        # Try UTF-8 encoding first
        try:
            df = pd.read_csv(filepath, encoding='utf-8')
        except UnicodeDecodeError:
            print("UTF-8 encoding failed, trying latin-1...")
            df = pd.read_csv(filepath, encoding='latin-1')
        
        # Print basic information
        print(f"Successfully loaded CSV file!")
        print(f"Number of rows: {len(df)}")
        print(f"Number of columns: {len(df.columns)}")
        print(f"\nColumn names (first 10):")
        for i, col in enumerate(df.columns[:10]):
            print(f"  Column {i}: {col}")
        if len(df.columns) > 10:
            print(f"  ... and {len(df.columns) - 10} more columns")
        
        return df
        
    except FileNotFoundError:
        raise FileNotFoundError(f"CSV file not found: {filepath}")
    except pd.errors.EmptyDataError:
        raise Exception(f"CSV file is empty: {filepath}")
    except Exception as e:
        raise Exception(f"Error reading CSV file: {e}")


def extract_basic_data(df):
    """
    Extract basic student data from the DataFrame.
    
    Args:
        df (pd.DataFrame): The parsed DataFrame
        
    Returns:
        dict: Dictionary containing extracted data with keys:
            - 'netids': List of student NetIDs
    """
    print(f"\n--- Extracting basic data ---")
    
    # Column D is index 3 (0-indexed): "Your UW NetId"
    netid_column = df.columns[3]
    print(f"NetID column name: '{netid_column}'")
    
    # Extract netIDs from column D
    netids = df.iloc[:, 3].tolist()
    
    print(f"Number of NetIDs extracted: {len(netids)}")
    print(f"\nFirst 5 NetIDs:")
    for i, netid in enumerate(netids[:5]):
        print(f"  {i+1}. {netid}")
    
    # Return extracted data
    return {
        'netids': netids
    }


def parse_preference_value(cell_value):
    """
    Parse a preference cell value and extract the ranking number.
    
    Args:
        cell_value: Cell value from CSV (e.g., "#1 Choice", "#2 Choice", etc.)
        
    Returns:
        int: The ranking number (1-5), or None if blank/invalid
    """
    if pd.isna(cell_value) or cell_value == '':
        return None
    
    # Convert to string and extract number from patterns like "#1 Choice", "#2 Choice", etc.
    value_str = str(cell_value).strip()
    match = re.search(r'#(\d+)\s*Choice', value_str)
    if match:
        return int(match.group(1))
    
    return None


def extract_project_name(column_header):
    """
    Extract the project name from a column header.
    
    Args:
        column_header (str): Column header containing project name in brackets
        
    Returns:
        str: The project name, or None if no project name found
    """
    # Extract text within brackets [ProjectName]
    match = re.search(r'\[([^\]]+)\]', column_header)
    if match:
        return match.group(1).strip()
    return None


def extract_project_preferences(df):
    """
    Extract project preferences from the DataFrame.
    
    Args:
        df (pd.DataFrame): The parsed DataFrame
        
    Returns:
        dict: Dictionary mapping netID -> {project_name: ranking}
              e.g., {'netid1': {'ProjectA': 1, 'ProjectB': 2, ...}, ...}
    """
    print(f"\n--- Extracting project preferences ---")
    
    # Get netIDs from column D (index 3)
    netids = df.iloc[:, 3].tolist()
    
    # Identify project columns (from column E onwards, index 4+)
    # Project columns contain brackets "[ProjectName]"
    # Stop when we reach "Team Member" columns
    project_columns = []
    project_names = []
    
    for i in range(4, len(df.columns)):
        col_name = df.columns[i]
        # Stop if we reach team member columns
        if 'Team Member' in col_name:
            break
        
        # Extract project name from column header
        project_name = extract_project_name(col_name)
        if project_name:
            project_columns.append(i)
            project_names.append(project_name)
    
    print(f"Found {len(project_columns)} project columns")
    print(f"First 5 projects: {project_names[:5]}")
    
    # Build preferences dictionary
    preferences = {}
    
    for row_idx, netid in enumerate(netids):
        student_prefs = {}
        
        for col_idx, project_name in zip(project_columns, project_names):
            cell_value = df.iloc[row_idx, col_idx]
            ranking = parse_preference_value(cell_value)
            
            if ranking is not None:
                student_prefs[project_name] = ranking
        
        preferences[netid] = student_prefs
    
    # Print some statistics
    total_prefs = sum(len(prefs) for prefs in preferences.values())
    avg_prefs = total_prefs / len(preferences) if preferences else 0
    
    print(f"Total preferences collected: {total_prefs}")
    print(f"Average preferences per student: {avg_prefs:.1f}")
    
    return preferences


def parse_member_string(cell_value):
    """
    Parse a team member cell value and extract the netID.
    
    Handles various formats:
    - "Name, netid"
    - "Name netid"
    - "Name (netid)"
    - "netid@uw.edu" or "netid@cs.washington.edu"
    
    Args:
        cell_value: Cell value from CSV
        
    Returns:
        str: The extracted netID, or None if blank/unparseable
    """
    if pd.isna(cell_value) or cell_value == '':
        return None
    
    value_str = str(cell_value).strip()
    if not value_str:
        return None
    
    # Handle email format: netid@uw.edu or netid@cs.washington.edu
    email_match = re.search(r'(\w+)@(?:uw\.edu|cs\.washington\.edu)', value_str)
    if email_match:
        return email_match.group(1)
    
    # Try to find pattern "Name, netid" or "Name netid" or "Name (netid)"
    # Look for a comma followed by a word (netid)
    comma_match = re.search(r',\s*(\w+)\s*$', value_str)
    if comma_match:
        return comma_match.group(1)
    
    # Try parentheses format: "Name (netid)"
    paren_match = re.search(r'\((\w+)\)', value_str)
    if paren_match:
        return paren_match.group(1)
    
    # Try space-separated: "Name netid" (take the last word if it looks like a netid)
    parts = value_str.split()
    if len(parts) >= 2:
        # Assume the last part is the netid if it's lowercase and short
        last_part = parts[-1].strip()
        if last_part.islower() and len(last_part) <= 20:
            return last_part
    
    # If nothing worked, return None and we'll log a warning
    return None


def extract_subteam_data(df, known_netids=None, quality_tracker=None):
    """
    Extract subteam member preferences from the DataFrame with data cleaning.
    
    Args:
        df (pd.DataFrame): The parsed DataFrame
        known_netids (set): Set of valid netIDs from the dataset
        quality_tracker (DataQualityTracker): Tracker for data quality issues
        
    Returns:
        dict: Dictionary mapping netID -> list of netIDs they want to work with
              e.g., {'netid1': ['netid2', 'netid3'], ...}
    """
    print(f"\n--- Extracting subteam data ---")
    
    if known_netids is None:
        known_netids = set(df.iloc[:, 3].tolist())
    if quality_tracker is None:
        quality_tracker = DataQualityTracker()
    
    # Get netIDs from column D (index 3)
    netids = df.iloc[:, 3].tolist()
    
    # Find Team Member columns (they start after the project columns)
    team_member_columns = []
    for i in range(len(df.columns)):
        col_name = df.columns[i]
        if 'Team Member' in col_name:
            team_member_columns.append(i)
    
    print(f"Found {len(team_member_columns)} team member columns")
    
    # Build subteam dictionary with data cleaning
    subteams = {}
    unparseable_entries = []
    
    for row_idx, netid in enumerate(netids):
        team_members = []
        
        for col_idx in team_member_columns:
            cell_value = df.iloc[row_idx, col_idx]
            member_netid = parse_member_string(cell_value)
            
            if member_netid is not None:
                # Normalize to lowercase for consistency
                member_netid_lower = str(member_netid).lower().strip()
                netid_lower = str(netid).lower().strip()
                
                # Check if netID needs case normalization
                if member_netid != member_netid_lower:
                    quality_tracker.add_issue('case_normalization', 
                                             f"{netid}: team member '{member_netid}' normalized to '{member_netid_lower}'")
                    member_netid = member_netid_lower
                
                # Check if netID is in known set
                if member_netid not in known_netids:
                    # Try fuzzy matching
                    matched, score = fuzzy_match_netid(member_netid, known_netids)
                    if matched:
                        quality_tracker.add_issue('fuzzy_matched_netids', 
                                                 f"{netid}: '{member_netid}' fuzzy matched to '{matched}' (score: {score:.2f})")
                        member_netid = matched
                    else:
                        quality_tracker.add_issue('unknown_netids_in_subteams', 
                                                 f"{netid}: team member '{member_netid}' not found in student list")
                        # Still include it - might be a valid netID not in this dataset
                
                # Avoid duplicates and self-references
                if member_netid not in team_members and member_netid != netid_lower:
                    team_members.append(member_netid)
                elif member_netid == netid_lower:
                    # Person listed themselves, just skip
                    pass
            elif not pd.isna(cell_value) and str(cell_value).strip():
                # Log unparseable non-empty entries
                unparseable_entries.append((netid, str(cell_value)))
        
        subteams[netid] = team_members
    
    # Print warnings for unparseable entries
    if unparseable_entries:
        print(f"\nWarning: {len(unparseable_entries)} unparseable team member entries:")
        for netid, value in unparseable_entries[:5]:  # Show first 5
            print(f"  {netid}: '{value}'")
        if len(unparseable_entries) > 5:
            print(f"  ... and {len(unparseable_entries) - 5} more")
    
    # Calculate statistics
    num_with_members = sum(1 for members in subteams.values() if members)
    total_members = sum(len(members) for members in subteams.values())
    avg_members = total_members / len(subteams) if subteams else 0
    
    print(f"\nSubteam statistics:")
    print(f"  Students with subteam preferences: {num_with_members}/{len(subteams)}")
    print(f"  Total subteam member entries: {total_members}")
    print(f"  Average members per student: {avg_members:.1f}")
    
    # Size distribution
    size_distribution = {}
    for members in subteams.values():
        size = len(members)
        size_distribution[size] = size_distribution.get(size, 0) + 1
    
    print(f"\n  Size distribution:")
    for size in sorted(size_distribution.keys()):
        count = size_distribution[size]
        print(f"    {size} members: {count} students")
    
    return subteams


def validate_subteam(members, subteam_prefs):
    """
    Check if a group of netIDs forms a valid subteam.
    
    A valid subteam requires that for each member M in the team:
    - M's preference list contains exactly all other members (not including M themselves)
    
    Args:
        members: Set of netIDs
        subteam_prefs: Dictionary mapping netID -> list of preferred team members
        
    Returns:
        bool: True if this is a valid subteam
    """
    members_set = set(members)
    
    for member in members_set:
        # Get this member's preferences
        member_prefs = set(subteam_prefs.get(member, []))
        
        # Their preferences should be exactly the other members (excluding themselves)
        expected_prefs = members_set - {member}
        
        if member_prefs != expected_prefs:
            return False
    
    return True


def identify_subteams(subteam_prefs):
    """
    Identify valid, complete subteams from preference data.
    
    A subteam is valid when all members mutually list each other.
    
    Args:
        subteam_prefs: Dictionary mapping netID -> list of netIDs they want to work with
        
    Returns:
        dict with keys:
            - 'complete_subteams': List of sets, each set is a valid subteam
            - 'individuals': Set of netIDs not in any complete subteam
    """
    print(f"\n--- Identifying subteams ---")
    
    complete_subteams = []
    assigned = set()  # Track who's been assigned to a subteam
    
    # Sort by size of preference list (larger teams first) to prioritize larger subteams
    sorted_people = sorted(subteam_prefs.items(), key=lambda x: len(x[1]), reverse=True)
    
    for netid, prefs in sorted_people:
        if netid in assigned:
            continue
        
        if not prefs:
            # No preferences, will be an individual
            continue
        
        # Form potential subteam: this person + their preferences
        potential_team = {netid} | set(prefs)
        
        # Check if this is a valid subteam
        if validate_subteam(potential_team, subteam_prefs):
            # Check if any member is already assigned
            if not (potential_team & assigned):
                complete_subteams.append(potential_team)
                assigned.update(potential_team)
                print(f"  Found subteam of size {len(potential_team)}: {sorted(potential_team)}")
    
    # Everyone else is an individual
    all_people = set(subteam_prefs.keys())
    individuals = all_people - assigned
    
    print(f"\nSubteam identification results:")
    print(f"  Complete subteams: {len(complete_subteams)}")
    print(f"  Individuals: {len(individuals)}")
    
    # Size distribution of subteams
    if complete_subteams:
        size_dist = {}
        for team in complete_subteams:
            size = len(team)
            size_dist[size] = size_dist.get(size, 0) + 1
        
        print(f"\n  Subteam size distribution:")
        for size in sorted(size_dist.keys()):
            count = size_dist[size]
            print(f"    Size {size}: {count} subteam(s)")
    
    return {
        'complete_subteams': complete_subteams,
        'individuals': individuals
    }


def calculate_team_project_prefs(team_members, project_prefs):
    """
    Calculate common project preferences for a team.
    
    Finds projects that ALL team members have in their top 5 and calculates
    aggregate preference scores.
    
    Args:
        team_members: Iterable of netIDs (set, list, etc.)
        project_prefs: Dictionary mapping netID -> {project_name: ranking}
        
    Returns:
        dict: Dictionary of common projects with aggregate scores, sorted by score
              {project: {'aggregate_score': score, 'rankings': [r1, r2, ...]}}
              Empty dict if no common preferences
    """
    team_list = list(team_members)
    
    if not team_list:
        return {}
    
    # Find projects that are in ALL members' top 5
    # Start with first member's projects
    common_projects = set(project_prefs.get(team_list[0], {}).keys())
    
    # Intersect with each other member's projects
    for netid in team_list[1:]:
        member_projects = set(project_prefs.get(netid, {}).keys())
        common_projects &= member_projects
    
    # Calculate aggregate scores for common projects
    project_scores = {}
    for project in common_projects:
        rankings = []
        for netid in team_list:
            ranking = project_prefs[netid][project]
            rankings.append(ranking)
        
        aggregate_score = sum(rankings)
        project_scores[project] = {
            'aggregate_score': aggregate_score,
            'rankings': rankings
        }
    
    # Sort by aggregate score (lower is better)
    sorted_projects = dict(sorted(project_scores.items(), key=lambda x: x[1]['aggregate_score']))
    
    return sorted_projects


def calculate_subteam_project_prefs(subteam, project_prefs):
    """
    Calculate common project preferences for a subteam.
    
    This is a wrapper around calculate_team_project_prefs for consistency.
    
    Args:
        subteam: Set of netIDs
        project_prefs: Dictionary mapping netID -> {project_name: ranking}
        
    Returns:
        dict: Dictionary of common projects with aggregate scores
    """
    return calculate_team_project_prefs(subteam, project_prefs)


def classify_subteams(subteams_data):
    """
    Classify subteams based on size for team formation.
    
    Teams of size 5-6 can be directly assigned to projects.
    Teams of size 1-4 need to be merged or supplemented.
    
    Args:
        subteams_data: Dictionary with 'complete_subteams' and 'individuals'
        
    Returns:
        dict with keys:
            - 'complete_teams': List of teams ready for assignment (size 5-6)
            - 'incomplete_subteams': Dict organized by size (1-4)
    """
    print(f"\n--- Classifying Subteams ---")
    
    complete_teams = []
    incomplete_subteams = {1: [], 2: [], 3: [], 4: []}
    
    # Process complete subteams
    for subteam in subteams_data['complete_subteams']:
        size = len(subteam)
        team_obj = {'members': subteam, 'size': size}
        
        if size >= 5 and size <= 6:
            # Can be directly assigned
            complete_teams.append(team_obj)
        elif size >= 1 and size <= 4:
            # Needs merging/supplementing
            incomplete_subteams[size].append(team_obj)
        # Note: size > 6 would be an error, but shouldn't happen with our validation
    
    # Process individuals (treat as subteams of size 1)
    for individual in subteams_data['individuals']:
        team_obj = {'members': {individual}, 'size': 1}
        incomplete_subteams[1].append(team_obj)
    
    # Print classification results
    print(f"Complete teams (size 5-6): {len(complete_teams)}")
    people_in_complete = sum(team['size'] for team in complete_teams)
    print(f"  Total people: {people_in_complete}")
    
    print(f"\nIncomplete subteams (need merging):")
    people_in_incomplete = 0
    for size in sorted(incomplete_subteams.keys()):
        count = len(incomplete_subteams[size])
        if count > 0:
            people_count = count * size
            people_in_incomplete += people_count
            print(f"  Size {size}: {count} subteam(s) ({people_count} people)")
    
    print(f"  Total people in incomplete teams: {people_in_incomplete}")
    
    return {
        'complete_teams': complete_teams,
        'incomplete_subteams': incomplete_subteams
    }


def check_compatibility(subteam1, subteam2, project_prefs):
    """
    Check if two subteams can be merged based on project preferences.
    
    Returns True if the combined group has at least one project that
    ALL members have in their top 5.
    
    Args:
        subteam1: Dict with 'members' (set of netIDs)
        subteam2: Dict with 'members' (set of netIDs)
        project_prefs: Dictionary mapping netID -> {project_name: ranking}
        
    Returns:
        bool: True if compatible (at least one common project)
    """
    combined_members = subteam1['members'] | subteam2['members']
    common_prefs = calculate_team_project_prefs(combined_members, project_prefs)
    return len(common_prefs) > 0


def merge_subteams_into_teams(incomplete_subteams, project_prefs):
    """
    Merge smaller subteams into valid teams of 5-6 people.
    
    Args:
        incomplete_subteams: Dict organized by size {1: [...], 2: [...], ...}
        project_prefs: Dictionary mapping netID -> {project_name: ranking}
        
    Returns:
        dict with keys:
            - 'formed_teams': List of successfully formed teams
            - 'unmatched': List of subteams that couldn't be matched
    """
    print(f"\n--- Merging Subteams into Teams ---")
    
    formed_teams = []
    used = set()  # Track indices of used subteams by (size, index)
    
    # Helper function to check if a subteam is used
    def is_used(size, idx):
        return (size, idx) in used
    
    # Helper function to mark as used
    def mark_used(size, idx):
        used.add((size, idx))
    
    # Strategy 1: Size 4 + Size 2 = 6, or Size 4 + Size 1 = 5
    print("\nMerging size 4 subteams...")
    for i, team4 in enumerate(incomplete_subteams[4]):
        if is_used(4, i):
            continue
        
        # Try to add a size 2 subteam
        found = False
        for j, team2 in enumerate(incomplete_subteams[2]):
            if is_used(2, j):
                continue
            if check_compatibility(team4, team2, project_prefs):
                merged = {
                    'members': team4['members'] | team2['members'],
                    'source_subteams': [team4, team2],
                    'size': 6
                }
                formed_teams.append(merged)
                mark_used(4, i)
                mark_used(2, j)
                print(f"  Merged size 4 + size 2 → team of 6")
                found = True
                break
        
        if found:
            continue
        
        # Try to add a size 1 subteam
        for j, team1 in enumerate(incomplete_subteams[1]):
            if is_used(1, j):
                continue
            if check_compatibility(team4, team1, project_prefs):
                merged = {
                    'members': team4['members'] | team1['members'],
                    'source_subteams': [team4, team1],
                    'size': 5
                }
                formed_teams.append(merged)
                mark_used(4, i)
                mark_used(1, j)
                print(f"  Merged size 4 + size 1 → team of 5")
                break
    
    # Strategy 2: Size 3 + Size 3 = 6, or Size 3 + Size 2 = 5
    print("\nMerging size 3 subteams...")
    for i, team3a in enumerate(incomplete_subteams[3]):
        if is_used(3, i):
            continue
        
        # Try to merge with another size 3
        found = False
        for j, team3b in enumerate(incomplete_subteams[3]):
            if i >= j or is_used(3, j):
                continue
            if check_compatibility(team3a, team3b, project_prefs):
                merged = {
                    'members': team3a['members'] | team3b['members'],
                    'source_subteams': [team3a, team3b],
                    'size': 6
                }
                formed_teams.append(merged)
                mark_used(3, i)
                mark_used(3, j)
                print(f"  Merged size 3 + size 3 → team of 6")
                found = True
                break
        
        if found:
            continue
        
        # Try to merge with size 2
        for j, team2 in enumerate(incomplete_subteams[2]):
            if is_used(2, j):
                continue
            if check_compatibility(team3a, team2, project_prefs):
                merged = {
                    'members': team3a['members'] | team2['members'],
                    'source_subteams': [team3a, team2],
                    'size': 5
                }
                formed_teams.append(merged)
                mark_used(3, i)
                mark_used(2, j)
                print(f"  Merged size 3 + size 2 → team of 5")
                break
    
    # Strategy 3: Size 2 + Size 2 + Size 2 = 6, or Size 2 + Size 2 + Size 1 = 5
    print("\nMerging size 2 subteams...")
    for i, team2a in enumerate(incomplete_subteams[2]):
        if is_used(2, i):
            continue
        
        # Try to merge with two other size 2 teams
        found = False
        for j, team2b in enumerate(incomplete_subteams[2]):
            if i >= j or is_used(2, j):
                continue
            if not check_compatibility(team2a, team2b, project_prefs):
                continue
            
            for k, team2c in enumerate(incomplete_subteams[2]):
                if j >= k or is_used(2, k):
                    continue
                # Check if all three are compatible
                temp_merge = {'members': team2a['members'] | team2b['members']}
                if check_compatibility(temp_merge, team2c, project_prefs):
                    merged = {
                        'members': team2a['members'] | team2b['members'] | team2c['members'],
                        'source_subteams': [team2a, team2b, team2c],
                        'size': 6
                    }
                    formed_teams.append(merged)
                    mark_used(2, i)
                    mark_used(2, j)
                    mark_used(2, k)
                    print(f"  Merged size 2 + size 2 + size 2 → team of 6")
                    found = True
                    break
            if found:
                break
        
        if found:
            continue
        
        # Try size 2 + size 2 + size 1 = 5
        for j, team2b in enumerate(incomplete_subteams[2]):
            if i >= j or is_used(2, j):
                continue
            if not check_compatibility(team2a, team2b, project_prefs):
                continue
            
            for k, team1 in enumerate(incomplete_subteams[1]):
                if is_used(1, k):
                    continue
                temp_merge = {'members': team2a['members'] | team2b['members']}
                if check_compatibility(temp_merge, team1, project_prefs):
                    merged = {
                        'members': team2a['members'] | team2b['members'] | team1['members'],
                        'source_subteams': [team2a, team2b, team1],
                        'size': 5
                    }
                    formed_teams.append(merged)
                    mark_used(2, i)
                    mark_used(2, j)
                    mark_used(1, k)
                    print(f"  Merged size 2 + size 2 + size 1 → team of 5")
                    found = True
                    break
            if found:
                break
    
    # Strategy 4: Group individuals (size 1) into teams of 5-6
    print("\nGrouping individuals...")
    available_individuals = [(i, team) for i, team in enumerate(incomplete_subteams[1]) if not is_used(1, i)]
    
    while len(available_individuals) >= 5:
        # Try to find a compatible group of 5-6 individuals
        for group_size in [6, 5]:
            if len(available_individuals) < group_size:
                continue
            
            # Try combinations (greedy approach - take first compatible group found)
            for i in range(len(available_individuals) - group_size + 1):
                candidate_group = available_individuals[i:i+group_size]
                
                # Check if all are compatible
                combined = {'members': set()}
                for _, team in candidate_group:
                    combined['members'] |= team['members']
                
                common_prefs = calculate_team_project_prefs(combined['members'], project_prefs)
                if common_prefs:
                    # Found a compatible group!
                    merged = {
                        'members': combined['members'],
                        'source_subteams': [team for _, team in candidate_group],
                        'size': group_size
                    }
                    formed_teams.append(merged)
                    
                    # Mark all as used
                    for idx, _ in candidate_group:
                        mark_used(1, idx)
                    
                    print(f"  Grouped {group_size} individuals → team of {group_size}")
                    
                    # Update available individuals
                    available_individuals = [(i, team) for i, team in enumerate(incomplete_subteams[1]) if not is_used(1, i)]
                    break
            else:
                continue
            break
        else:
            # No compatible group found, break out
            break
    
    # Collect unmatched subteams
    unmatched = []
    for size in [4, 3, 2, 1]:
        for i, team in enumerate(incomplete_subteams[size]):
            if not is_used(size, i):
                unmatched.append(team)
    
    print(f"\nMerging results:")
    print(f"  Formed teams: {len(formed_teams)}")
    people_in_formed = sum(team['size'] for team in formed_teams)
    print(f"  People placed: {people_in_formed}")
    print(f"  Unmatched subteams: {len(unmatched)}")
    people_unmatched = sum(team['size'] for team in unmatched)
    print(f"  People unmatched: {people_unmatched}")
    
    return {
        'formed_teams': formed_teams,
        'unmatched': unmatched
    }


def assign_projects_to_complete_subteams(complete_teams, project_prefs):
    """
    Assign projects to 5-6 person complete subteams.
    
    For each team, assigns their most preferred common project
    (the one with the lowest aggregate score).
    
    Args:
        complete_teams: List of complete team dicts with 'members' and 'size'
        project_prefs: Dictionary mapping netID -> {project_name: ranking}
        
    Returns:
        dict with key 'assignments': List of assignment dicts
    """
    print(f"\n--- Assigning Projects to Complete Subteams ---")
    
    assignments = []
    
    for i, team in enumerate(complete_teams):
        # Calculate common project preferences for this team
        common_prefs = calculate_team_project_prefs(team['members'], project_prefs)
        
        if not common_prefs:
            print(f"\n⚠️  ERROR: Team {i+1} has no common project preferences!")
            print(f"   Members: {', '.join(sorted(team['members']))}")
            continue
        
        # Assign the project with the lowest aggregate score (most preferred)
        best_project = list(common_prefs.keys())[0]  # Already sorted by score
        best_score_data = common_prefs[best_project]
        
        assignment = {
            'team_members': sorted(team['members']),
            'project': best_project,
            'aggregate_score': best_score_data['aggregate_score'],
            'individual_rankings': best_score_data['rankings']
        }
        assignments.append(assignment)
        
        # Calculate max individual ranking to flag poor assignments
        max_ranking = max(best_score_data['rankings'])
        warning = ""
        if max_ranking >= 4:
            warning = " ⚠️  (some members got #4 or #5 choice)"
        
        print(f"\nTeam {i+1} → {best_project}")
        print(f"  Members: {', '.join(assignment['team_members'])}")
        print(f"  Aggregate score: {best_score_data['aggregate_score']}")
        print(f"  Individual rankings: {best_score_data['rankings']}{warning}")
    
    # Analyze assignment quality
    print(f"\n--- Assignment Quality Analysis ---")
    print(f"Total assignments: {len(assignments)}")
    
    # Distribution by aggregate score
    score_ranges = {
        'perfect (all #1)': [],
        'excellent (6-10)': [],
        'good (11-15)': [],
        'fair (16-20)': [],
        'poor (21+)': []
    }
    
    teams_with_low_choices = []
    
    for assignment in assignments:
        score = assignment['aggregate_score']
        max_rank = max(assignment['individual_rankings'])
        
        # Track by score range
        if score == len(assignment['team_members']):  # All #1 choices
            score_ranges['perfect (all #1)'].append(assignment)
        elif score <= 10:
            score_ranges['excellent (6-10)'].append(assignment)
        elif score <= 15:
            score_ranges['good (11-15)'].append(assignment)
        elif score <= 20:
            score_ranges['fair (16-20)'].append(assignment)
        else:
            score_ranges['poor (21+)'].append(assignment)
        
        # Flag teams where someone got #4 or #5
        if max_rank >= 4:
            teams_with_low_choices.append((assignment, max_rank))
    
    print(f"\nDistribution by aggregate score:")
    for range_name, teams in score_ranges.items():
        if teams:
            print(f"  {range_name}: {len(teams)} team(s)")
    
    if teams_with_low_choices:
        print(f"\n⚠️  Warning: {len(teams_with_low_choices)} team(s) have members with #4 or #5 choices:")
        for assignment, max_rank in teams_with_low_choices:
            print(f"  - {assignment['project']}: highest rank = #{max_rank}")
    else:
        print(f"\n✓ All teams assigned projects where everyone had it in their top 3!")
    
    return {
        'assignments': assignments
    }


def assign_projects_to_merged_teams(merged_teams, project_prefs):
    """
    Assign projects to teams formed by merging smaller subteams.
    
    For each merged team, assigns their most preferred common project
    (the one with the lowest aggregate score).
    
    Args:
        merged_teams: List of merged team dicts with 'members', 'size', and 'source_subteams'
        project_prefs: Dictionary mapping netID -> {project_name: ranking}
        
    Returns:
        dict with key 'assignments': List of assignment dicts
    """
    print(f"\n--- Assigning Projects to Merged Teams ---")
    
    assignments = []
    
    for i, team in enumerate(merged_teams):
        # Calculate common project preferences for this team
        common_prefs = calculate_team_project_prefs(team['members'], project_prefs)
        
        if not common_prefs:
            print(f"\n⚠️  ERROR: Merged Team {i+1} has no common project preferences!")
            print(f"   Members: {', '.join(sorted(team['members']))}")
            print(f"   This shouldn't happen - team was formed with compatibility check!")
            continue
        
        # Assign the project with the lowest aggregate score (most preferred)
        best_project = list(common_prefs.keys())[0]  # Already sorted by score
        best_score_data = common_prefs[best_project]
        
        assignment = {
            'team_members': sorted(team['members']),
            'project': best_project,
            'aggregate_score': best_score_data['aggregate_score'],
            'individual_rankings': best_score_data['rankings'],
            'source_subteams_count': len(team['source_subteams'])
        }
        assignments.append(assignment)
        
        # Calculate max individual ranking to flag poor assignments
        max_ranking = max(best_score_data['rankings'])
        warning = ""
        if max_ranking >= 4:
            warning = " ⚠️  (some members got #4 or #5 choice)"
        
        print(f"\nMerged Team {i+1} → {best_project}")
        print(f"  Members: {', '.join(assignment['team_members'])}")
        print(f"  Formed from {assignment['source_subteams_count']} subteam(s)")
        print(f"  Aggregate score: {best_score_data['aggregate_score']}")
        print(f"  Individual rankings: {best_score_data['rankings']}{warning}")
    
    # Analyze assignment quality
    print(f"\n--- Merged Teams Assignment Quality ---")
    print(f"Total assignments: {len(assignments)}")
    
    # Distribution by aggregate score
    score_ranges = {
        'perfect (all #1)': [],
        'excellent (6-10)': [],
        'good (11-15)': [],
        'fair (16-20)': [],
        'poor (21+)': []
    }
    
    teams_with_low_choices = []
    
    for assignment in assignments:
        score = assignment['aggregate_score']
        max_rank = max(assignment['individual_rankings'])
        
        # Track by score range
        if score == len(assignment['team_members']):  # All #1 choices
            score_ranges['perfect (all #1)'].append(assignment)
        elif score <= 10:
            score_ranges['excellent (6-10)'].append(assignment)
        elif score <= 15:
            score_ranges['good (11-15)'].append(assignment)
        elif score <= 20:
            score_ranges['fair (16-20)'].append(assignment)
        else:
            score_ranges['poor (21+)'].append(assignment)
        
        # Flag teams where someone got #4 or #5
        if max_rank >= 4:
            teams_with_low_choices.append((assignment, max_rank))
    
    print(f"\nDistribution by aggregate score:")
    for range_name, teams in score_ranges.items():
        if teams:
            print(f"  {range_name}: {len(teams)} team(s)")
    
    if teams_with_low_choices:
        print(f"\n⚠️  Warning: {len(teams_with_low_choices)} team(s) have members with #4 or #5 choices:")
        for assignment, max_rank in teams_with_low_choices:
            print(f"  - {assignment['project']}: highest rank = #{max_rank}")
    else:
        print(f"\n✓ All merged teams assigned projects where everyone had it in their top 3!")
    
    return {
        'assignments': assignments
    }


def write_output_csv(assignments, output_filepath):
    """
    Write team assignments to CSV file.
    
    Format: project_name, '[member1, member2, member3, ...]'
    
    Args:
        assignments: List of assignment dicts with 'project' and 'team_members'
        output_filepath: Path to output CSV file
    """
    print(f"\n--- Writing Output CSV ---")
    
    # Sort assignments by project name for consistent output
    sorted_assignments = sorted(assignments, key=lambda x: x['project'])
    
    # Format for CSV output
    output_data = []
    for assignment in sorted_assignments:
        project_name = assignment['project']
        # Format members as string representation of list
        members_str = '[' + ', '.join(assignment['team_members']) + ']'
        output_data.append({
            'Project': project_name,
            'Team Members': members_str
        })
    
    # Write CSV with proper escaping using pandas
    output_records = []
    for assignment in sorted_assignments:
        project_name = assignment['project']
        members_str = '[' + ', '.join(assignment['team_members']) + ']'
        output_records.append([project_name, members_str])
    
    df_output = pd.DataFrame(output_records)
    df_output.to_csv(output_filepath, index=False, header=False)
    
    print(f"Output written to: {output_filepath}")
    print(f"  Teams: {len(output_data)}")
    print(f"  Total people assigned: {sum(len(a['team_members']) for a in assignments)}")


def analyze_assignments(assignments, project_prefs):
    """
    Analyze assignment quality and preference satisfaction.
    
    Args:
        assignments: List of assignment dicts
        project_prefs: Dictionary mapping netID -> {project_name: ranking}
        
    Returns:
        dict: Analysis results including satisfaction breakdown
    """
    print(f"\n--- Analyzing Assignment Optimization ---")
    
    # Track individual preference satisfaction
    preference_counts = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
    all_individual_rankings = []
    
    for assignment in assignments:
        for ranking in assignment['individual_rankings']:
            preference_counts[ranking] = preference_counts.get(ranking, 0) + 1
            all_individual_rankings.append(ranking)
    
    total_people = len(all_individual_rankings)
    
    print(f"\nIndividual Preference Satisfaction:")
    print(f"  Total people assigned: {total_people}")
    for rank in sorted(preference_counts.keys()):
        count = preference_counts[rank]
        percentage = (count / total_people * 100) if total_people > 0 else 0
        print(f"  #{rank} choice: {count} people ({percentage:.1f}%)")
    
    # Calculate average individual ranking
    avg_rank = sum(all_individual_rankings) / len(all_individual_rankings) if all_individual_rankings else 0
    print(f"\n  Average ranking per person: {avg_rank:.2f}")
    
    # Identify worst assignments
    worst_assignments = []
    for assignment in assignments:
        max_rank = max(assignment['individual_rankings'])
        avg_rank_team = assignment['aggregate_score'] / len(assignment['team_members'])
        
        if max_rank >= 4 or avg_rank_team >= 3.5:
            worst_assignments.append({
                'project': assignment['project'],
                'max_rank': max_rank,
                'avg_rank': avg_rank_team,
                'aggregate_score': assignment['aggregate_score'],
                'team_size': len(assignment['team_members']),
                'rankings': assignment['individual_rankings']
            })
    
    worst_assignments.sort(key=lambda x: (x['max_rank'], x['avg_rank']), reverse=True)
    
    if worst_assignments:
        print(f"\nWorst Assignments (needs attention):")
        for i, wa in enumerate(worst_assignments[:5]):
            print(f"  {i+1}. {wa['project']}")
            print(f"     Max ranking: #{wa['max_rank']}, Avg: {wa['avg_rank']:.2f}")
            print(f"     Individual rankings: {wa['rankings']}")
    
    # Verify optimality
    print(f"\n--- Verifying Assignment Optimality ---")
    
    # Calculate total aggregate score
    total_aggregate = sum(a['aggregate_score'] for a in assignments)
    print(f"Total aggregate score across all teams: {total_aggregate}")
    print(f"Average aggregate score per team: {total_aggregate / len(assignments):.1f}")
    
    # Since multiple teams can share projects, greedy is optimal
    print(f"\n✓ Assignments are optimal!")
    print(f"  Reason: Multiple teams can work on the same project,")
    print(f"  so each team getting their best option minimizes total score.")
    
    # Check if any improvements possible
    improvements_possible = []
    for assignment in assignments:
        # Check if there were other options for this team
        team_members = assignment['team_members']
        common_prefs = calculate_team_project_prefs(team_members, project_prefs)
        
        if len(common_prefs) > 1:
            best_project = list(common_prefs.keys())[0]
            if assignment['project'] != best_project:
                improvements_possible.append({
                    'current': assignment['project'],
                    'better': best_project,
                    'current_score': assignment['aggregate_score'],
                    'better_score': common_prefs[best_project]['aggregate_score']
                })
    
    if improvements_possible:
        print(f"\n⚠ {len(improvements_possible)} assignment(s) could be improved:")
        for imp in improvements_possible[:3]:
            print(f"  {imp['current']} (score {imp['current_score']}) → {imp['better']} (score {imp['better_score']})")
    else:
        print(f"\n✓ All teams assigned to their best possible project!")
    
    return {
        'preference_counts': preference_counts,
        'total_people': total_people,
        'average_rank': avg_rank,
        'worst_assignments': worst_assignments,
        'total_aggregate': total_aggregate,
        'improvements_possible': improvements_possible
    }


def validate_output(output_filepath):
    """
    Validate the output CSV file by reading it with pandas.
    
    Ensures the file can be properly parsed and has the correct format.
    
    Args:
        output_filepath: Path to the output CSV file
        
    Returns:
        bool: True if validation passes, False otherwise
    """
    print(f"\n--- Validating Output CSV ---")
    
    try:
        # Read the CSV with pandas
        df = pd.read_csv(output_filepath, header=None, names=['Project', 'Team_Members'])
        
        print(f"✓ CSV successfully read by pandas")
        print(f"  Rows: {len(df)}")
        print(f"  Columns: {len(df.columns)}")
        
        # Check that we have exactly 2 columns
        if len(df.columns) != 2:
            print(f"✗ ERROR: Expected 2 columns, found {len(df.columns)}")
            return False
        
        print(f"✓ Correct number of columns (2)")
        
        # Validate each row
        validation_errors = []
        
        for idx in range(len(df)):
            row = df.iloc[idx]
            row_num = idx + 1
            project = row['Project']
            members = row['Team_Members']
            
            # Check project name is not empty
            if pd.isna(project) or str(project).strip() == '':
                validation_errors.append(f"Row {row_num}: Project name is empty")
                continue
            
            # Check members list format
            members_str = str(members)
            if not members_str.startswith('[') or not members_str.endswith(']'):
                validation_errors.append(f"Row {row_num} ({project}): Members list doesn't start with '[' and end with ']'")
                continue
            
            # Try to parse the member list
            try:
                # Extract members from the string representation
                members_content = members_str[1:-1]  # Remove brackets
                if members_content.strip():  # Not empty
                    member_list = [m.strip() for m in members_content.split(',')]
                    
                    # Check team size (should be 5 or 6)
                    if len(member_list) < 5 or len(member_list) > 6:
                        validation_errors.append(f"Row {row_num} ({project}): Team has {len(member_list)} members (expected 5-6)")
                    
                    # Check no empty members
                    if any(not m for m in member_list):
                        validation_errors.append(f"Row {row_num} ({project}): Contains empty member names")
                else:
                    validation_errors.append(f"Row {row_num} ({project}): Empty member list")
            except Exception as e:
                validation_errors.append(f"Row {row_num} ({project}): Error parsing members - {e}")
        
        if validation_errors:
            print(f"✗ Validation errors found:")
            for error in validation_errors[:10]:  # Show first 10 errors
                print(f"  - {error}")
            if len(validation_errors) > 10:
                print(f"  ... and {len(validation_errors) - 10} more errors")
            return False
        
        print(f"✓ All rows properly formatted")
        print(f"✓ All teams have 5-6 members")
        print(f"\n✓ Validation PASSED - Output CSV is valid!")
        
        # Show a sample row
        if len(df) > 0:
            print(f"\nSample row:")
            sample = df.iloc[0]
            print(f"  Project: {sample['Project']}")
            print(f"  Members: {sample['Team_Members']}")
        
        return True
        
    except FileNotFoundError:
        print(f"✗ ERROR: Output file not found: {output_filepath}")
        return False
    except pd.errors.ParserError as e:
        print(f"✗ ERROR: Failed to parse CSV file: {e}")
        return False
    except Exception as e:
        print(f"✗ ERROR: Validation failed: {e}")
        return False


def generate_report(assignments, unmatched, quality_tracker=None, analysis_results=None, report_filepath='report.txt'):
    """
    Generate a summary report of the team formation results.
    
    Args:
        assignments: List of all assignment dicts
        unmatched: List of unmatched subteam dicts
        report_filepath: Path to output report file
    """
    print(f"\n--- Generating Report ---")
    
    with open(report_filepath, 'w') as f:
        f.write("=" * 70 + "\n")
        f.write("TEAM FORMATION SUMMARY REPORT\n")
        f.write("=" * 70 + "\n\n")
        
        # Overall statistics
        f.write("OVERALL STATISTICS\n")
        f.write("-" * 70 + "\n")
        total_teams = len(assignments)
        total_placed = sum(len(a['team_members']) for a in assignments)
        unmatched_count = sum(len(team['members']) for team in unmatched)
        total_students = total_placed + unmatched_count
        
        f.write(f"Total students: {total_students}\n")
        f.write(f"Students successfully placed: {total_placed} ({total_placed/total_students*100:.1f}%)\n")
        f.write(f"Students unmatched: {unmatched_count} ({unmatched_count/total_students*100:.1f}%)\n")
        f.write(f"Total teams formed: {total_teams}\n\n")
        
        # Preference satisfaction distribution
        f.write("PREFERENCE SATISFACTION DISTRIBUTION\n")
        f.write("-" * 70 + "\n")
        
        score_ranges = {
            'Perfect (all #1)': 0,
            'Excellent (avg 1.0-2.0 per person)': 0,
            'Good (avg 2.0-3.0 per person)': 0,
            'Fair (avg 3.0-4.0 per person)': 0,
            'Poor (avg 4.0+ per person)': 0
        }
        
        teams_with_low_choices = []
        
        for assignment in assignments:
            score = assignment['aggregate_score']
            team_size = len(assignment['team_members'])
            avg_per_person = score / team_size
            max_rank = max(assignment['individual_rankings'])
            
            if score == team_size:  # All #1
                score_ranges['Perfect (all #1)'] += 1
            elif avg_per_person <= 2.0:
                score_ranges['Excellent (avg 1.0-2.0 per person)'] += 1
            elif avg_per_person <= 3.0:
                score_ranges['Good (avg 2.0-3.0 per person)'] += 1
            elif avg_per_person <= 4.0:
                score_ranges['Fair (avg 3.0-4.0 per person)'] += 1
            else:
                score_ranges['Poor (avg 4.0+ per person)'] += 1
            
            if max_rank >= 4:
                teams_with_low_choices.append((assignment['project'], max_rank))
        
        for range_name, count in score_ranges.items():
            if count > 0:
                f.write(f"  {range_name}: {count} team(s)\n")
        
        if teams_with_low_choices:
            f.write(f"\nTeams with members who got #4 or #5 choices: {len(teams_with_low_choices)}\n")
            for project, max_rank in teams_with_low_choices:
                f.write(f"  - {project}: highest rank = #{max_rank}\n")
        
        f.write("\n")
        
        # Assignment analysis (if provided)
        if analysis_results:
            f.write("ASSIGNMENT OPTIMIZATION ANALYSIS\n")
            f.write("-" * 70 + "\n")
            
            # Individual preference satisfaction
            f.write("Individual Preference Satisfaction:\n")
            total = analysis_results['total_people']
            for rank in sorted(analysis_results['preference_counts'].keys()):
                count = analysis_results['preference_counts'][rank]
                percentage = (count / total * 100) if total > 0 else 0
                f.write(f"  #{rank} choice: {count} people ({percentage:.1f}%)\n")
            
            f.write(f"\nAverage ranking per person: {analysis_results['average_rank']:.2f}\n")
            f.write(f"Total aggregate score: {analysis_results['total_aggregate']}\n")
            
            # Worst assignments
            if analysis_results['worst_assignments']:
                f.write(f"\nAssignments Needing Attention ({len(analysis_results['worst_assignments'])} team(s)):\n")
                for wa in analysis_results['worst_assignments'][:5]:
                    f.write(f"  - {wa['project']}: ")
                    f.write(f"max rank #{wa['max_rank']}, avg {wa['avg_rank']:.2f}, ")
                    f.write(f"rankings {wa['rankings']}\n")
            
            # Optimality verification
            f.write(f"\nOptimality Status:\n")
            if analysis_results['improvements_possible']:
                f.write(f"  ⚠ {len(analysis_results['improvements_possible'])} potential improvement(s) found\n")
                for imp in analysis_results['improvements_possible'][:3]:
                    f.write(f"    - {imp['current']} → {imp['better']} ")
                    f.write(f"(score {imp['current_score']} → {imp['better_score']})\n")
            else:
                f.write(f"  ✓ All teams assigned to their best possible project\n")
            
            f.write("\n")
        
        # Data quality issues (if tracker provided)
        if quality_tracker and quality_tracker.has_issues():
            f.write("DATA QUALITY ISSUES\n")
            f.write("-" * 70 + "\n")
            
            total_issues = sum(len(issues) for issues in quality_tracker.issues.values())
            f.write(f"Total issues found: {total_issues}\n\n")
            
            for category, issues in quality_tracker.issues.items():
                if issues:
                    category_name = category.replace('_', ' ').title()
                    f.write(f"{category_name}: {len(issues)} issue(s)\n")
                    for issue in issues[:5]:  # Show first 5
                        f.write(f"  - {issue}\n")
                    if len(issues) > 5:
                        f.write(f"  ... and {len(issues) - 5} more\n")
                    f.write("\n")
            
            f.write("Note: These issues were handled automatically where possible.\n")
            f.write("Unknown netIDs may indicate students not in the dataset.\n\n")
        
        # Team assignments
        f.write("TEAM ASSIGNMENTS\n")
        f.write("-" * 70 + "\n")
        
        # Sort by project name
        sorted_assignments = sorted(assignments, key=lambda x: x['project'])
        
        for i, assignment in enumerate(sorted_assignments, 1):
            f.write(f"\nTeam {i}: {assignment['project']}\n")
            f.write(f"  Members ({len(assignment['team_members'])}): {', '.join(assignment['team_members'])}\n")
            f.write(f"  Aggregate score: {assignment['aggregate_score']}\n")
            f.write(f"  Individual rankings: {assignment['individual_rankings']}\n")
            
            # Calculate average
            avg = assignment['aggregate_score'] / len(assignment['team_members'])
            f.write(f"  Average per person: {avg:.2f}\n")
        
        # Unmatched people
        if unmatched:
            f.write("\n" + "=" * 70 + "\n")
            f.write("UNMATCHED STUDENTS\n")
            f.write("=" * 70 + "\n")
            f.write(f"Total unmatched: {unmatched_count} student(s)\n\n")
            
            # Extract all unmatched netids
            unmatched_people = []
            for team in unmatched:
                unmatched_people.extend(sorted(team['members']))
            unmatched_people.sort()
            
            f.write("List of unmatched students:\n")
            for i, netid in enumerate(unmatched_people, 1):
                f.write(f"  {i}. {netid}\n")
            
            f.write("\nNote: These students could not be placed in teams of 5-6 with\n")
            f.write("compatible project preferences (projects in everyone's top 5).\n")
        
        f.write("\n" + "=" * 70 + "\n")
        f.write("END OF REPORT\n")
        f.write("=" * 70 + "\n")
    
    print(f"Report written to: {report_filepath}")
    print(f"  Total teams: {total_teams}")
    print(f"  People placed: {total_placed}/{total_students}")


def main(input_file, output_file):
    """
    Main function for team formation.
    
    Args:
        input_file (str): Path to the input CSV file with student preferences
        output_file (str): Path to write the output CSV file with team assignments
    """
    try:
        # Initialize data quality tracker
        quality_tracker = DataQualityTracker()
        
        # Check if input file exists
        if not os.path.exists(input_file):
            raise FileNotFoundError(f"Input file not found: {input_file}")
        
        logging.info(f"Reading preferences from: {input_file}")
        
        # Parse the CSV file and load student preferences
        df = parse_input_csv(input_file)
        
        # Extract basic data (netIDs for now)
        basic_data = extract_basic_data(df)
        
        # Extract project preferences
        project_prefs = extract_project_preferences(df)
        
        # Validate input data
        validate_input_data(df, basic_data['netids'], project_prefs, quality_tracker)
        
        # Extract subteam data with cleaning
        known_netids = set(basic_data['netids'])
        subteam_data = extract_subteam_data(df, known_netids, quality_tracker)
        
        # Identify valid, complete subteams
        subteam_results = identify_subteams(subteam_data)
        
        # Calculate common project preferences for each subteam
        print(f"\n--- Analyzing Subteam Project Preferences ---")
        subteam_project_analysis = []
        subteams_with_no_common = []
        
        for i, subteam in enumerate(subteam_results['complete_subteams']):
            common_prefs = calculate_subteam_project_prefs(subteam, project_prefs)
            subteam_project_analysis.append({
                'subteam': subteam,
                'common_prefs': common_prefs
            })
            
            if not common_prefs:
                subteams_with_no_common.append((i+1, sorted(subteam)))
                logging.error(f"\n⚠️  ERROR: Subteam {i+1} has NO common project preferences!")
                logging.error(f"   Members: {', '.join(sorted(subteam))}")
                quality_tracker.add_issue('no_common_preferences', 
                                         f"Subteam {i+1}: {', '.join(sorted(subteam))}")
            else:
                print(f"\nSubteam {i+1} ({len(subteam)} members) - Top 3 common projects:")
                for j, (project, data) in enumerate(list(common_prefs.items())[:3]):
                    print(f"  {j+1}. {project}")
                    print(f"     Aggregate score: {data['aggregate_score']}")
                    print(f"     Individual rankings: {data['rankings']}")
                if len(common_prefs) > 3:
                    print(f"  ... and {len(common_prefs) - 3} more common project(s)")
        
        # Summary of subteam analysis
        if subteams_with_no_common:
            print(f"\n⚠️  WARNING: {len(subteams_with_no_common)} subteam(s) have NO common preferences!")
            print(f"   This violates the constraint that projects must be in everyone's top 5.")
        else:
            print(f"\n✓ All {len(subteam_results['complete_subteams'])} subteams have at least one common project preference")
        
        # Classify subteams for team formation
        classified_teams = classify_subteams(subteam_results)
        
        # Assertion: Verify all complete teams are size 5-6
        for team in classified_teams['complete_teams']:
            assert len(team['members']) in [5, 6], f"Invalid complete team size: {len(team['members'])}"
        
        # Merge incomplete subteams into valid teams
        merged_results = merge_subteams_into_teams(classified_teams['incomplete_subteams'], project_prefs)
        
        # Assertion: Verify all merged teams are size 5-6
        for team in merged_results['formed_teams']:
            assert len(team['members']) in [5, 6], f"Invalid merged team size: {len(team['members'])}"
        
        # Assign projects to complete subteams
        complete_assignments = assign_projects_to_complete_subteams(classified_teams['complete_teams'], project_prefs)
        
        # Assertion: Verify all assignments have valid projects
        for assignment in complete_assignments['assignments']:
            assert 'project' in assignment, "Assignment missing project"
            assert 'team_members' in assignment, "Assignment missing team members"
            assert len(assignment['team_members']) in [5, 6], f"Invalid team size in assignment: {len(assignment['team_members'])}"
            
            # Verify project is in everyone's top 5
            for member in assignment['team_members']:
                member_prefs = project_prefs.get(member, {})
                assert assignment['project'] in member_prefs, \
                    f"Project {assignment['project']} not in {member}'s preferences"
        
        # Assign projects to merged teams
        merged_assignments = assign_projects_to_merged_teams(merged_results['formed_teams'], project_prefs)
        
        # Assertion: Verify merged assignments
        for assignment in merged_assignments['assignments']:
            assert len(assignment['team_members']) in [5, 6], f"Invalid merged team size: {len(assignment['team_members'])}"
            for member in assignment['team_members']:
                member_prefs = project_prefs.get(member, {})
                assert assignment['project'] in member_prefs, \
                    f"Project {assignment['project']} not in {member}'s preferences (merged team)"
        
        # Compare complete vs merged team satisfaction
        print(f"\n--- Satisfaction Comparison: Complete vs Merged Teams ---")
        
        if complete_assignments['assignments']:
            complete_scores = [a['aggregate_score'] for a in complete_assignments['assignments']]
            avg_complete = sum(complete_scores) / len(complete_scores)
            complete_avg_per_person = avg_complete / len(complete_assignments['assignments'][0]['team_members']) if complete_assignments['assignments'] else 0
            print(f"\nComplete Subteams:")
            print(f"  Teams: {len(complete_assignments['assignments'])}")
            print(f"  Average aggregate score: {avg_complete:.1f}")
            print(f"  Average score per person: {complete_avg_per_person:.2f}")
            
            complete_perfect = sum(1 for a in complete_assignments['assignments'] if a['aggregate_score'] == len(a['team_members']))
            print(f"  Perfect assignments (all #1): {complete_perfect}/{len(complete_assignments['assignments'])}")
        
        if merged_assignments['assignments']:
            merged_scores = [a['aggregate_score'] for a in merged_assignments['assignments']]
            avg_merged = sum(merged_scores) / len(merged_scores)
            avg_team_size = sum(len(a['team_members']) for a in merged_assignments['assignments']) / len(merged_assignments['assignments'])
            merged_avg_per_person = avg_merged / avg_team_size
            print(f"\nMerged Teams:")
            print(f"  Teams: {len(merged_assignments['assignments'])}")
            print(f"  Average aggregate score: {avg_merged:.1f}")
            print(f"  Average score per person: {merged_avg_per_person:.2f}")
            
            merged_perfect = sum(1 for a in merged_assignments['assignments'] if a['aggregate_score'] == len(a['team_members']))
            print(f"  Perfect assignments (all #1): {merged_perfect}/{len(merged_assignments['assignments'])}")
        
        # Overall comparison
        if complete_assignments['assignments'] and merged_assignments['assignments']:
            print(f"\nComparison:")
            if complete_avg_per_person < merged_avg_per_person:
                print(f"  Complete subteams have better satisfaction (lower score per person)")
            elif complete_avg_per_person > merged_avg_per_person:
                print(f"  Merged teams have better satisfaction (lower score per person)")
            else:
                print(f"  Both have equal satisfaction")
        
        # Print examples of merged teams
        print(f"\n--- Merged Teams Examples ---")
        if merged_results['formed_teams']:
            print(f"\nShowing first 3 merged teams:")
            for i, team in enumerate(merged_results['formed_teams'][:3]):
                members_list = sorted(team['members'])
                print(f"\nMerged Team {i+1} (size {team['size']}):")
                print(f"  Members: {', '.join(members_list)}")
                print(f"  Source subteams: {len(team['source_subteams'])} subteam(s) merged")
                
                # Show common projects for this merged team
                common_prefs = calculate_team_project_prefs(team['members'], project_prefs)
                if common_prefs:
                    top_projects = list(common_prefs.items())[:3]
                    print(f"  Common projects:")
                    for project, data in top_projects:
                        print(f"    - {project} (score: {data['aggregate_score']})")
                else:
                    print(f"  ⚠️  WARNING: No common projects!")
            
            if len(merged_results['formed_teams']) > 3:
                print(f"\n... and {len(merged_results['formed_teams']) - 3} more merged teams")
        
        # Show unmatched people if any
        if merged_results['unmatched']:
            logging.warning(f"\n⚠️  Unmatched Subteams/Individuals:")
            logging.warning(f"  Total unmatched: {len(merged_results['unmatched'])}")
            unmatched_people = []
            for team in merged_results['unmatched']:
                unmatched_people.extend(sorted(team['members']))
            logging.warning(f"  Unmatched people ({len(unmatched_people)}): {', '.join(unmatched_people[:10])}")
            if len(unmatched_people) > 10:
                logging.warning(f"    ... and {len(unmatched_people) - 10} more")
            
            # Log detailed list at DEBUG level
            logging.debug(f"  Complete list of unmatched: {', '.join(sorted(unmatched_people))}")
        
        # Print examples of extracted preferences
        print(f"\n--- Sample Project Preferences ---")
        sample_netids = list(project_prefs.keys())[:3]
        for netid in sample_netids:
            prefs = project_prefs[netid]
            print(f"\n{netid}:")
            if prefs:
                # Sort by ranking to show in order
                sorted_prefs = sorted(prefs.items(), key=lambda x: x[1])
                for project, rank in sorted_prefs:
                    print(f"  #{rank} - {project}")
            else:
                print(f"  No preferences")
        
        # Print examples of complete subteams
        print(f"\n--- Complete Subteams (Mutual Matches) ---")
        if subteam_results['complete_subteams']:
            # Show first 3 complete subteams as examples
            for i, team in enumerate(subteam_results['complete_subteams'][:3]):
                sorted_team = sorted(team)
                print(f"\nSubteam {i+1} (size {len(team)}):")
                for member in sorted_team:
                    print(f"  - {member}")
            
            if len(subteam_results['complete_subteams']) > 3:
                print(f"\n... and {len(subteam_results['complete_subteams']) - 3} more complete subteam(s)")
        else:
            print("No complete subteams found")
        
        # Print examples of individuals
        if subteam_results['individuals']:
            print(f"\n--- Individuals (No Complete Subteam Match) ---")
            individuals_list = sorted(list(subteam_results['individuals']))
            print(f"First 10 individuals: {', '.join(individuals_list[:10])}")
            if len(individuals_list) > 10:
                print(f"... and {len(individuals_list) - 10} more")
        
        # Print summary of parsed data
        print(f"\n--- Summary ---")
        print(f"Total students: {len(basic_data['netids'])}")
        print(f"Students with preferences: {sum(1 for p in project_prefs.values() if p)}")
        print(f"Students with subteam preferences: {sum(1 for s in subteam_data.values() if s)}")
        print(f"Complete subteams identified: {len(subteam_results['complete_subteams'])}")
        print(f"Individuals (no complete subteam): {len(subteam_results['individuals'])}")
        print(f"\nTeam Formation Results:")
        all_formed_teams = classified_teams['complete_teams'] + merged_results['formed_teams']
        print(f"  Total formed teams: {len(all_formed_teams)}")
        total_placed = sum(team['size'] for team in all_formed_teams)
        print(f"    People successfully placed: {total_placed}")
        print(f"    - Complete subteams (no merge needed): {len(classified_teams['complete_teams'])} teams")
        print(f"    - Merged teams: {len(merged_results['formed_teams'])} teams")
        
        print(f"\n  Project Assignments:")
        print(f"    Complete subteams with projects: {len(complete_assignments['assignments'])}")
        print(f"    Merged teams with projects: {len(merged_assignments['assignments'])}")
        total_assigned = len(complete_assignments['assignments']) + len(merged_assignments['assignments'])
        people_assigned = sum(len(a['team_members']) for a in complete_assignments['assignments']) + sum(len(a['team_members']) for a in merged_assignments['assignments'])
        print(f"    Total teams with project assignments: {total_assigned}")
        print(f"    Total people with project assignments: {people_assigned}")
        
        if merged_results['unmatched']:
            unmatched_count = len(merged_results['unmatched'])
            unmatched_people_count = sum(team['size'] for team in merged_results['unmatched'])
            print(f"\n  Unmatched: {unmatched_count} subteams ({unmatched_people_count} people)")
        else:
            print(f"\n  Unmatched: 0 (all students placed!)")
        print(f"\nNetIDs successfully extracted from column D")
        print(f"Project preferences successfully extracted")
        print(f"Subteam data successfully extracted")
        print(f"Subteam validation completed")
        print(f"Team classification completed")
        print(f"Team merging completed")
        print(f"Project assignment completed for all formed teams")
        
        # Combine all assignments for output
        all_assignments = complete_assignments['assignments'] + merged_assignments['assignments']
        
        # Analyze assignments for optimization and satisfaction
        analysis_results = analyze_assignments(all_assignments, project_prefs)
        
        # Write output CSV
        write_output_csv(all_assignments, output_file)
        
        # Validate output CSV
        validation_passed = validate_output(output_file)
        
        # Generate report with quality tracker data and analysis
        generate_report(all_assignments, merged_results['unmatched'], quality_tracker, analysis_results)
        
        # Print data quality summary
        quality_tracker.print_summary()
        
        # Final success message
        logging.info(f"\n{'='*70}")
        if validation_passed:
            logging.info(f"TEAM FORMATION COMPLETED SUCCESSFULLY")
        else:
            logging.warning(f"TEAM FORMATION COMPLETED WITH VALIDATION WARNINGS")
        logging.info(f"{'='*70}")
        logging.info(f"\nSummary:")
        logging.info(f"  ✓ Output CSV: {output_file}")
        if validation_passed:
            logging.info(f"  ✓ CSV validation: PASSED")
        else:
            logging.warning(f"  ⚠ CSV validation: FAILED (check messages above)")
        logging.info(f"  ✓ Report: report.txt")
        logging.info(f"  ✓ Log file: team_formation.log")
        logging.info(f"  ✓ Teams formed: {len(all_assignments)}")
        logging.info(f"  ✓ Students placed: {sum(len(a['team_members']) for a in all_assignments)}/{len(basic_data['netids'])}")
        
        if merged_results['unmatched']:
            unmatched_count = sum(len(team['members']) for team in merged_results['unmatched'])
            logging.warning(f"  ⚠ Students unmatched: {unmatched_count}")
            logging.warning(f"     (See report.txt for details)")
        
        logging.info(f"\n{'='*70}")
        
    except FileNotFoundError as e:
        logging.error(f"Error: {e}")
        sys.exit(1)
    except PermissionError as e:
        logging.error(f"Error: Permission denied - {e}")
        sys.exit(1)
    except Exception as e:
        logging.error(f"Error: An unexpected error occurred - {e}")
        logging.debug(f"Exception details:", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Team Formation System - Assigns students to teams based on preferences"
    )
    parser.add_argument(
        "input_file",
        help="Path to the input CSV file containing student preferences"
    )
    parser.add_argument(
        "output_file",
        nargs='?',
        default="out.csv",
        help="Path to the output CSV file for team assignments (default: out.csv)"
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="Run tests before processing"
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose (DEBUG level) logging"
    )
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(verbose=args.verbose)
    
    # Run tests if requested
    if args.test:
        test_passed = run_tests(args.input_file)
        if not test_passed:
            logging.error("\n✗ Tests failed. Please fix issues before proceeding.")
            sys.exit(1)
        logging.info("Proceeding with team formation...\n")
    
    main(args.input_file, args.output_file)

