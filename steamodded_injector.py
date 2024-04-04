import subprocess
import os
import sys
import tempfile
import zipfile
import platform

def merge_directory_contents(directory_path):
    directory_content = ""
    core_file_name = "core.lua"
    
    if os.path.exists(directory_path):
        print(f"Processing directory: {directory_path}")
        
        # Process core.lua first if it exists
        core_file_path = os.path.join(directory_path, core_file_name)
        if os.path.isfile(core_file_path):
            try:
                with open(core_file_path, "r", encoding="utf-8") as file:
                    directory_content += file.read() + "\n"  # Append the core file content first
                    print(f"Appended {core_file_name} to the directory content")
            except IOError as e:
                print(f"Error reading {core_file_path}: {e}")
        
        # Process the rest of the .lua files
        for file_name in os.listdir(directory_path):
            if file_name.endswith(".lua") and file_name != core_file_name:  # Skip the core.lua file
                file_path = os.path.join(directory_path, file_name)
                try:
                    with open(file_path, "r", encoding="utf-8") as file:
                        file_content = file.read()
                        directory_content += "\n" + file_content
                        print(f"Appended {file_name} to the directory content")
                except IOError as e:
                    print(f"Error reading {file_path}: {e}")
    else:
        print(f"Directory not found: {directory_path}")
    return directory_content


def modify_main_lua(main_lua_path, base_dir, directories):
    print(f"Modifying {main_lua_path} with files from {directories} in {base_dir}")

    try:
        with open(main_lua_path, "r", encoding="utf-8") as file:
            main_lua_content = file.read()
    except IOError as e:
        print(f"Error reading {main_lua_path}: {e}")
        return

    for directory in directories:
        directory_path = os.path.join(base_dir, directory)
        print(f"Looking for directory: {directory_path}")  # Debug print
        directory_content = merge_directory_contents(directory_path)
        main_lua_content += "\n" + directory_content

    try:
        with open(main_lua_path, "w", encoding="utf-8") as file:
            file.write(main_lua_content)
    except IOError as e:
        print(f"Error writing to {main_lua_path}: {e}")


def modify_game_lua(game_lua_path):
    try:
        with open(game_lua_path, "r", encoding="utf-8") as file:
            lines = file.readlines()

        target_line = "    self.SPEEDFACTOR = 1\n"
        insert_line = "    initSteamodded()\n"  # Ensure proper indentation
        target_index = None

        for i, line in enumerate(lines):
            if target_line in line:
                target_index = i
                break  # Find the first occurrence and stop

        if target_index is not None:
            print("Target line found. Inserting new line.")
            lines.insert(target_index + 1, insert_line)
            with open(game_lua_path, "w", encoding="utf-8") as file:
                file.writelines(lines)
            print("Successfully modified game.lua.")
        else:
            print("Target line not found in game.lua.")

    except IOError as e:
        print(f"Error modifying game.lua: {e}")


print("Starting the process...")

# Determine the base directory (where the .exe is located)
if getattr(sys, "frozen", False):
    # Running in a PyInstaller or Nuitka bundle
    base_dir = os.path.dirname(sys.executable)
else:
    # Running in a normal Python environment
    base_dir = os.path.dirname(os.path.abspath(__file__))

seven_zip_file = os.path.join(base_dir, "7-zip/7z.zip")

# Temporary directory for 7-Zip suite
seven_zip_dir = tempfile.TemporaryDirectory()
print(seven_zip_dir.name)
print("Extracting 7-Zip suite...")
with zipfile.ZipFile(seven_zip_file, "r") as zip_ref:
    zip_ref.extractall(seven_zip_dir.name)

# Check the operating system
#if os.name() == 'Linux':
#    seven_zip_path = ['wine', os.path.join(seven_zip_dir.name, "7z.exe")]
#elif os.name == 'nt':
#    seven_zip_path = os.path.join(seven_zip_dir.name, "7z.exe")
#else:
#    # Handle other operating systems or raise an error
#    raise NotImplementedError("This script only supports Windows and Linux.")

seven_zip_path = f"{seven_zip_dir.name}/7z.exe"

# Determine the operating system and prepare the 7-Zip command accordingly
if os.name == 'posix':
    if platform.system() == 'Darwin':
        # This is macOS
        command = "7zz"  # Update this path as necessary for macOS
    else:
        # This is Linux or another POSIX-compliant OS
        command = "7zz"
else:
    # This is for Windows
    command = f"{seven_zip_dir.name}/7z.exe"

#command = seven_zip_dir + ["x", "-o" + temp_dir.name, sfx_archive_path]

# seven_zip_path = os.path.join(seven_zip_dir.name, "7z.exe")

# Check if the SFX archive path is provided
if len(sys.argv) < 2:
    sfx_archive_path = input("请输入 Balatro.exe 文件路径（可直接拖入）：")
    if not os.path.exists(sfx_archive_path):
        print("Please drag and drop the SFX archive onto this executable.")
        seven_zip_dir.cleanup()
        sys.exit(1)
else:
    sfx_archive_path = sys.argv[1]
print(f"SFX Archive received: {sfx_archive_path}")

# Temporary directory for extraction and modification
temp_dir = tempfile.TemporaryDirectory()
print(temp_dir.name)
# Extract the SFX archive
#subprocess.run([command, "x", "-o" + temp_dir.name, sfx_archive_path])
subprocess.run([command, "x", f"-o{temp_dir.name}", sfx_archive_path], check=True)
print("Extraction complete.")

# Path to main.lua and game.lua within the extracted files
main_lua_path = os.path.join(temp_dir.name, "main.lua")
game_lua_path = os.path.join(temp_dir.name, "game.lua")
decompile_output_path = os.path.join(temp_dir.name, "output")
os.makedirs(decompile_output_path, exist_ok=True)  # Create the output directory

main_lua_output_path = os.path.join(temp_dir.name, "main.lua")

# Modify main.lua
directories = ["core", "debug", "loader"]
modify_main_lua(main_lua_output_path, base_dir, directories)
print("Modification of main.lua complete.")

# Modify main.lua
modify_game_lua(game_lua_path)
print("Modification of game.lua complete.")

# Update the SFX archive with the modified main.lua
#subprocess.run([command, "a", sfx_archive_path, main_lua_output_path])
subprocess.run([command, "a", sfx_archive_path, main_lua_output_path], check=True)
# Update the SFX archive with the modified game.lua
#subprocess.run([command, "a", sfx_archive_path, game_lua_path])
subprocess.run([command, "a", sfx_archive_path, game_lua_path], check=True)
print("SFX Archive updated.")

seven_zip_dir.cleanup()
temp_dir.cleanup()

print("处理完成，按任意键退出...")
input()
