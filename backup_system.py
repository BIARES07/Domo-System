import shutil
import os
from datetime import datetime

def backup_db():
    db_path = "domo_metrics.db"
    backup_dir = "backups"
    
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)
        
    if os.path.exists(db_path):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = os.path.join(backup_dir, f"domo_metrics_{timestamp}.db.bak")
        shutil.copy2(db_path, backup_path)
        print(f"[BACKUP] Base de datos respaldada en: {backup_path}")
    else:
        print("[BACKUP] No se encontró la base de datos para respaldar.")

if __name__ == "__main__":
    backup_db()
