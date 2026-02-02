import os
import re

def update_main():
    main_file = "backend/app/main.py"
    with open(main_file, "r") as f:
        content = f.read()
    
    content = re.sub(r'APP_VERSION = ".*?"', 'APP_VERSION = "2.12.69"', content)
    content = re.sub(r'GIT_COMMIT = ".*?"', 'GIT_COMMIT = "v845-supreme-apex-2920"', content)
    content = re.sub(r'OPERATIONAL_APEX = ".*?"', 'OPERATIONAL_APEX = "v845 SUPREME APEX 2920 VERIFICATION"', content)
    
    with open(main_file, "w") as f:
        f.write(content)
    print(f"Updated {main_file}")

if __name__ == "__main__":
    update_main()
