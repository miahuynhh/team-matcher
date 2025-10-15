# Team Formation and Project Assignment System - Prompt Plan

## Project Overview

This document outlines a step-by-step implementation plan for building a team formation system that:
- Forms teams of 5-6 people from a CSV of preferences
- Respects subteam member preferences (keeps subteams together)
- Assigns projects based on team member preferences (1-5 ranking)
- Optimizes for maximum preference satisfaction
- Outputs results in CSV format for Docker deployment

**Input**: `cse403-preferences.csv` with netIDs (column D), project preferences (columns E-AY), subteam members (columns AZ-BE)

**Output**: `out.csv` with format: `(project_name, '[member1, member2, ...]')`

**Constraints**:
- Teams must have 5-6 people
- Subteams cannot be split
- Project must be in top 5 preferences for ALL team members
- Avoid assigning #4 and #5 preferences when possible
- 5-6 person subteams get their most preferred project

---

## Phase 1: Project Foundation and Basic I/O

### Prompt 1: Project Setup and Basic Structure

```
Create a Python project structure for a team formation system with the following:

1. Create a main Python file called `team_formation.py` that will contain our core logic
2. Add a simple command-line interface that accepts an input CSV file path and output path
3. Add basic error handling for file operations
4. Create a `run.sh` bash script that:
   - Installs Python 3 and pip if needed
   - Installs pandas (we'll use this for CSV operations)
   - Runs the Python script: `python3 team_formation.py cse403-preferences.csv out.csv`
   - Makes sure the script is executable

The main file should have:
- A main() function that takes input_file and output_file as parameters
- Basic file existence checking
- A try-except block for error handling
- Placeholder comments for where we'll add parsing, processing, and output logic

Keep it simple - just the skeleton for now. We'll add the actual logic in subsequent steps.
```

---

### Prompt 2: CSV Input Parsing Structure

```
Extend the team_formation.py file to parse the input CSV file using pandas.

Add a function called `parse_input_csv(filepath)` that:
1. Reads the CSV file using pandas (handle encoding issues - try utf-8 first, then latin-1 if that fails)
2. Returns a pandas DataFrame
3. Prints basic information about the data (number of rows, column names)
4. Handles the case where the file doesn't exist or can't be read

Also add a function called `extract_basic_data(df)` that:
1. Takes the DataFrame as input
2. Extracts column D (netID) into a list
3. Prints the first few netIDs to verify parsing works
4. Returns a dictionary with 'netids' as a key

Wire this into the main() function so it:
1. Calls parse_input_csv
2. Calls extract_basic_data
3. Prints a summary of what was parsed

Don't worry about project preferences or subteam members yet - just get the basic CSV reading working with netIDs.
```

---

## Phase 2: Data Extraction and Modeling

### Prompt 3: Extract Project Preferences

```
Add functionality to extract project preferences from the CSV.

Create a function called `extract_project_preferences(df)` that:
1. Identifies all columns from E to AY (these contain project preferences)
2. For each row (person), extracts their project preferences
3. Creates a dictionary mapping netID -> {project_name: ranking}
   - Where ranking is 1-5 (extracted from values like "#1 Choice", "#2 Choice", etc.)
   - Skip blank cells
4. The column headers contain project names in format "[ProjectName]" - extract just the project name

Return a dictionary structure like:
```python
{
    'netid1': {'ProjectA': 1, 'ProjectB': 2, 'ProjectC': 3, 'ProjectD': 4, 'ProjectE': 5},
    'netid2': {'ProjectX': 1, 'ProjectY': 2, ...},
    ...
}
```

Add helper functions as needed:
- `parse_preference_value(cell_value)` - converts "#1 Choice" to 1, handles blank cells
- `extract_project_name(column_header)` - extracts "ProjectName" from "[ProjectName]"

Wire this into main() and print a few examples to verify it's working correctly.
```

---

### Prompt 4: Extract Subteam Member Data

```
Add functionality to extract subteam member preferences.

Create a function called `extract_subteam_data(df)` that:
1. Identifies columns from AZ to BE (these contain subteam member information)
2. For each row (person), extracts who they listed as subteam members
3. Parses the format: "Name, netid" or "Name netid" (note: formatting is inconsistent in the data)
4. Creates a dictionary mapping netID -> list of netIDs they want to work with

Return a dictionary structure like:
```python
{
    'netid1': ['netid2', 'netid3', 'netid4', 'netid5'],
    'netid2': ['netid1', 'netid3', 'netid4', 'netid5'],
    ...
}
```

Add helper functions:
- `parse_member_string(cell_value)` - extracts netID from various formats:
  - "Name, netid"
  - "Name netid" 
  - "Name (netid)"
  - Handle extra spaces, email format (netid@uw.edu or netid@cs.washington.edu)
- Handle blank cells (empty list)
- Handle inconsistencies gracefully (log warnings for unparseable entries)

Wire this into main() and print statistics:
- How many people specified subteam members
- Size distribution of subteam preferences (how many listed 0, 1, 2, 3, 4, 5 members)
- Show a few example subteam groupings
```

---

## Phase 3: Subteam Formation and Validation

### Prompt 5: Identify Complete Subteams

```
Create logic to identify valid, complete subteams.

A subteam is valid when all members mutually list each other. Add a function called `identify_subteams(subteam_prefs)` that:

1. Takes the subteam preferences dictionary from Prompt 4
2. Identifies groups where mutual preferences exist
3. Returns a list of subteams (each subteam is a set of netIDs)

Algorithm approach:
- Start with each person's preference list
- Check if all people in their list also list them back
- A subteam is complete when: for every person A in the subteam, A's preference list contains exactly all other members of the subteam (and A includes themselves)
- Handle edge cases:
  - Person lists themselves
  - Person lists others who don't list them back (incomplete subteam - treat as individual)
  - Person lists no one (individual)

Return structure:
```python
{
    'complete_subteams': [
        {'netid1', 'netid2', 'netid3', 'netid4', 'netid5'},
        {'netid6', 'netid7', 'netid8', 'netid9', 'netid10', 'netid11'},
        ...
    ],
    'individuals': {'netid12', 'netid13', ...}
}
```

Add a function `validate_subteam(members, subteam_prefs)` that checks if a group of netIDs forms a valid subteam.

Wire this into main() and print:
- Number of complete subteams found
- Size of each subteam
- Number of individuals
- Show examples of complete subteams with their members
```

---

### Prompt 6: Calculate Common Project Preferences for Subteams

```
Create logic to find common project preferences across subteam members.

Add a function called `calculate_subteam_project_prefs(subteam, project_prefs)` that:
1. Takes a subteam (set of netIDs) and the project preferences dictionary
2. Finds projects that are in the top 5 for ALL members of the subteam
3. For each common project, calculates an aggregate preference score

Scoring approach:
- A project is valid only if ALL members have it in their top 5
- For valid projects, calculate aggregate score (lower is better):
  - Sum of all members' rankings for that project
  - Example: If 5 members rank a project as [1, 2, 1, 3, 2], aggregate score = 9
- Return projects sorted by aggregate score

Return structure:
```python
{
    'ProjectX': {'aggregate_score': 9, 'rankings': [1, 2, 1, 3, 2]},
    'ProjectY': {'aggregate_score': 12, 'rankings': [2, 2, 3, 2, 3]},
    ...
}
```

Add a function `calculate_team_project_prefs(team_members, project_prefs)` that does the same for any group (we'll reuse this for merged teams).

Wire this into main():
1. For each complete subteam, calculate their common preferences
2. Print the top 3 project choices for each subteam
3. Flag any subteams with no common preferences (this is a problem!)

If a subteam has no common preferences, log an error - this violates the constraint that the project must be in everyone's top 5.
```

---

## Phase 4: Team Formation Strategy

### Prompt 7: Classify Subteams by Size

```
Create logic to classify subteams and prepare for team formation.

Add a function called `classify_subteams(subteams_data)` that:
1. Separates subteams into categories based on size
2. Identifies which subteams can be directly assigned (size 5-6)
3. Identifies which need to be merged or supplemented (size 1-4)

Return structure:
```python
{
    'complete_teams': [
        # Subteams of size 5-6, can be assigned directly
        {'members': {'netid1', 'netid2', 'netid3', 'netid4', 'netid5'}, 'size': 5},
        ...
    ],
    'incomplete_subteams': {
        # Organized by size for easier merging
        1: [{'members': {'netid10'}, 'size': 1}, ...],
        2: [{'members': {'netid11', 'netid12'}, 'size': 2}, ...],
        3: [{'members': {'netid13', 'netid14', 'netid15'}, 'size': 3}, ...],
        4: [{'members': {'netid16', 'netid17', 'netid18', 'netid19'}, 'size': 4}, ...],
    }
}
```

Wire this into main() and print:
- Number of complete teams (size 5-6)
- Breakdown of incomplete subteams by size
- Total number of people in complete vs incomplete teams

This sets us up for the next step: merging incomplete subteams into valid teams.
```

---

### Prompt 8: Team Formation - Merge Compatible Subteams

```
Create logic to merge smaller subteams into valid teams of 5-6 people.

Add a function called `merge_subteams_into_teams(incomplete_subteams, project_prefs)` that:
1. Takes incomplete subteams organized by size
2. Attempts to merge them into teams of 5-6 people
3. Only merges subteams that have at least one common project preference
4. Prioritizes merges that result in better preference alignment

Strategy:
- Start with size 4 subteams - they need 1-2 more people
- Try to add individuals (size 1) or pairs (size 2) that have compatible preferences
- Then handle size 3 subteams - can merge with another size 3, or with size 2+individual
- Then size 2 subteams - can merge with another size 2 + individual, or with size 3
- Finally handle remaining individuals - group them if they have compatible preferences

For compatibility checking, add a function `check_compatibility(subteam1, subteam2, project_prefs)`:
- Returns True if the combined group has at least one common project in everyone's top 5
- Returns False otherwise

Return structure:
```python
{
    'formed_teams': [
        {
            'members': {'netid1', 'netid2', 'netid3', 'netid4', 'netid5'},
            'source_subteams': [subteam1, subteam2],  # Track where members came from
            'size': 5
        },
        ...
    ],
    'unmatched': [
        # Subteams that couldn't be matched into teams of 5-6
        # We'll need to handle these separately
    ]
}
```

Wire this into main() and print:
- Number of successfully formed teams
- Number of people successfully placed in teams
- Number of unmatched subteams/individuals
- Show examples of merged teams

Note: It's okay if some people can't be placed - the problem may not have a perfect solution. We'll report unmatched people in the output or in a separate log.
```

---

## Phase 5: Project Assignment

### Prompt 9: Assign Projects to Complete Teams (5-6 person subteams)

```
Create logic to assign projects to teams that were originally 5-6 person subteams.

Add a function called `assign_projects_to_complete_subteams(complete_teams, project_prefs)` that:
1. For each 5-6 person subteam, assign their most preferred common project
2. Track which projects have been assigned to which teams
3. Handle the case where multiple teams want the same project (this is allowed - multiple teams can work on the same project)

For each team:
1. Calculate their common project preferences (reuse function from Prompt 6)
2. Assign the project with the lowest aggregate score (most preferred)
3. Store the assignment

Return structure:
```python
{
    'assignments': [
        {
            'team_members': ['netid1', 'netid2', 'netid3', 'netid4', 'netid5'],
            'project': 'ProjectX',
            'aggregate_score': 9
        },
        ...
    ]
}
```

Wire this into main() and print:
- Each team assignment
- Distribution of preference scores (how many teams got aggregate score 5 (all #1), 6-10, 11-15, etc.)
- Check if any teams had to be assigned a project where someone got their #4 or #5 choice (flag these)
```

---

### Prompt 10: Assign Projects to Merged Teams

```
Create logic to assign projects to teams formed by merging smaller subteams.

Add a function called `assign_projects_to_merged_teams(merged_teams, project_prefs)` that:
1. For each merged team, find common project preferences across all members
2. Assign the project that maximizes overall satisfaction
3. Use the same aggregate scoring approach as before

Since these teams were formed by merging, they were already checked for compatibility (at least one common project), so we know a valid assignment exists.

Use the same return structure as Prompt 9.

Wire this into main() and print:
- Each merged team assignment  
- Compare preference satisfaction between complete subteams and merged teams
- Flag any teams where someone got their #4 or #5 choice

At this point, we should have a complete list of:
- Team assignments (project + members) for all successfully formed teams
- Any unmatched individuals/subteams that couldn't be placed
```

---

## Phase 6: Output Generation

### Prompt 11: Format and Write Output CSV

```
Create logic to format the output and write to CSV.

Add a function called `write_output_csv(assignments, output_filepath)` that:
1. Takes the list of team assignments
2. Formats each as: (project_name, '[member1, member2, member3, member4, member5]')
3. Writes to a CSV file with proper formatting

Formatting requirements:
- First column: project name (string, no quotes in the CSV)
- Second column: member list as a string representation of a list: '[member1, member2, ...]'
- Use pandas to write the CSV to ensure proper escaping

Example output:
```
CookiesShallNotPass,[amarto, azitab, cbither, elijoshi, spenj]
Align,[kiann2, erathi, dpetkau, vishksat, lberna]
```

Also add a function called `generate_report(assignments, unmatched)` that:
1. Creates a summary report
2. Saves it as `report.txt` with:
   - Total number of teams formed
   - Total number of people successfully placed
   - Number of unmatched people
   - Distribution of preference satisfaction
   - List of unmatched people (if any)

Wire this into main():
1. Combine all assignments (complete subteams + merged teams)
2. Sort by project name for consistent output
3. Write output CSV
4. Generate report
5. Print success message with summary statistics
```

---

### Prompt 12: Add Pandas Validation

```
Add validation to ensure the output CSV can be properly read by pandas.

Add a function called `validate_output(output_filepath)` that:
1. Reads the output CSV using pandas
2. Verifies the format is correct
3. Checks that each row has exactly 2 columns
4. Verifies member lists are properly formatted
5. Prints validation results

Call this at the end of main() after writing the output file.

If validation fails, print clear error messages indicating what's wrong.

This ensures the output meets the requirement: "please try to use pandas dataframe to parse your out.csv to smoke-test it works"
```

---

## Phase 7: Optimization and Edge Cases

### Prompt 13: Handle Edge Cases and Improve Robustness

```
Improve the system to handle edge cases and inconsistencies in the input data.

Add/enhance the following:

1. Data cleaning in `extract_subteam_data`:
   - Handle typos in netIDs (fuzzy matching against known netIDs)
   - Handle case sensitivity (normalize to lowercase)
   - Handle email formats vs plain netIDs
   - Log warnings for netIDs that appear in subteam lists but not in the main data

2. Subteam validation improvements:
   - Handle cases where person A lists person B, but B doesn't list A
   - Option to create "partial" subteams where most (but not all) members agree
   - Allow singleton "subteams" (individuals) to be treated as valid

3. Project assignment fallback:
   - If a merged team has no common preferences in top 5, log it as an error but try to find the "least bad" assignment
   - Allow assignments where at most one person gets a project not in their top 5, if necessary

4. Input validation:
   - Check for duplicate netIDs
   - Check for people who submitted preferences but didn't select exactly 5 projects
   - Check for missing required data

Wire these improvements throughout the codebase and add comprehensive error messages.

Update the report to include:
- Data quality issues found
- Edge cases encountered
- Decisions made for ambiguous cases
```

---

### Prompt 14: Optimize Project Assignments

```
Add optimization logic to improve overall satisfaction.

Currently we assign projects greedily (first valid option). Let's add optimization:

Add a function called `optimize_assignments(teams, project_prefs)` that:
1. Takes all teams (both complete and merged)
2. Finds the optimal project assignment that minimizes total aggregate score
3. Ensures all constraints are still met (project must be in everyone's top 5)

Approach:
- For each team, we already have their list of valid projects with aggregate scores
- We want to assign projects such that the sum of all aggregate scores is minimized
- This is an assignment problem, but since multiple teams can work on the same project, it's simpler than the classic version

Algorithm:
1. For each team, calculate valid projects and scores
2. Sort each team's options by score (best first)
3. Assign each team to their best available option
4. Note: No conflicts since multiple teams can have the same project

Actually, given that multiple teams can share projects, the greedy approach (each team gets their best option) is already optimal. But add this analysis to verify our assignments are optimal.

Add a function `analyze_assignments(assignments, project_prefs)` that:
- Calculates statistics on preference satisfaction
- Shows how many people got their #1, #2, #3, #4, #5 choice
- Identifies the "worst" assignments (highest aggregate scores or people with #4/#5 choices)
- Suggests if any improvements could be made

Wire this into main() and include the analysis in the report.
```

---

## Phase 8: Testing and Integration

### Prompt 15: Add Comprehensive Testing

```
Add testing and validation throughout the pipeline.

Create a function called `run_tests(input_filepath)` that:
1. Tests each component with the actual input data
2. Validates intermediate results at each stage
3. Checks for logical inconsistencies

Tests to add:
1. CSV parsing: verify all expected columns exist
2. Data extraction: verify no data loss (all rows processed)
3. Subteam identification: verify mutual listings are detected correctly
4. Project preferences: verify all teams have valid common preferences
5. Team formation: verify all teams have 5-6 members
6. Project assignment: verify all assignments satisfy constraints
7. Output format: verify CSV is correctly formatted

Add assertion checks:
```python
assert len(team['members']) in [5, 6], f"Invalid team size: {len(team['members'])}"
assert all(project in prefs for prefs in member_prefs), "Project not in someone's top 5"
```

Add a `--test` flag to the command line interface that runs these tests before proceeding with actual output generation.

Update run.sh to run tests first, then generate output.
```

---

### Prompt 16: Add Logging and Debugging Output

```
Add comprehensive logging to help debug issues.

Add a logging module with different levels:
- INFO: Normal progress messages
- WARNING: Data quality issues, edge cases
- ERROR: Violations of constraints, unmatched people
- DEBUG: Detailed processing information

Create a `setup_logging()` function that:
1. Configures Python logging
2. Writes logs to both console and `team_formation.log`
3. Uses appropriate log levels throughout the codebase

Replace all print statements with appropriate logging calls:
- Progress updates → logging.info()
- Data issues → logging.warning()
- Constraint violations → logging.error()
- Detailed processing → logging.debug()

Add a `--verbose` flag to enable DEBUG level logging.

Update run.sh to save the log file in the output directory.

This will help troubleshoot issues when running in Docker.
```

---

### Prompt 17: Final Integration and Polish

```
Integrate all components and add final polish.

1. Review the entire codebase:
   - Ensure consistent naming conventions
   - Add docstrings to all functions
   - Add type hints where appropriate
   - Ensure proper error handling everywhere

2. Update main() to:
   - Use clear step-by-step processing with progress indicators
   - Handle all error cases gracefully
   - Produce informative output at each stage
   - Generate both the required CSV and an optional detailed report

3. Enhance run.sh:
   - Add error checking at each step
   - Verify output file was created successfully
   - Print summary of results
   - Handle the case where dependencies are already installed (faster re-runs)

4. Add command-line options:
   - `--input` or `-i`: input CSV path (default: cse403-preferences.csv)
   - `--output` or `-o`: output CSV path (default: out.csv)
   - `--verbose` or `-v`: verbose logging
   - `--report`: generate detailed report (default: True)
   - `--test`: run validation tests

5. Create a README for the a3 folder explaining:
   - What the code does
   - How to run it locally
   - How to run it in Docker
   - What files are generated

6. Final testing:
   - Run with the provided input file
   - Verify output format matches requirements
   - Test in a clean Docker environment
   - Verify the zip structure is correct
```

---

## Phase 9: Docker Testing and Deployment

### Prompt 18: Prepare for Docker Deployment

```
Ensure the solution works correctly in the Docker environment specified in the README.

1. Test run.sh in a clean environment:
   - Verify it works on Ubuntu (bash)
   - Make sure Python 3 installation works
   - Ensure pandas can be installed without issues
   - Handle potential apt-get update delays

2. Update run.sh to be more robust:
```bash
#!/bin/bash
set -e  # Exit on any error

# Install dependencies
echo "Installing Python dependencies..."
python3 -m pip install --quiet pandas numpy

# Run the team formation script
echo "Running team formation algorithm..."
python3 team_formation.py cse403-preferences.csv out.csv

# Verify output was created
if [ ! -f out.csv ]; then
    echo "Error: out.csv was not created!"
    exit 1
fi

echo "Team formation complete! Output written to out.csv"
echo "Number of teams formed: $(wc -l < out.csv)"
```

3. Create the a3.zip structure:
   - Verify all necessary files are included
   - Test unzipping and running in Docker
   - Make sure the output path (/workspace/out.csv) is correct

4. Add final validation:
   - After generating out.csv, read it back with pandas
   - Print the first few rows to verify format
   - Verify no syntax errors in the CSV

5. Document any assumptions or limitations in a NOTES.txt file.

Test the complete Docker workflow using the exact command from the README:
```bash
docker run --rm -it -v "$(pwd)":/workspace -w /workspace ubuntu bash -lc "\
export DEBIAN_FRONTEND=noninteractive && \
apt-get update && apt-get install -y unzip python3 && \
unzip -o a3.zip && \
cd a3 && \
chmod +x run.sh && \
./run.sh"
```

Ensure out.csv appears in the workspace after running.
```

---

## Summary and Implementation Notes

### Key Design Decisions

1. **Subteam Formation**: Use mutual listing validation - only form subteams where all members list each other
2. **Team Merging**: Only merge subteams with compatible project preferences
3. **Project Assignment**: Greedy assignment works since multiple teams can share projects
4. **Edge Cases**: Log warnings for data quality issues but continue processing when possible
5. **Output Format**: Use pandas to ensure proper CSV formatting

### Dependencies

- Python 3
- pandas library
- Standard library: csv, logging, argparse, sys, collections

### Testing Strategy

1. Unit test each function with sample data
2. Integration test with the full input file
3. Validate output format with pandas
4. Test in Docker environment
5. Verify all constraints are satisfied

### Success Criteria

- All teams have 5-6 members ✓
- No subteams are split ✓
- All project assignments are in each member's top 5 ✓
- Output CSV format matches specification ✓
- Works in Docker environment ✓
- Maximizes preference satisfaction ✓

### Implementation Order

Execute prompts 1-18 in sequence. Each prompt builds on the previous work, with clear integration points. No orphaned code - each step produces working, testable functionality that feeds into the next step.

---

## Appendix: Data Structure Reference

### Internal Data Structures

```python
# Person's project preferences
project_prefs = {
    'netid': {
        'ProjectName': 1,  # ranking 1-5
        'ProjectName2': 2,
        ...
    }
}

# Subteam membership preferences
subteam_prefs = {
    'netid': ['netid2', 'netid3', 'netid4']  # who they want to work with
}

# Identified subteams
subteams = {
    'complete_subteams': [
        {'netid1', 'netid2', 'netid3', 'netid4', 'netid5'},
        ...
    ],
    'individuals': {'netid10', 'netid11', ...}
}

# Team assignments
assignments = [
    {
        'team_members': ['netid1', 'netid2', 'netid3', 'netid4', 'netid5'],
        'project': 'ProjectName',
        'aggregate_score': 9
    },
    ...
]
```

### Output Format

```csv
ProjectName1,[member1, member2, member3, member4, member5]
ProjectName2,[member6, member7, member8, member9, member10, member11]
```

---

## Notes for the LLM

- Each prompt is self-contained but builds on previous work
- Always test intermediate results before moving to the next step
- Use descriptive variable names and add comments
- Handle edge cases gracefully with appropriate logging
- Prioritize correctness over optimization initially
- Add optimization once basic functionality works
- Keep functions focused and modular for easier testing and debugging

