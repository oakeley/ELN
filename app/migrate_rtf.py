"""
standalone_migrate_rtf.py - Add RTF support to the database
A standalone script that directly modifies the database without importing the application
"""

import os
import sqlite3
import sys

def add_rtf_columns(db_path):
    """Add RTF columns to the database tables using direct SQLite connection"""
    print(f"Adding RTF support to database: {db_path}")
    
    if not os.path.exists(db_path):
        print(f"Error: Database file not found at {db_path}")
        return False
    
    try:
        # Connect to the database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if columns already exist in file table
        cursor.execute("PRAGMA table_info(file)")
        file_columns = [column[1] for column in cursor.fetchall()]
        
        # Check if columns already exist in file_version table
        cursor.execute("PRAGMA table_info(file_version)")
        file_version_columns = [column[1] for column in cursor.fetchall()]
        
        # Add rtf_content column to file table if it doesn't exist
        if 'rtf_content' not in file_columns:
            print("Adding rtf_content column to file table...")
            cursor.execute('ALTER TABLE file ADD COLUMN rtf_content TEXT')
            print("Done.")
        else:
            print("rtf_content column already exists in file table.")
        
        # Add rtf_content column to file_version table if it doesn't exist
        if 'rtf_content' not in file_version_columns:
            print("Adding rtf_content column to file_version table...")
            cursor.execute('ALTER TABLE file_version ADD COLUMN rtf_content TEXT')
            print("Done.")
        else:
            print("rtf_content column already exists in file_version table.")
        
        # Commit changes and close
        conn.commit()
        conn.close()
        
        print("Database migration completed successfully.")
        return True
        
    except Exception as e:
        print(f"Error during migration: {str(e)}")
        return False

if __name__ == "__main__":
    # Try to locate the database file
    possible_db_paths = [
        # Common locations relative to the script
        os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "app.db"),
        os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "instance", "app.db"),
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "app.db"),
        "app.db"  # Current directory
    ]
    
    # Check for command line argument for the database path
    if len(sys.argv) > 1:
        db_path = sys.argv[1]
        if os.path.exists(db_path):
            add_rtf_columns(db_path)
        else:
            print(f"Error: Specified database file not found at {db_path}")
            print("Usage: python standalone_migrate_rtf.py [path_to_database]")
            sys.exit(1)
    else:
        # Try to find database automatically
        db_found = False
        for path in possible_db_paths:
            if os.path.exists(path):
                print(f"Found database at: {path}")
                if add_rtf_columns(path):
                    db_found = True
                break
        
        if not db_found:
            print("Error: Could not locate the database file automatically.")
            print("Please specify the database path as a command-line argument:")
            print("Usage: python standalone_migrate_rtf.py [path_to_database]")
            print("\nPossible locations checked:")
            for path in possible_db_paths:
                print(f" - {path}")
            sys.exit(1)
