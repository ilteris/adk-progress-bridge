
import os

def fix_duplicates():
    file_path = "backend/app/dummy_tool.py"
    with open(file_path, "r") as f:
        lines = f.readlines()
    
    seen_names = set()
    duplicated_names = set()
    
    # First pass to find duplicated names
    for line in lines:
        if "@progress_tool(name=" in line:
            name = line.split('"')[1]
            if name in seen_names:
                duplicated_names.add(name)
            seen_names.add(name)
    
    print(f"Found {len(duplicated_names)} duplicated names.")
    
    # Second pass to rename the SECOND occurrence
    new_lines = []
    fixed_names = set()
    for line in lines:
        if "@progress_tool(name=" in line:
            name = line.split('"')[1]
            if name in duplicated_names:
                if name in fixed_names:
                    # This is the second occurrence (or more)
                    new_name = name + "_v2"
                    line = line.replace(f'name="{name}"', f'name="{new_name}"')
                    # Also need to find the next line with "async def" and rename it
                fixed_names.add(name)
        
        # Also need to handle the function name in "async def"
        if "async def " in line:
             func_name = line.split("async def ")[1].split("(")[0]
             # If we just renamed a tool, we should probably rename the function too if it matches
             # But the decorator handles the registry name.
             # Actually, if we have:
             # @progress_tool(name="foo")
             # async def foo(): ...
             # @progress_tool(name="foo")
             # async def foo(): ...
             # We need to change both.
        
        new_lines.append(line)
        
    # More robust renaming:
    final_lines = []
    occurrences = {}
    
    for i in range(len(lines)):
        line = lines[i]
        if "@progress_tool(name=" in line:
            name = line.split('"')[1]
            occurrences[name] = occurrences.get(name, 0) + 1
            if occurrences[name] > 1:
                # Rename this occurrence
                new_name = f"{name}_unique_{occurrences[name]}"
                line = line.replace(f'name="{name}"', f'name="{new_name}"')
                
                # Try to rename the function in the next few lines
                for j in range(i+1, min(i+5, len(lines))):
                    if "async def " in lines[j]:
                        func_name = lines[j].split("async def ")[1].split("(")[0]
                        new_func_name = f"{func_name}_unique_{occurrences[name]}"
                        lines[j] = lines[j].replace(f"async def {func_name}", f"async def {new_func_name}")
                        break
        final_lines.append(line)

    with open(file_path, "w") as f:
        f.writelines(final_lines)
    print("Fixed duplicates in " + file_path)

if __name__ == "__main__":
    fix_duplicates()
