import os

def save_filenames_as_ts_array():
    # Get the current directory
    current_dir = os.getcwd()

    # Get all file names in the directory (excluding directories)
    filenames = [f for f in os.listdir(current_dir) if os.path.isfile(os.path.join(current_dir, f))]

    # Format filenames as a TypeScript array
    ts_array_content = f"export const fileNames: string[] = {filenames};"

    # Save to a `names.ts` file
    output_file = os.path.join(current_dir, "names.ts")
    with open(output_file, "w", encoding="utf-8") as ts_file:
        ts_file.write(ts_array_content)

    print(f"File names have been saved to {output_file}.")

# Run the function
if __name__ == "__main__":
    save_filenames_as_ts_array()