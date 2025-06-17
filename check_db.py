
import sqlite3
import os

DB_FILENAME = 'app.db'
TABLE_TO_CHECK = 'course'
COLUMN_TO_FIND = 'term_id'


db_path = os.path.join(os.path.dirname(__file__), DB_FILENAME)

if not os.path.exists(db_path):
    print(f"خطا: فایل پایگاه داده در مسیر '{db_path}' پیدا نشد.")
    print("لطفاً مطمئن شوید که دستور 'flask db upgrade' را با موفقیت اجرا کرده‌اید.")
else:
    print(f"درحال بررسی ساختار جدول '{TABLE_TO_CHECK}' در فایل: {db_path}\n")
    try:

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()


        cursor.execute(f"PRAGMA table_info({TABLE_TO_CHECK});")
        columns = cursor.fetchall()

        if not columns:
            print(f"جدول '{TABLE_TO_CHECK}' در پایگاه داده وجود ندارد.")
        else:
            print(f"ستون‌های پیدا شده در جدول '{TABLE_TO_CHECK}':")
            print("-" * 40)
            found_term_id = False

            for col in columns:

                col_name = col[1]
                col_type = col[2]
                print(f"- ستون: {col_name:<15} | نوع: {col_type}")
                if col_name == COLUMN_TO_FIND:
                    found_term_id = True
            print("-" * 40)


            if found_term_id:
                print(f"\n✅ موفقیت: ستون '{COLUMN_TO_FIND}' در جدول وجود دارد!")
            else:
                print(f"\n❌ خطا: ستون '{COLUMN_TO_FIND}' در جدول پیدا نشد!")

    except Exception as e:
        print(f"یک خطای غیرمنتظره رخ داد: {e}")
    finally:
        # بستن اتصال
        if 'conn' in locals() and conn:
            conn.close()