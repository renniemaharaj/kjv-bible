import json
import os
import re
import argparse
import hashlib

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

def calculate_hash(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            book_data = json.load(f)
        
        # Create a string of all verses in order
        verses_string = ""
        for chapter in sorted(book_data.keys(), key=int):
            for verse_num in sorted(book_data[chapter].keys(), key=int):
                verses_string += book_data[chapter][verse_num]
        
        # Calculate SHA-512 hash
        hash_obj = hashlib.sha512(verses_string.encode('utf-8'))
        return hash_obj.hexdigest()
    except Exception as e:
        print(f"Error processing {file_path}: {str(e)}")
        return None

def main():
    parser = argparse.ArgumentParser(description='Bible verse processor')
    parser.add_argument('command', choices=['check', 'count', 'hash'],
                      help='Command to execute (check: scan for malformed verses, count: count verses, hash: calculate verses hash)')
    args = parser.parse_args()

    total_verses = 0
    combined_hash = hashlib.sha512()

    for root, dirs, files in os.walk('.'):
        for file in files:
            if file.endswith('.json'):
                file_path = os.path.join(root, file)
                if args.command == 'check':
                    check_verse_content(file_path)
                elif args.command == 'count':
                    total_verses += count_verses(file_path)
                elif args.command == 'hash':
                    file_hash = calculate_hash(file_path)
                    if file_hash:
                        book_name = os.path.basename(file_path).replace('.json', '')
                        print(f"{book_name}: {file_hash}")
                        combined_hash.update(file_hash.encode('utf-8'))
    
    if args.command == 'count':
        print(f"\nTotal verses across all books: {total_verses}")
    elif args.command == 'hash':
        print(f"\nCombined hash of all books: {combined_hash.hexdigest()}")

if __name__ == "__main__":
    main()