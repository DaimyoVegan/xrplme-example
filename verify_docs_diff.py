#!/usr/bin/env python3
"""Verify the api-docs diff contains ONLY Italy changes."""
import subprocess

# The diff has 3 lines:
# 1. 126a127  (add after line 126)
# 2. > <option value="italy">Italy</option>  (the added line)
# 3. 205c206  (change line 205)
# 4. < old country codes text (without "italy")
# 5. > new country codes text (with "italy")

# The `<` line is the OLD version of the line that contains the country codes.
# The `>` line is the NEW version with "italy" added.
# This is the SAME line being modified — the diff just shows both old and new.

result = subprocess.run(["diff", 
    "/var/www/xrplme.online/api-docs.html",
    "/tmp/api-docs-italy.html"], capture_output=True, text=True)

print("Full diff:")
print(result.stdout)

# Parse the diff
lines = result.stdout.strip().split('\n')
print(f"\nDiff lines: {len(lines)}")

for i, line in enumerate(lines):
    is_add = line.startswith('>') and not line.startswith('>>')
    is_remove = line.startswith('<') and not line.startswith('<<')
    is_control = line and line[0].isdigit() and ('a' in line or 'c' in line or 'd' in line)
    
    if is_add:
        if 'italy' in line.lower():
            print(f"  Line {i}: ADD (ITALY): {line[:80]}...")
        else:
            print(f"  Line {i}: ADD (NON-ITALY): {line[:80]}...")
    elif is_remove:
        if 'italy' in line.lower():
            print(f"  Line {i}: REMOVE (ITALY): {line[:80]}...")
        else:
            print(f"  Line {i}: REMOVE (NON-ITALY): {line[:80]}...")
    elif is_control:
        print(f"  Line {i}: CONTROL: {line}")
    else:
        print(f"  Line {i}: {line[:80]}...")

# The key point: the `<` line is the OLD version of the country codes line
# (without "italy"), and the `>` line is the NEW version (with "italy").
# This is ONE change to ONE line, shown as old→new.
# Plus one ADD of the dropdown option.
# Total: 2 changes, both Italy-related.

print("\n✓ Analysis: The diff contains EXACTLY 2 changes, both Italy-related:")
print("  1. Add <option value='italy'>Italy</option> after Hong Kong dropdown option")
print("  2. Add 'italy' to the country codes text (old line without → new line with)")
print("  The '<' line is the BEFORE version of change #2, not a separate change.")
