from sqlalchemy import Column, Integer, String, Float, ForeignKey, Date, Boolean, Text
from sqlalchemy.orm import relationship
from core.database_models import Base
from datetime import datetime

class Warehouse(Base):
    """
    المخازن (خام، إكسسوار، منتج تام، أدوات مكتبية)
    """
    __tablename__ = 'warehouses'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, unique=True)
    type = Column(String(50), nullable=False) # Raw, Accessory, Finished, General
    location = Column(String(200), nullable=True)
    is_active = Column(Boolean, default=True)

class Product(Base):
    """
    الأصناف (للمبيعات والمشتريات العادية غير التشغيل)
    """
    __tablename__ = 'products'
    
    id = Column(Integer, primary_key=True)
    code = Column(String(50), unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    category = Column(String(50), nullable=True)
    
    # وحدة القياس (كجم، متر، قطعة)
    unit = Column(String(20), default='Piece')
    
    # الأسعار
    cost_price = Column(Float, default=0.0)
    sale_price = Column(Float, default=0.0)
    
    # الرصيد الحالي (يمكن حسابه لاحقاً من الحركات)
    current_stock = Column(Float, default=0.0)
    
    is_active = Column(Boolean, default=True)

class InventoryTransaction(Base):
    """
    سجل حركات المخازن الموحد
    """
    __tablename__ = 'inventory_transactions'
    
    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False)
    warehouse_id = Column(Integer, ForeignKey('warehouses.id'), nullable=False)
    
    transaction_type = Column(String(20), nullable=False) # In, Out
    quantity = Column(Float, nullable=False)
    unit_cost = Column(Float, default=0.0)
    
    reference = Column(String(100), nullable=True) # Invoice number, Operation Cut ID, etc.
    date = Column(Date, default=datetime.now)
    
    product = relationship('Product')
    warehouse = relationship('Warehouse')

class Partner(Base):
    """
    الشركاء (عملاء وموردين)
    """
    __tablename__ = 'partners'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    type = Column(String(20), nullable=False) # Customer, Supplier, Both, Factory
    
    phone = Column(String(20), nullable=True)
    address = Column(String(200), nullable=True)
    tax_id = Column(String(50), nullable=True) # الرقم الضريبي
    
    # الربط بالمحاسبة
    account_id = Column(Integer, ForeignKey('accounts.id'), nullable=True)
    
    is_active = Column(Boolean, default=True)
    
    account = relationship('Account')

class Invoice(Base):
    """
    الفواتير (مبيعات ومشتريات)
    """
    __tablename__ = 'invoices'
    
    id = Column(Integer, primary_key=True)
    type = Column(String(20), nullable=False) # Sales, Purchase, SalesReturn, PurchaseReturn
    invoice_number = Column(String(50), unique=True, nullable=False)
    date = Column(Date, default=datetime.now)
    
    partner_id = Column(Integer, ForeignKey('partners.id'), nullable=False)
    warehouse_id = Column(Integer, ForeignKey('warehouses.id'), nullable=True)
    
    total_amount = Column(Float, default=0.0)
    tax_amount = Column(Float, default=0.0)
    discount_amount = Column(Float, default=0.0)
    net_amount = Column(Float, default=0.0)
    
    status = Column(String(20), default='Draft') # Draft, Posted, Cancelled
    payment_status = Column(String(20), default='Unpaid') # Unpaid, Partial, Paid
    
    notes = Column(Text, nullable=True)
    
    # الربط بالمحاسبة
    journal_entry_id = Column(Integer, ForeignKey('journal_entries.id'), nullable=True)
    
    partner = relationship('Partner')
    warehouse = relationship('Warehouse')
    items = relationship('InvoiceItem', back_populates='invoice', cascade="all, delete-orphan")

class InvoiceItem(Base):
    """
    تفاصيل الفاتورة
    """
    __tablename__ = 'invoice_items'
    
    id = Column(Integer, primary_key=True)
    invoice_id = Column(Integer, ForeignKey('invoices.id'), nullable=False)
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False)
    
    quantity = Column(Float, nullable=False)
    unit_price = Column(Float, nullable=False)
    total = Column(Float, nullable=False)
    
    invoice = relationship('Invoice', back_populates='items')
    product = relationship('Product')
