
import sys
sys.path.insert(0, 'e:/backoup/25-2-2026')
import app.routes.operation_storage as s

try:
    # 1. Add a test factory
    s.add_factory("F1", "Test Factory")
    
    # 2. Add a test batch
    rows = [{"code": "A1", "name": "Item A", "size": "L", "quantity": "100"}]
    batch_code = s.save_cut_batch(rows, notes="", source="manual", cut_date="01/01/2026", message_no="MSG1")
    
    # 3. Get the item
    items = s.get_recent_cut_items(limit=10)
    item_id = items[0]["id"]
    
    # 4. Dispatch the item
    payload = {
        "id": item_id,
        "cut_date": "01/01/2026",
        "message_no": "MSG1",
        "code": "A1",
        "name": "Item A",
        "size": "L",
        "quantity": "100",
        "description": "",
        "factory_code": "F1",
        "factory_name": "Test Factory",
        "manufacturing_price": "50",
        "dispatch_date": "02/01/2026"
    }
    
    updated = s.update_cut_item_dispatch(
        item_id=payload.get("id"),
        cut_date=payload.get("cut_date"),
        message_no=payload.get("message_no"),
        code=payload.get("code"),
        name=payload.get("name"),
        size=payload.get("size"),
        quantity=payload.get("quantity"),
        factory_code=payload.get("factory_code"),
        factory_name=payload.get("factory_name"),
        manufacturing_price=payload.get("manufacturing_price"),
        dispatch_date=payload.get("dispatch_date"),
        description=payload.get("description"),
    )
    
    print("SUCCESS:", updated)
except Exception as e:
    import traceback
    traceback.print_exc()
