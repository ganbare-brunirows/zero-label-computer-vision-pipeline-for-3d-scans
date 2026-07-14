---
name: run-houdini-scan-prep
description: Executes the Houdini hython script (C:\Users\bruni\Documents\AgentsSkillsWorkflows\.agents\scripts\houdini_scans_prepration.py) to process raw scans into a merged and optimized USD file for Isaac Sim. Use this when the Simulation Engineer needs to prepare the dataset.
---
# Houdini Scan Preparation Skill

## Instructions
1. Run the `hython` script located at `C:\Users\bruni\Documents\AgentsSkillsWorkflows\.agents\scripts\houdini_scans_prepration.py`.
2. Depending on the script's required arguments (like input directory and output USD path), execute it using the `run_command` tool.
   Example: `hython scripts/houdini_scans_preparation.py <folder_with_objs>`
3. Ensure the process completes successfully and verify the output USD file is generated in the correct output directory.
4. If there are errors related to missing modules or Houdini license, report them clearly to the user.
5. Send the output usd file and the folder with the subfolders to the next step of the workflow
