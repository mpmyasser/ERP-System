from core.db_manager import DBManager
from sqlalchemy import text

def update_schema():
    db = DBManager()
    session = db.get_session()
    
    print("Updating Products schema...")
    
    try:
        # Check and add columns to products table
        columns = [
            ('unit', "TEXT DEFAULT 'Piece'"),
            ('structure_type', "TEXT DEFAULT 'Single'"),
            ('size', "TEXT"),
            ('image_path', "TEXT"),
            ('parent_id', "INTEGER REFERENCES products(id)")
        ]
        
        for col_name, col_def in columns:
            try:
                session.execute(text(f"ALTER TABLE products ADD COLUMN {col_name} {col_def}"))
                print(f"Added column {col_name} to products")
            except Exception as e:
                # Column likely exists
                print(f"Column {col_name} might already exist or error: {e}")
                
        session.commit()
        print("Schema update completed successfully.")
        
    except Exception as e:
        session.rollback()
        print(f"Error updating schema: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    update_schema()
