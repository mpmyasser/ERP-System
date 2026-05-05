from operation_app import _get_admin_password_file_path, create_app
from operation_storage import DB_PATH


app = create_app()


if __name__ == "__main__":
    print("=" * 72)
    print("حركة التشغيل - شاشة قسم القص")
    print(f"قاعدة البيانات: {DB_PATH}")
    print(f"ملف كلمة سر الأدمن: {_get_admin_password_file_path()}")
    print("URL: http://127.0.0.1:5100")
    print("=" * 72)
    app.run(debug=True, host="0.0.0.0", port=5100)
