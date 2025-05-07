import json
import os
import re

def check_verse_content(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            book_data = json.load(f)
            
        book_filename = os.path.basename(file_path)
        book_name = book_filename.replace('.json', '')
        
        issues_found = False
        
        # Pattern to match: "filename digit:digit actual verse"
        pattern = rf"^{book_name}\s+\d+:\d+"
        
        for chapter, verses in book_data.items():
            for verse_num, verse_content in verses.items():
                if re.match(pattern, verse_content):
                    print(f"Issue found in {book_filename}")
                    print(f"Chapter {chapter}, Verse {verse_num}")
                    print(f"Content: {verse_content}")
                    print("-" * 50)
                    issues_found = True
                    
        if not issues_found:
            print(f"No issues found in {book_filename}")
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON format in {file_path}")
    except Exception as e:
        print(f"Error processing {file_path}: {str(e)}")

def main():
    # Walk through current directory
    for root, dirs, files in os.walk('.'):
        for file in files:
            if file.endswith('.json'):
                file_path = os.path.join(root, file)
                check_verse_content(file_path)

if __name__ == "__main__":
    main()