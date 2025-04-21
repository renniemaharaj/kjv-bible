import os

def sort_biblical_order(books):
    bible_order = [
        "Genesis", "Exodus", "Leviticus", "Numbers", "Deuteronomy",
        "Joshua", "Judges", "Ruth", "1 Samuel", "2 Samuel",
        "1 Kings", "2 Kings", "1 Chronicles", "2 Chronicles", "Ezra",
        "Nehemiah", "Esther", "Job", "Psalm", "Proverbs",
        "Ecclesiastes", "Song of Solomon", "Isaiah", "Jeremiah",
        "Lamentations", "Ezekiel", "Daniel", "Hosea", "Joel", "Amos",
        "Obadiah", "Jonah", "Micah", "Nahum", "Habakkuk", "Zephaniah",
        "Haggai", "Zechariah", "Malachi", "Matthew", "Mark", "Luke",
        "John", "Acts", "Romans", "1 Corinthians", "2 Corinthians",
        "Galatians", "Ephesians", "Philippians", "Colossians",
        "1 Thessalonians", "2 Thessalonians", "1 Timothy", "2 Timothy",
        "Titus", "Philemon", "Hebrews", "James", "1 Peter", "2 Peter",
        "1 John", "2 John", "3 John", "Jude", "Revelation"
    ]
    bible_map = {book.lower(): i for i, book in enumerate(bible_order)}

    def normalize_for_sort(filename):
        name = os.path.splitext(filename)[0].replace("_", " ").replace("-", " ").lower()
        return bible_map.get(name, len(bible_order))  # Unknowns go to the end

    return sorted(books, key=normalize_for_sort)

def save_filenames_as_ts_array(exceptions=None):
    if exceptions is None:
        exceptions = ['.git', '.gitignore', 'names.py', 'names.ts', '.vscode', 'README.md']

    try:
        current_dir = os.getcwd()

        # Get and filter filenames
        filenames = [
            f for f in os.listdir(current_dir)
            if os.path.isfile(os.path.join(current_dir, f))
            and f not in exceptions
        ]

        # Sort biblically
        sorted_filenames = sort_biblical_order(filenames)

        # Format as TypeScript array
        quoted_names = [f'"{name}"' for name in sorted_filenames]
        ts_array_content = f'export const fileNames: string[] = [{", ".join(quoted_names)}];\n'

        # Write to names.ts
        output_file = os.path.join(current_dir, "names.ts")
        with open(output_file, "w", encoding="utf-8") as ts_file:
            ts_file.write(ts_array_content)

        print(f"Successfully saved {len(sorted_filenames)} file names to {output_file}.")

    except Exception as e:
        print(f"Error occurred: {str(e)}")

if __name__ == "__main__":
    save_filenames_as_ts_array()