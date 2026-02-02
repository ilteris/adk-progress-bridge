
import os

def update_main():
    main_file = "backend/app/main.py"
    with open(main_file, "r") as f:
        lines = f.readlines()
    
    with open(main_file, "w") as f:
        for line in lines:
            if 'APP_VERSION = "2.12.58"' in line:
                f.write('APP_VERSION = "2.12.59" # Bumped for v835\n')
            elif 'GIT_COMMIT = "v834-supreme-apex-2480"' in line:
                f.write('GIT_COMMIT = "v835-supreme-apex-2520"\n')
            elif 'OPERATIONAL_APEX = "v834 SUPREME APEX 2480 VERIFICATION"' in line:
                f.write('OPERATIONAL_APEX = "v835 SUPREME APEX 2520 VERIFICATION"\n')
            else:
                f.write(line)
    print(f"Updated {main_file} to Version 2.12.59")

if __name__ == "__main__":
    update_main()

