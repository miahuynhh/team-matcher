Create a new program that forms teams of 5-6 people and assigns each team to a project.

The input to the program is a spreadsheet of preferences submitted by the people.
 * Each person gives their preferences for subteam members.  (A subteam may have size 1.)
 * Each person also gives 5 preferences for their project.

The member and project preferences must be consistent across all the members of a subteam.

The input spreadsheet is in file `cse403-preferences.csv`.  It has the following structure:
 * netID (a unique identifier) in column D.
 * project preferences in columns E-AY, with the project name in the column header and a value that is blank or is the person's preference ranking of that project.
 * subteam members in columns AZ-BE.

The output is a list of teams.  Each team contains 5-6 people and an assigned project.
A team consists of one or more subteams.

Subteams are not split up:  each person is in the same team as all of their preferred subteam members.

A team is assigned a project that is one of the 5 preferences for each of its members.

When a subteam has size 5 or 6, assign it to a team that is working on its most preferred project.

Given the above constraints, assign each team to the most preferred possible project.  More specicially, form teams so as to satisfy as many members' project preference as possible.
Ideally, every person would be in a team working on that person's most preferred project.
It is undesirable for anyone to be assigned to their #4 or #5 preferred project.

Submit a a3.zip that contains a folder a3/, under a3, you should have all your source codeand a run.sh shell script.

## Reproducing Results with Docker

You should write a `run.sh` under a3/ also such that it can 1. install necessary libs and 2. generate the output and save it to `out.csv`.

Your `out.csv` should have the following schema (team_proj_name, all_team_members), where first element is a string and second is a list of strings
For example, a row would look like:

('CookiesShallNotPass', '[m1, m2, m3, m4, m5, m6]')

This means that a group containing '[m1, m2, m3, m4, m5, m6]' is assigned the project 'CookiesShallNotPass'. 

(NOTE: this is in tuple format for demonstration purpose, please follow CSV format when running your code.)

(NOTE: please try to use pandas dataframe to parse your out.csv to smoke-test it works.)

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
