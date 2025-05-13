#!/usr/bin/env python3

import argparse
import os
import re
import sys
import shutil
import time
from datetime import datetime
from pathlib import Path
import json
import random
import string


class BulkFileRenamer:
    def __init__(self, options=None):
        self.options = options or {}
        self.log_file = self.options.get('log_file', 'rename_log.json')
        self.preview_mode = self.options.get('preview', False)
        self.backup_folder = self.options.get('backup_folder', '.rename_backup')
        self.use_backup = self.options.get('create_backup', False)
        self.verbose = self.options.get('verbose', False)
        
        # For renaming history
        self.rename_history = []
        
        # For rollback
        self.last_operation = []
        
        # Count for {count} pattern
        self.count = 1
        
        # Patterns for smart renaming
        self.date_formats = {
            'YYYY': lambda f: datetime.fromtimestamp(os.path.getmtime(f)).strftime('%Y'),
            'MM': lambda f: datetime.fromtimestamp(os.path.getmtime(f)).strftime('%m'),
            'DD': lambda f: datetime.fromtimestamp(os.path.getmtime(f)).strftime('%d'),
            'hh': lambda f: datetime.fromtimestamp(os.path.getmtime(f)).strftime('%H'),
            'mm': lambda f: datetime.fromtimestamp(os.path.getmtime(f)).strftime('%M'),
            'ss': lambda f: datetime.fromtimestamp(os.path.getmtime(f)).strftime('%S'),
            'date': lambda f: datetime.fromtimestamp(os.path.getmtime(f)).strftime('%Y-%m-%d'),
            'time': lambda f: datetime.fromtimestamp(os.path.getmtime(f)).strftime('%H-%M-%S'),
            'datetime': lambda f: datetime.fromtimestamp(os.path.getmtime(f)).strftime('%Y-%m-%d_%H-%M-%S'),
        }
        
        self.special_patterns = {
            'count': lambda f, p: str(self.count).zfill(p),
            'random': lambda f, p: ''.join(random.choices(string.ascii_letters + string.digits, k=int(p) if p.isdigit() else 5)),
            'ext': lambda f, p: os.path.splitext(f)[1][1:],
            'origname': lambda f, p: os.path.splitext(os.path.basename(f))[0]
        }
    
    def create_backup(self, files):
        """Create backup of files before renaming"""
        if not self.use_backup:
            return True
        
        if not os.path.exists(self.backup_folder):
            os.makedirs(self.backup_folder)
        
        # Timestamp for this backup session
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        session_folder = os.path.join(self.backup_folder, f"backup_{timestamp}")
        os.makedirs(session_folder)
        
        try:
            # Copy files to backup
            for file_path in files:
                if os.path.exists(file_path):
                    filename = os.path.basename(file_path)
                    dest_path = os.path.join(session_folder, filename)
                    shutil.copy2(file_path, dest_path)
                    if self.verbose:
                        print(f"Backed up: {file_path} -> {dest_path}")
            
            # Save operation metadata
            meta_file = os.path.join(session_folder, "metadata.json")
            meta_data = {
                "timestamp": timestamp,
                "files": [os.path.abspath(f) for f in files],
                "options": self.options
            }
            
            with open(meta_file, 'w', encoding='utf-8') as f:
                json.dump(meta_data, f, indent=2)
            
            return True
        except Exception as e:
            print(f"Error creating backup: {str(e)}")
            return False
    
    def log_operation(self, old_path, new_path):
        """Log rename operation to history"""
        self.rename_history.append({
            "old_path": old_path,
            "new_path": new_path,
            "timestamp": time.time()
        })
        
        self.last_operation.append({
            "old_path": old_path,
            "new_path": new_path
        })
        
        # Save to log file
        if self.log_file:
            try:
                log_data = []
                if os.path.exists(self.log_file):
                    with open(self.log_file, 'r', encoding='utf-8') as f:
                        log_data = json.load(f)
                
                log_data.append({
                    "old_path": old_path,
                    "new_path": new_path,
                    "timestamp": time.time(),
                    "date": time.strftime("%Y-%m-%d %H:%M:%S")
                })
                
                with open(self.log_file, 'w', encoding='utf-8') as f:
                    json.dump(log_data, f, indent=2)
            except Exception as e:
                if self.verbose:
                    print(f"Error logging operation: {str(e)}")
    
    def rollback_last_operation(self):
        """Rollback the last rename operation"""
        if not self.last_operation:
            print("Nothing to rollback.")
            return False
        
        success = True
        operations = list(reversed(self.last_operation))
        
        for op in operations:
            old_path = op["old_path"]
            new_path = op["new_path"]
            
            try:
                if os.path.exists(new_path):
                    if self.preview_mode:
                        print(f"Would rollback: {new_path} -> {old_path}")
                    else:
                        os.rename(new_path, old_path)
                        print(f"Rolled back: {new_path} -> {old_path}")
                else:
                    print(f"Warning: Can't rollback {new_path} (file doesn't exist)")
                    success = False
            except Exception as e:
                print(f"Error rolling back {new_path}: {str(e)}")
                success = False
        
        if success and not self.preview_mode:
            self.last_operation = []
        
        return success
    
    def replace_special_patterns(self, pattern, file_path):
        """Replace special patterns in the new filename format"""
        # First replace date patterns
        for key, func in self.date_formats.items():
            if f'{{{key}}}' in pattern:
                pattern = pattern.replace(f'{{{key}}}', func(file_path))
        
        # Then replace special patterns with parameters
        # Format: {pattern:parameter}
        special_pattern_regex = r'\{([^:}]+)(?::([^}]+))?\}'
        
        def replace_match(match):
            pattern_name = match.group(1)
            parameter = match.group(2) or ""
            
            if pattern_name in self.special_patterns:
                return self.special_patterns[pattern_name](file_path, parameter)
            return match.group(0)
        
        return re.sub(special_pattern_regex, replace_match, pattern)
    
    def rename_files(self, files, pattern, find=None, replace=None, regex=False, case_sensitive=True):
        """Rename files based on pattern and replacement"""
        if not files:
            print("No files to rename.")
            return False
        
        # Create backup if enabled
        if self.use_backup:
            self.create_backup(files)
        
        # Clear last operations list
        self.last_operation = []
        
        # Reset counter
        self.count = 1
        
        # Process each file
        renamed_count = 0
        
        for file_path in files:
            if not os.path.exists(file_path):
                print(f"Warning: {file_path} doesn't exist, skipping.")
                continue
            
            # Get directory, original filename and extension
            file_dir = os.path.dirname(file_path) or '.'
            filename = os.path.basename(file_path)
            
            # Different renaming strategies
            if pattern and (find is None) and (replace is None):
                # Direct pattern replacement
                new_filename = self.replace_special_patterns(pattern, file_path)
                
                # Make sure filename is valid
                new_filename = self.sanitize_filename(new_filename)
            
            elif find is not None and replace is not None:
                # Find and replace in filename
                if regex:
                    flags = 0 if case_sensitive else re.IGNORECASE
                    new_filename = re.sub(find, replace, filename, flags=flags)
                else:
                    if not case_sensitive:
                        new_filename = filename.replace(find.lower(), replace)
                    else:
                        new_filename = filename.replace(find, replace)
            
            else:
                print("Error: Invalid renaming options.")
                return False
            
            # Check if new filename is different
            if new_filename == filename:
                if self.verbose:
                    print(f"Skipping {filename} (no change)")
                continue
            
            # Create new path
            new_path = os.path.join(file_dir, new_filename)
            
            # Check if destination exists
            if os.path.exists(new_path) and new_path != file_path:
                print(f"Error: Can't rename to {new_filename} (already exists)")
                continue
            
            # Rename file
            if self.preview_mode:
                print(f"Would rename: {filename} -> {new_filename}")
            else:
                try:
                    os.rename(file_path, new_path)
                    self.log_operation(file_path, new_path)
                    print(f"Renamed: {filename} -> {new_filename}")
                    renamed_count += 1
                except Exception as e:
                    print(f"Error renaming {filename}: {str(e)}")
            
            # Increment counter for next file
            self.count += 1
        
        print(f"\n{'Preview of ' if self.preview_mode else ''}Renamed {renamed_count} file(s).")
        return renamed_count > 0
    
    def get_files_from_patterns(self, patterns, recursive=False):
        """Get files matching glob patterns"""
        all_files = []
        
        for pattern in patterns:
            if recursive:
                for root, _, files in os.walk('.'):
                    for file in files:
                        file_path = os.path.join(root, file)
                        if self.match_pattern(file_path, pattern):
                            all_files.append(file_path)
            else:
                import fnmatch
                for file in os.listdir('.'):
                    if os.path.isfile(file) and fnmatch.fnmatch(file, pattern):
                        all_files.append(file)
        
        return sorted(list(set(all_files)))
    
    def match_pattern(self, filename, pattern):
        """Check if filename matches the pattern"""
        import fnmatch
        return fnmatch.fnmatch(filename, pattern)
    
    def sanitize_filename(self, filename):
        """Make sure filename is valid"""
        # Remove invalid characters
        invalid_chars = ['<', '>', ':', '"', '/', '\\', '|', '?', '*']
        for char in invalid_chars:
            filename = filename.replace(char, '_')
        
        # Handle special cases
        if filename in ('.', '..'):
            filename = '_' + filename
        
        # Ensure filename isn't empty
        if not filename:
            filename = 'unnamed'
        
        return filename
    
    def show_history(self, limit=None):
        """Show rename operation history"""
        if not os.path.exists(self.log_file):
            print("No history found.")
            return
        
        try:
            with open(self.log_file, 'r', encoding='utf-8') as f:
                log_data = json.load(f)
            
            if limit:
                log_data = log_data[-limit:]
            
            print(f"\nRename History (Last {len(log_data)} operations):\n")
            print(f"{'Date':<20} {'Original Name':<30} {'New Name':<30}")
            print("-" * 80)
            
            for entry in log_data:
                date = entry.get('date', 'Unknown')
                old_name = os.path.basename(entry.get('old_path', 'Unknown'))
                new_name = os.path.basename(entry.get('new_path', 'Unknown'))
                
                print(f"{date:<20} {old_name:<30} {new_name:<30}")
            
            print()
        except Exception as e:
            print(f"Error reading history: {str(e)}")
    
    def clear_history(self):
        """Clear rename operation history"""
        if os.path.exists(self.log_file):
            try:
                os.remove(self.log_file)
                print("History cleared.")
                return True
            except Exception as e:
                print(f"Error clearing history: {str(e)}")
                return False
        else:
            print("No history to clear.")
            return False


def parse_arguments():
    parser = argparse.ArgumentParser(description='Bulk File Renamer - Rename files in bulk using patterns')
    
    # File selection options
    file_group = parser.add_argument_group('File Selection')
    file_group.add_argument('-f', '--files', nargs='+', help='Specific files to rename')
    file_group.add_argument('-p', '--pattern', nargs='+', help='File patterns to match (e.g. *.jpg)')
    file_group.add_argument('-r', '--recursive', action='store_true', help='Search files recursively')
    
    # Renaming options
    rename_group = parser.add_argument_group('Renaming Options')
    rename_group.add_argument('-n', '--name', help='New filename pattern (use {count} for numbering, {date} for date, etc.)')
    rename_group.add_argument('--find', help='String to find in filenames')
    rename_group.add_argument('--replace', help='String to replace with')
    rename_group.add_argument('--regex', action='store_true', help='Use regex for find/replace')
    rename_group.add_argument('-i', '--case-insensitive', action='store_true', help='Case insensitive find/replace')
    
    # Operation options
    op_group = parser.add_argument_group('Operation Options')
    op_group.add_argument('--preview', action='store_true', help='Preview changes without renaming')
    op_group.add_argument('--backup', action='store_true', help='Create backup of files before renaming')
    op_group.add_argument('--backup-dir', help='Custom backup directory')
    op_group.add_argument('--log', help='Custom log file path')
    op_group.add_argument('--rollback', action='store_true', help='Rollback the last rename operation')
    op_group.add_argument('--history', action='store_true', help='Show rename history')
    op_group.add_argument('--clear-history', action='store_true', help='Clear rename history')
    op_group.add_argument('--history-limit', type=int, help='Limit history display to N entries')
    op_group.add_argument('-v', '--verbose', action='store_true', help='Verbose output')
    
    # Help options
    help_group = parser.add_argument_group('Help Options')
    help_group.add_argument('--patterns', action='store_true', help='Show available special patterns')
    help_group.add_argument('--examples', action='store_true', help='Show usage examples')
    help_group.add_argument('--version', action='version', version='Bulk File Renamer v1.0.0')
    
    return parser.parse_args()


def show_patterns():
    """Show available special patterns"""
    print("\nSpecial Patterns for Filename Template:\n")
    
    print("Date/Time Patterns:")
    print("  {YYYY}     - Year (e.g. 2024)")
    print("  {MM}       - Month (01-12)")
    print("  {DD}       - Day (01-31)")
    print("  {hh}       - Hour (00-23)")
    print("  {mm}       - Minute (00-59)")
    print("  {ss}       - Second (00-59)")
    print("  {date}     - Date in YYYY-MM-DD format")
    print("  {time}     - Time in HH-MM-SS format")
    print("  {datetime} - Full timestamp (YYYY-MM-DD_HH-MM-SS)")
    
    print("\nSpecial Value Patterns:")
    print("  {count}           - Incremental counter (1, 2, 3...)")
    print("  {count:3}         - Zero-padded counter (001, 002, 003...)")
    print("  {random}          - 5 random alphanumeric characters")
    print("  {random:10}       - 10 random alphanumeric characters")
    print("  {ext}             - Original file extension")
    print("  {origname}        - Original filename without extension")
    
    print("\nExample Pattern:")
    print("  photo_{date}_{count:3}.{ext}")
    print("  Result: photo_2024-01-01_001.jpg, photo_2024-01-01_002.png, etc.")
    print()


def show_examples():
    """Show usage examples"""
    print("\nBulk File Renamer - Usage Examples:\n")
    
    print("1. Rename all JPG files to a numbered sequence:")
    print("   python main.py -p \"*.jpg\" -n \"photo_{count:3}.jpg\"")
    
    print("\n2. Add date prefix to text files:")
    print("   python main.py -p \"*.txt\" -n \"{date}_{origname}.{ext}\"")
    
    print("\n3. Replace spaces with underscores in all files:")
    print("   python main.py -p \"*\" --find \" \" --replace \"_\"")
    
    print("\n4. Use regex to remove numbers from filenames:")
    print("   python main.py -p \"*\" --find \"[0-9]+\" --replace \"\" --regex")
    
    print("\n5. Recursively rename all PNG files in subfolders:")
    print("   python main.py -p \"*.png\" -r -n \"image_{count:4}.png\"")
    
    print("\n6. Preview changes without renaming:")
    print("   python main.py -p \"*.jpg\" -n \"new_{origname}.jpg\" --preview")
    
    print("\n7. Create backup before renaming:")
    print("   python main.py -f \"file1.txt\" \"file2.txt\" -n \"{datetime}_{origname}.{ext}\" --backup")
    
    print("\n8. Rollback the last rename operation:")
    print("   python main.py --rollback")
    
    print("\n9. View rename history:")
    print("   python main.py --history")
    
    print("\n10. Find and replace with case-insensitive matching:")
    print("   python main.py -p \"*.txt\" --find \"test\" --replace \"sample\" -i")
    
    print()


def main():
    args = parse_arguments()
    
    # Show help info if requested
    if args.patterns:
        show_patterns()
        return
    
    if args.examples:
        show_examples()
        return
    
    # Setup options
    options = {
        'preview': args.preview,
        'create_backup': args.backup,
        'backup_folder': args.backup_dir or '.rename_backup',
        'log_file': args.log or 'rename_log.json',
        'verbose': args.verbose
    }
    
    renamer = BulkFileRenamer(options)
    
    # Handle history operations
    if args.history:
        renamer.show_history(args.history_limit)
        return
    
    if args.clear_history:
        renamer.clear_history()
        return
    
    # Handle rollback
    if args.rollback:
        renamer.rollback_last_operation()
        return
    
    # Get files to rename
    files = []
    if args.files:
        files = [f for f in args.files if os.path.exists(f)]
    elif args.pattern:
        files = renamer.get_files_from_patterns(args.pattern, args.recursive)
    
    if not files:
        print("No files found to rename.")
        return
    
    if args.verbose:
        print(f"Found {len(files)} files to process.")
    
    # Rename files
    renamer.rename_files(
        files,
        args.name,
        args.find,
        args.replace,
        args.regex,
        not args.case_insensitive
    )


if __name__ == "__main__":
    main()
