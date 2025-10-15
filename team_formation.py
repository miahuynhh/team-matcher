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
                print(f"\n⚠️  ERROR: Subteam {i+1} has NO common project preferences!")
                print(f"   Members: {', '.join(sorted(subteam))}")
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
        
        # Merge incomplete subteams into valid teams
        merged_results = merge_subteams_into_teams(classified_teams['incomplete_subteams'], project_prefs)
        
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
            print(f"\n⚠️  Unmatched Subteams/Individuals:")
            print(f"  Total unmatched: {len(merged_results['unmatched'])}")
            unmatched_people = []
            for team in merged_results['unmatched']:
                unmatched_people.extend(sorted(team['members']))
            print(f"  Unmatched people ({len(unmatched_people)}): {', '.join(unmatched_people[:10])}")
            if len(unmatched_people) > 10:
                print(f"    ... and {len(unmatched_people) - 10} more")
        
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
        
        if merged_results['unmatched']:
            unmatched_count = len(merged_results['unmatched'])
            unmatched_people_count = sum(team['size'] for team in merged_results['unmatched'])
            print(f"  Unmatched: {unmatched_count} subteams ({unmatched_people_count} people)")
        else:
            print(f"  Unmatched: 0 (all students placed!)")
        print(f"\nNetIDs successfully extracted from column D")
        print(f"Project preferences successfully extracted")
        print(f"Subteam data successfully extracted")
        print(f"Subteam validation completed")
        print(f"Team classification completed")
        print(f"Team merging completed")
        
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

