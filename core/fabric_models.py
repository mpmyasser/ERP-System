from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Date, Boolean, Text
from sqlalchemy.orm import relationship
from core.database_models import Base
from datetime import datetime

class FabricDesign(Base):
    """
    سجل الرسومات (للطباعة)
    """
    __tablename__ = 'fabric_designs'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, unique=True)
    image_path = Column(String(255), nullable=True) # مسار الصورة التوضيحية
    notes = Column(Text, nullable=True)
    
    is_active = Column(Boolean, default=True)

class FabricRoll(Base):
    """
    سجل الأتواب (تتبع القماش الخام والمصبوغ والمطبوع)
    """
    __tablename__ = 'fabric_rolls'
    
    id = Column(Integer, primary_key=True)
    serial_number = Column(String(50), unique=True, nullable=False) # الباركود أو السيريال
    
    # الربط مع الشركاء والمستودعات
    supplier_id = Column(Integer, ForeignKey('partners.id'), nullable=True)
    warehouse_id = Column(Integer, ForeignKey('warehouses.id'), nullable=True)
    
    # نوع القماش والمواصفات
    fabric_type = Column(String(100), nullable=False)
    color = Column(String(50), nullable=True)
    design_id = Column(Integer, ForeignKey('fabric_designs.id'), nullable=True)
    
    # الأوزان والقياسات
    gross_weight = Column(Float, nullable=False) # الوزن القائم بالكيلو
    net_weight = Column(Float, nullable=True)    # الوزن الصافي (يحسب عند التصنيع فقط بخصم 450 جرام)
    meters = Column(Float, nullable=True)        # الأمتار (خاصة بعد الطباعة)
    
    # الحالة (خام، في المصبغة، مصبوغ، في المطبعة، مطبوع، تم القص، مباع)
    status = Column(String(50), default='Raw') 
    
    # ربط بالرسالة
    current_message_id = Column(Integer, ForeignKey('production_messages.id'), nullable=True)
    
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    supplier = relationship('Partner')
    warehouse = relationship('Warehouse')
    design = relationship('FabricDesign')
    message = relationship('ProductionMessage', foreign_keys=[current_message_id])
    
    def calculate_net_weight(self, number_of_rolls=1):
        """
        خصم وزن الكون والكيس (450 جرام لكل توب) للوصول للوزن الصافي عند التصنيع.
        """
        if self.gross_weight is not None:
            deduction = number_of_rolls * 0.450
            self.net_weight = max(0, self.gross_weight - deduction)
            return self.net_weight
        return 0.0

class ProductionMessage(Base):
    """
    رسالة الإنتاج (للمصبغة أو المطبعة)
    """
    __tablename__ = 'production_messages'
    
    id = Column(Integer, primary_key=True)
    message_number = Column(String(50), unique=True, nullable=False)
    type = Column(String(20), nullable=False) # Dyeing (صباغة), Printing (طباعة)
    
    partner_id = Column(Integer, ForeignKey('partners.id'), nullable=False) # المصبغة أو المطبعة
    date_sent = Column(Date, default=datetime.now)
    date_received = Column(Date, nullable=True)
    
    # الإجماليات (للمطابقة)
    total_weight_sent = Column(Float, default=0.0)
    total_weight_received = Column(Float, default=0.0)
    total_meters_received = Column(Float, default=0.0)
    
    # الفاقد
    loss_weight = Column(Float, default=0.0)
    loss_percentage = Column(Float, default=0.0)
    
    status = Column(String(20), default='Processing') # Processing, Completed, Cancelled
    
    # الربط المحاسبي (فاتورة الخدمة)
    invoice_id = Column(Integer, ForeignKey('invoices.id'), nullable=True)
    
    partner = relationship('Partner')
    invoice = relationship('Invoice')
    # Rolls are linked back to this message via FabricRoll.current_message_id
