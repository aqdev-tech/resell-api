import sqlite3

def fix_missing_admin_data():
    """Sets default values for role and is_active on admins where it's NULL."""
    conn = sqlite3.connect("reselling.db")
    cursor = conn.cursor()
    
    try:
        print("Updating admin accounts with missing data...")
        
        # Set default role for admins with a NULL role
        cursor.execute("UPDATE admins SET role = 'ADMIN' WHERE role IS NULL")
        role_updated_count = cursor.rowcount
        
        # Set default active status for admins with a NULL is_active status
        cursor.execute("UPDATE admins SET is_active = 1 WHERE is_active IS NULL")
        active_updated_count = cursor.rowcount
        
        conn.commit()
        
        if role_updated_count > 0 or active_updated_count > 0:
            print(f"Successfully updated {role_updated_count} role(s) and {active_updated_count} active status(es).")
        else:
            print("No admin accounts needed updating.")

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    fix_missing_admin_data()
