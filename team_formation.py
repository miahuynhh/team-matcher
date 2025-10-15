#!/usr/bin/env python3
"""
Team Formation System
Assigns students to teams based on their preferences and constraints.
"""

import sys
import os
import argparse
import pandas as pd
import re


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


def extract_subteam_data(df):
    """
    Extract subteam member preferences from the DataFrame.
    
    Args:
        df (pd.DataFrame): The parsed DataFrame
        
    Returns:
        dict: Dictionary mapping netID -> list of netIDs they want to work with
              e.g., {'netid1': ['netid2', 'netid3'], ...}
    """
    print(f"\n--- Extracting subteam data ---")
    
    # Get netIDs from column D (index 3)
    netids = df.iloc[:, 3].tolist()
    
    # Find Team Member columns (they start after the project columns)
    team_member_columns = []
    for i in range(len(df.columns)):
        col_name = df.columns[i]
        if 'Team Member' in col_name:
            team_member_columns.append(i)
    
    print(f"Found {len(team_member_columns)} team member columns")
    
    # Build subteam dictionary
    subteams = {}
    unparseable_entries = []
    
    for row_idx, netid in enumerate(netids):
        team_members = []
        
        for col_idx in team_member_columns:
            cell_value = df.iloc[row_idx, col_idx]
            member_netid = parse_member_string(cell_value)
            
            if member_netid is not None:
                # Avoid duplicates and self-references
                if member_netid not in team_members and member_netid != netid:
                    team_members.append(member_netid)
                elif member_netid == netid:
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


def main(input_file, output_file):
    """
    Main function for team formation.
    
    Args:
        input_file (str): Path to the input CSV file with student preferences
        output_file (str): Path to write the output CSV file with team assignments
    """
    try:
        # Check if input file exists
        if not os.path.exists(input_file):
            raise FileNotFoundError(f"Input file not found: {input_file}")
        
        print(f"Reading preferences from: {input_file}")
        
        # Parse the CSV file and load student preferences
        df = parse_input_csv(input_file)
        
        # Extract basic data (netIDs for now)
        basic_data = extract_basic_data(df)
        
        # Extract project preferences
        project_prefs = extract_project_preferences(df)
        
        # Extract subteam data
        subteam_data = extract_subteam_data(df)
        
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
        
        # Print examples of subteam groupings
        print(f"\n--- Sample Subteam Groupings ---")
        # Find some interesting examples with different sizes
        examples_by_size = {}
        for netid, members in subteam_data.items():
            size = len(members)
            if size not in examples_by_size:
                examples_by_size[size] = []
            if len(examples_by_size[size]) < 2:  # Keep up to 2 examples per size
                examples_by_size[size].append((netid, members))
        
        for size in sorted(examples_by_size.keys(), reverse=True):
            if size > 0:  # Skip people with no subteam
                for netid, members in examples_by_size[size][:1]:  # Show 1 per size
                    print(f"\n{netid} wants to work with {len(members)} people:")
                    for member in members:
                        print(f"  - {member}")
        
        # Print summary of parsed data
        print(f"\n--- Summary ---")
        print(f"Total students: {len(basic_data['netids'])}")
        print(f"Students with preferences: {sum(1 for p in project_prefs.values() if p)}")
        print(f"Students with subteam preferences: {sum(1 for s in subteam_data.values() if s)}")
        print(f"NetIDs successfully extracted from column D")
        print(f"Project preferences successfully extracted")
        print(f"Subteam data successfully extracted")
        
        # TODO: Process the data and form teams
        # This will include the team formation algorithm
        
        # TODO: Generate output and write to CSV
        # This will format the results and write to the output file
        
        print(f"\nTeam assignments will be written to: {output_file}")
        print("Team formation completed successfully!")
        
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except PermissionError as e:
        print(f"Error: Permission denied - {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: An unexpected error occurred - {e}", file=sys.stderr)
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
        help="Path to the output CSV file for team assignments"
    )
    
    args = parser.parse_args()
    main(args.input_file, args.output_file)

