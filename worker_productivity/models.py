"""
نموذج قاعدة بيانات تتبع إنتاج العمال
- يعمل على SQLite مستقل (worker_productivity.db)
- لا يرتبط بالمشروع الحالي
"""

from datetime import datetime, date
from sqlalchemy import (
    Column, Integer, String, Float, Date, DateTime, Time,
    ForeignKey, UniqueConstraint, Text, create_engine
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

Base = declarative_base()

# ---------- الجداول الرئيسية ----------

class Worker(Base):
    """بيانات العامل"""
    __tablename__ = 'workers'

    id = Column(Integer, primary_key=True)
    code = Column(String(20), unique=True, nullable=False, index=True)  # كود العامل
    name = Column(String(100), nullable=False)                          # اسم العامل
    hire_date = Column(Date, nullable=True)                             # تاريخ التعيين
    is_insured = Column(String(20), default='غير مؤمن')                # التأمين
    salary = Column(Float, default=0)                                   # المرتب
    is_active = Column(Integer, default=1)                              # نشط / غير نشط
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.now)

    records = relationship('ProductionRecord', back_populates='worker')

    def __repr__(self):
        return f"<Worker {self.code} - {self.name}>"


class Stage(Base):
    """مراحل الإنتاج"""
    __tablename__ = 'stages'

    id = Column(Integer, primary_key=True)
    code = Column(String(10), unique=True, nullable=False, index=True)  # رقم المرحلة
    name = Column(String(100), nullable=False)                          # اسم المرحلة
    machine_type = Column(String(50), nullable=True)                    # نوع الماكينة (اوفر، اورليه، سنجر)
    product_type = Column(String(50), nullable=True)                    # علوي / سفلي
    created_at = Column(DateTime, default=datetime.now)

    records = relationship('ProductionRecord', back_populates='stage')

    def __repr__(self):
        return f"<Stage {self.code} - {self.name}>"


class Product(Base):
    """الأصناف والمقاسات"""
    __tablename__ = 'products'

    id = Column(Integer, primary_key=True)
    code = Column(String(30), unique=True, nullable=False, index=True)  # كود الصنف
    name = Column(String(200), nullable=False)                          # اسم الصنف
    size = Column(String(20), nullable=False)                           # المقاس
    created_at = Column(DateTime, default=datetime.now)

    __table_args__ = (
        UniqueConstraint('code', 'size', name='_product_code_size_uc'),
    )

    records = relationship('ProductionRecord', back_populates='product')

    def __repr__(self):
        return f"<Product {self.code} - {self.name} - {self.size}>"


class ProductionRecord(Base):
    """
    جدول سجلات الإنتاج - البيانات الأساسية
    كل سجل = عملية واحدة لعامل واحد على صنف واحد في مرحلة واحدة
    """
    __tablename__ = 'production_records'

    id = Column(Integer, primary_key=True)
    record_date = Column(Date, nullable=False, index=True)              # التاريخ
    worker_code = Column(String(20), ForeignKey('workers.code'), nullable=False, index=True)
    stage_code = Column(String(10), ForeignKey('stages.code'), nullable=False, index=True)
    product_code = Column(String(30), ForeignKey('products.code'), nullable=False, index=True)

    time_from = Column(Time, nullable=False)                            # وقت البدء
    time_to = Column(Time, nullable=False)                              # وقت الانتهاء
    hours_worked = Column(Float, nullable=False)                        # عدد ساعات العمل (محسوب)
    quantity = Column(Float, nullable=False, default=0)                 # الكمية المنتجة
    machine_type = Column(String(50), nullable=True)                    # نوع الماكينة
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # العلاقات
    worker = relationship('Worker', back_populates='records')
    stage = relationship('Stage', back_populates='records')
    product = relationship('Product', back_populates='records')

    def __repr__(self):
        return (f"<Record {self.record_date} - {self.worker_code} - "
                f"Stage {self.stage_code} - Qty {self.quantity}>")


class Benchmark(Base):
    """
    جدول المعايير الإحصائية
    يحسب لكل مجموعة (مرحلة × صنف × مقاس) الإحصائيات
    """
    __tablename__ = 'benchmarks'

    id = Column(Integer, primary_key=True)
    stage_code = Column(String(10), ForeignKey('stages.code'), nullable=False, index=True)
    product_code = Column(String(30), ForeignKey('products.code'), nullable=False, index=True)

    # إحصائيات الوقت لكل وحدة (hours per unit)
    avg_hours_per_unit = Column(Float, nullable=True)      # المتوسط
    median_hours_per_unit = Column(Float, nullable=True)   # الوسيط
    min_hours_per_unit = Column(Float, nullable=True)      # الأسرع
    max_hours_per_unit = Column(Float, nullable=True)      # الأبطأ
    std_hours_per_unit = Column(Float, nullable=True)      # الانحراف المعياري
    p25_hours_per_unit = Column(Float, nullable=True)      # الربع الأول
    p75_hours_per_unit = Column(Float, nullable=True)      # الربع الثالث
    p90_hours_per_unit = Column(Float, nullable=True)      # 90% الأسرع

    record_count = Column(Integer, default=0)              # عدد السجلات المبنية عليها
    last_updated = Column(DateTime, default=datetime.now)

    stage = relationship('Stage')
    product = relationship('Product')

    __table_args__ = (
        UniqueConstraint('stage_code', 'product_code', name='_benchmark_key_uc'),
    )

    def __repr__(self):
        return (f"<Benchmark Stage {self.stage_code} - "
                f"Product {self.product_code} - Avg {self.avg_hours_per_unit}>")


# ---------- دوال قاعدة البيانات ----------

DB_PATH = 'worker_productivity.db'


def get_engine(db_path=None):
    """إنشاء engine قاعدة البيانات"""
    path = db_path or DB_PATH
    return create_engine(f'sqlite:///{path}', echo=False)


def init_db(engine=None):
    """إنشاء الجداول في قاعدة البيانات"""
    if engine is None:
        engine = get_engine()
    Base.metadata.create_all(engine)


def get_session(engine=None):
    """إنشاء session للتعامل مع قاعدة البيانات"""
    if engine is None:
        engine = get_engine()
    Session = sessionmaker(bind=engine)
    return Session()


def init_and_get_session(db_path=None):
    """تهيئة قاعدة البيانات وإرجاع session جاهز"""
    engine = get_engine(db_path)
    init_db(engine)
    return get_session(engine)