from sqlalchemy import Column, Integer, String, Float, ForeignKey, Date, Boolean, UniqueConstraint
from sqlalchemy.orm import relationship
from core.database_models import Base
from datetime import datetime

class ProductionProduct(Base):
    """
    جدول الأصناف (Master Data)
    - مرجع ثابت للأوصاف والمقاسات
    - الوصف + المقاس = تعريف فريد للصنف
    """
    __tablename__ = 'production_products'
    
    id = Column(Integer, primary_key=True)
    description = Column(String(100), nullable=False) # وصف الصنف
    size = Column(String(50), nullable=False)        # المقاس
    category = Column(String(50), nullable=True)     # الفئة (شباب، بنات، طباعة...)
    
    __table_args__ = (
        UniqueConstraint('description', 'size', name='_prod_desc_size_uc'),
    )

    def __repr__(self):
        return f"<ProductionProduct {self.description} - {self.size}>"

class ProductionFactory(Base):
    """
    جدول المصانع / العملاء
    - يستخدم لربط القصص والدفعات المستقلة
    """
    __tablename__ = 'production_factories'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, unique=True) # اسم المصنع
    is_active = Column(Boolean, default=True)               # حالة التفعيل
    
    def __repr__(self):
        return f"<ProductionFactory {self.name}>"

class ProductionCut(Base):
    """
    جدول رأس القصة (الكيان الأساسي)
    - الرقم والتاريخ هما المرجع الأساسي
    - مرتبط بمصنع واحد
    """
    __tablename__ = 'production_cuts'
    
    id = Column(Integer, primary_key=True)
    cut_number = Column(String(50), unique=True, nullable=False) # رقم القصة
    date = Column(Date, default=datetime.now, nullable=False)     # تاريخ القص
    factory_id = Column(Integer, ForeignKey('production_factories.id'), nullable=True)
    
    factory = relationship('ProductionFactory', backref='cuts')
    details = relationship('ProductionCutDetail', backref='cut', cascade="all, delete-orphan")

    def __repr__(self):
        return f"<ProductionCut {self.cut_number}>"

class ProductionCutDetail(Base):
    """
    جدول محتويات القصة
    - يسجل الأصناف والمقاسات والكميات المرجعية لكل قصة
    """
    __tablename__ = 'production_cut_details'
    
    id = Column(Integer, primary_key=True)
    cut_id = Column(Integer, ForeignKey('production_cuts.id'), nullable=False)
    product_id = Column(Integer, ForeignKey('production_products.id'), nullable=False)
    
    # الكمية الأصلية الثابتة (مرجع للنظام)
    quantity = Column(Float, default=0.0, nullable=False)
    
    product = relationship('ProductionProduct')

    def __repr__(self):
        return f"<CutDetail {self.cut_id} - Product {self.product_id} - Qty {self.quantity}>"

class ProductionOperation(Base):
    """
    جدول حركة التشغيل
    - تتبع مراحل القصة (تشغيل، خياطة، استلام، تعبئة/تغليف)
    - تتبع زمني فقط بدون كميات
    """
    __tablename__ = 'production_operations'
    
    id = Column(Integer, primary_key=True)
    cut_id = Column(Integer, ForeignKey('production_cuts.id'), nullable=False)
    stage = Column(String(50), nullable=False) # المرحلة (تشغيل، خياطة، استلام، تعبئة/تغليف)
    date = Column(Date, default=datetime.now)  # تاريخ الحركة
    
    cut = relationship('ProductionCut', backref='operations')

class ProductionQualityControl(Base):
    """
    جدول العيوب والفاقد (تحليل مرحلة التعبئة)
    - تسجيل تحليلي للكميات بعد الخياطة وأثناء التعبئة
    """
    __tablename__ = 'production_quality_control'
    
    id = Column(Integer, primary_key=True)
    cut_id = Column(Integer, ForeignKey('production_cuts.id'), nullable=False)
    
    good_quantity = Column(Float, default=0.0)   # كمية سليمة
    defect_quantity = Column(Float, default=0.0) # كمية عيوب
    loss_quantity = Column(Float, default=0.0)   # كمية فاقد
    
    cut = relationship('ProductionCut', backref='qc_records')

class ProductionFactoryPayment(Base):
    """
    جدول دفعات تحت الحساب (مسمى السلف سابقاً)
    - دفعات مالية مستقلة تماماً للمصانع
    - لا توجد تسوية تلقائية أو ربط محاسبي
    """
    __tablename__ = 'production_factory_payments'
    
    id = Column(Integer, primary_key=True)
    factory_id = Column(Integer, ForeignKey('production_factories.id'), nullable=False)
    date = Column(Date, default=datetime.now) # تاريخ الدفعة
    amount = Column(Float, default=0.0)       # قيمة الدفعة
    notes = Column(String(255), nullable=True) # ملاحظات
    
    factory = relationship('ProductionFactory', backref='payments')
