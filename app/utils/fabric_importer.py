import pandas as pd
from core.fabric_models import FabricRoll, FabricDesign
from core.commercial_models import Partner, Warehouse
from typing import Tuple
import traceback

def import_fabric_rolls_from_excel(db_session, file_path: str) -> Tuple[bool, str]:
    """
    Imports Initial Fabric Rolls (الأرصدة الافتتاحية للأتواب) from an Excel file.
    Expected Columns:
    - serial_number (String)
    - fabric_type (String)
    - color (String, optional)
    - gross_weight (Float)
    - net_weight (Float, optional)
    - meters (Float, optional)
    - status (String: Raw, Dyed, Printed, Finished)
    - supplier_name (String, optional)
    - warehouse_name (String, optional)
    - design_name (String, optional)
    """
    try:
        df = pd.read_excel(file_path)
        
        required_cols = ['serial_number', 'fabric_type', 'gross_weight']
        for col in required_cols:
            if col not in df.columns:
                return False, f"العمود المطلوب غير موجود: {col}"
                
        existing_rolls = {r.serial_number: r for r in db_session.query(FabricRoll).all()}
        
        # Cache related entities to avoid repeated queries
        partners_cache = {p.name: p.id for p in db_session.query(Partner).all()}
        warehouses_cache = {w.name: w.id for w in db_session.query(Warehouse).all()}
        designs_cache = {d.name: d.id for d in db_session.query(FabricDesign).all()}
        
        for index, row in df.iterrows():
            serial = str(row['serial_number']).strip()
            if not serial or serial == 'nan':
                continue
                
            fabric_type = str(row['fabric_type']).strip()
            color = str(row.get('color', '')).strip()
            if color == 'nan': color = ''
            
            try:
                gross_weight = float(row['gross_weight'])
            except:
                gross_weight = 0.0
                
            try:
                net_weight = float(row['net_weight'])
            except:
                net_weight = None
                
            try:
                meters = float(row['meters'])
            except:
                meters = None
                
            status = str(row.get('status', 'Raw')).strip()
            if status == 'nan': status = 'Raw'
            
            supplier_name = str(row.get('supplier_name', '')).strip()
            warehouse_name = str(row.get('warehouse_name', '')).strip()
            design_name = str(row.get('design_name', '')).strip()
            
            supplier_id = partners_cache.get(supplier_name)
            warehouse_id = warehouses_cache.get(warehouse_name)
            design_id = designs_cache.get(design_name)
            
            # If design does not exist but was provided, we could create it on the fly
            if design_name and design_name != 'nan' and not design_id:
                new_design = FabricDesign(name=design_name)
                db_session.add(new_design)
                db_session.flush() # get ID
                design_id = new_design.id
                designs_cache[design_name] = design_id
            
            if serial in existing_rolls:
                roll = existing_rolls[serial]
                roll.fabric_type = fabric_type
                roll.color = color
                roll.gross_weight = gross_weight
                roll.net_weight = net_weight
                roll.meters = meters
                roll.status = status
                roll.supplier_id = supplier_id
                roll.warehouse_id = warehouse_id
                roll.design_id = design_id
            else:
                roll = FabricRoll(
                    serial_number=serial,
                    fabric_type=fabric_type,
                    color=color,
                    gross_weight=gross_weight,
                    net_weight=net_weight,
                    meters=meters,
                    status=status,
                    supplier_id=supplier_id,
                    warehouse_id=warehouse_id,
                    design_id=design_id
                )
                db_session.add(roll)
                
        db_session.commit()
        return True, "تم استيراد أرصدة الأتواب بنجاح"
        
    except Exception as e:
        db_session.rollback()
        error_msg = f"خطأ أثناء الاستيراد: {str(e)}\n{traceback.format_exc()}"
        print(error_msg)
        return False, str(e)
