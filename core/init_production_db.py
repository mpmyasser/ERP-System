import os
import sys
# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy import create_engine
from core.database_models import Base
from core.production_models import (
    ProductionProduct,
    ProductionFactory,
    ProductionCut,
    ProductionCutDetail,
    ProductionOperation,
    ProductionQualityControl,
    ProductionFactoryPayment,
)

def init_db():
    db_path = os.path.join(os.path.dirname(__file__), 'production.db')
    engine = create_engine(f'sqlite:///{db_path}', echo=False)
    
    # قائمة الجداول المراد إنشاؤها فقط في هذه القاعدة
    tables_to_create = [
        ProductionProduct.__table__,
        ProductionFactory.__table__,
        ProductionCut.__table__,
        ProductionCutDetail.__table__,
        ProductionOperation.__table__,
        ProductionQualityControl.__table__,
        ProductionFactoryPayment.__table__,
    ]
    
    # إنشاء الجداول المحددة فقط
    for table in tables_to_create:
        table.create(bind=engine, checkfirst=True)
        
    print('تم إنشاء جداول الإنتاج بنجاح في', db_path)

if __name__ == '__main__':
    init_db()
