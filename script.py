import json
import os
import re
import argparse

def count_verses(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            book_data = json.load(f)
            
        book_filename = os.path.basename(file_path)
        book_name = book_filename.replace('.json', '')
        
        verse_count = sum(len(verses) for verses in book_data.values())
        print(f"{book_name}: {verse_count} verses")
        return verse_count
    except Exception as e:
        print(f"Error processing {file_path}: {str(e)}")
        return 0

def check_verse_content(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            book_data = json.load(f)
            
        book_filename = os.path.basename(file_path)
        book_name = book_filename.replace('.json', '')
        
        issues_found = False
        pattern = rf"^\d*{book_name}\s+\d+:\d+"
        
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
    except Exception as e:
        print(f"Error processing {file_path}: {str(e)}")

def main():
    parser = argparse.ArgumentParser(description='Bible verse processor')
    parser.add_argument('command', choices=['check', 'count'],
                      help='Command to execute (check: scan for malformed verses, count: count verses)')
    args = parser.parse_args()

    total_verses = 0
    for root, dirs, files in os.walk('.'):
        for file in files:
            if file.endswith('.json'):
                file_path = os.path.join(root, file)
                if args.command == 'check':
                    check_verse_content(file_path)
                else:  # count
                    total_verses += count_verses(file_path)
    
    if args.command == 'count':
        print(f"\nTotal verses across all books: {total_verses}")

if __name__ == "__main__":
    main()