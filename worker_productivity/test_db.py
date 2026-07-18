"""اختبار إنشاء قاعدة البيانات والتأكد من عمل الموديلات"""
import os
import sys
sys.path.insert(0, os.path.dirname(__file__))
from models import init_and_get_session

session = init_and_get_session()
print("✅ DB created OK")
session.close()