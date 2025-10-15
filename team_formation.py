#!/usr/bin/env python3
"""
Team Formation System
Assigns students to teams based on their preferences and constraints.
"""

import sys
import os
import argparse
import pandas as pd


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
        
        # Print summary of parsed data
        print(f"\n--- Summary ---")
        print(f"Total students: {len(basic_data['netids'])}")
        print(f"NetIDs successfully extracted from column D")
        
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

