from core.fabric_models import FabricRoll, FabricDesign
from core.commercial_models import Partner, Warehouse
from typing import Tuple
from app.utils.import_helpers import load_excel, clean_str, safe_float, handle_import_error

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
        df, error = load_excel(file_path, ['serial_number', 'fabric_type', 'gross_weight'])
        if error:
            return False, error
        assert df is not None

        existing_rolls = {r.serial_number: r for r in db_session.query(FabricRoll).all()}
        
        # Cache related entities to avoid repeated queries
        partners_cache = {p.name: p.id for p in db_session.query(Partner).all()}
        warehouses_cache = {w.name: w.id for w in db_session.query(Warehouse).all()}
        designs_cache = {d.name: d.id for d in db_session.query(FabricDesign).all()}
        
        for index, row in df.iterrows():
            serial = clean_str(row['serial_number'])
            if not serial:
                continue
                
            fabric_type = clean_str(row['fabric_type'])
            color = clean_str(row.get('color', ''))
            
            gross_weight = safe_float(row.get('gross_weight'), 0.0)
            net_weight = safe_float(row.get('net_weight'))
            meters = safe_float(row.get('meters'))
                
            status = clean_str(row.get('status', 'Raw'), 'Raw')
            
            supplier_name = clean_str(row.get('supplier_name', ''))
            warehouse_name = clean_str(row.get('warehouse_name', ''))
            design_name = clean_str(row.get('design_name', ''))
            
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
        return False, handle_import_error(db_session, e)
