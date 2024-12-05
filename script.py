import os

# Directory to walk through
directory_path = './'

# List to store file name changes
books = []

# Function to separate numbers from file names
def separate_number_from_filename(filename):
    # Check if the filename starts with a number
    if filename[0].isdigit():
        # Find the first non-digit character index
        i = 0
        while i < len(filename) and filename[i].isdigit():
            i += 1
        # Create the new filename by inserting a space after the number
        new_filename = filename[:i] + ' ' + filename[i:]
        return new_filename
    return filename

# Walk through the directory
for root, dirs, files in os.walk(directory_path):
    for file in files:
        # Skip the script file itself to avoid renaming it
        if file == os.path.basename(__file__):
            continue

        # Get the new filename if it starts with a number
        new_file_name = separate_number_from_filename(file)
        
        if new_file_name != file:
            # Rename the file if the name has changed
            old_file_path = os.path.join(root, file)
            new_file_path = os.path.join(root, new_file_name)
            os.rename(old_file_path, new_file_path)
            print(f"Renamed: {file} -> {new_file_name}")
        
        # Create a book object with title (new filename without extension)
        book = {
            "id": file.split('.')[0],  # Assuming the filename before extension is the ID
            "title": new_file_name.rsplit('.', 1)[0]  # Remove extension from the filename for the title
        }
        
        # Add the book object to the list
        books.append(book)

# Export to a JavaScript file
js_export = 'const books = ' + str(books).replace("'", '"') + ';'

# Write the export to a JavaScript file
with open('./books.js', 'w') as js_file:
    js_file.write(js_export)

print("Books data exported to books.js")
