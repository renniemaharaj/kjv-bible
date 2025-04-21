# KJV Bible JSON Repository

This repository contains the complete King James Version (KJV) of the Bible in JSON format, making it easily accessible for developers to use in their applications.

## Repository Contents

- JSON files containing the complete text of the King James Version Bible
- Python utility script for managing file names
- TypeScript integration support

## Python Utility Script

The repository includes a Python script that helps generate a TypeScript array of file names. This is particularly useful when you need to work with the Bible JSON files in a TypeScript environment.

### Script Functionality

The `save_filenames_as_ts_array()` function:
1. Reads all files in the current directory except omit array
2. Creates a TypeScript array containing all 66 books of the Bible
3. Saves the array books to a `names.ts` file

### Usage

```bash
python names.py
```

The script will:
- Scan the current directory for files
- Generate a `names.ts` file containing an array of all 66 Bible books in order from Genesis to Revelation

    ```typescript
    export const fileNames: string[] = ['Genesis.json', 'Exodus.json', ..., 'Revelation.json'];
    ```

## Contributing

Feel free to contribute by submitting pull requests or creating issues for any improvements or corrections.

## License

This repository is open source and available under the MIT License.

## Acknowledgments

- King James Version Bible text is in the public domain