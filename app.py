# استيراد المكتبات اللازمة
import os
import sqlite3
import json
from flask import Flask, render_template, request, jsonify

# تهيئة تطبيق فلاسك
app = Flask(__name__)

# تحديد مسار مجلد قواعد البيانات
DB_DIR = '../GoalMeterics/DetectionExtraction/databases/'

# التأكد من وجود مجلد قواعد البيانات
if not os.path.exists(DB_DIR):
    os.makedirs(DB_DIR)

# دالة مساعدة للحصول على اتصال بقاعدة بيانات
def get_db_connection(db_name):
    """
    يقوم بإنشاء اتصال بقاعدة بيانات SQLite محددة.
    """
    db_path = os.path.join(DB_DIR, db_name)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row  # يسمح بالوصول إلى البيانات كقواميس
    return conn

# المسار الرئيسي للتطبيق
@app.route('/')
def index():
    """
    يعرض الصفحة الرئيسية مع قائمة بقواعد البيانات المتاحة.
    """
    db_files = [f for f in os.listdir(DB_DIR) if f.endswith('.sqlite') or f.endswith('.db')]
    return render_template('index.html', db_files=db_files)

# مسار لجلب قائمة الجداول في قاعدة بيانات معينة
@app.route('/get_tables', methods=['POST'])
def get_tables():
    """
    يستقبل اسم قاعدة البيانات ويقوم بإرجاع قائمة الجداول فيها.
    """
    db_name = request.json['db_name']
    if not db_name or not db_name.endswith(('.sqlite', '.db')):
        return jsonify({"error": "اسم قاعدة بيانات غير صالح"}), 400

    conn = None
    try:
        conn = get_db_connection(db_name)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row['name'] for row in cursor.fetchall()]
        return jsonify(tables)
    except sqlite3.OperationalError as e:
        return jsonify({"error": f"خطأ في قاعدة البيانات: {e}"}), 500
    finally:
        if conn:
            conn.close()

# مسار لجلب قائمة الأعمدة في جدول معين
@app.route('/get_columns', methods=['POST'])
def get_columns():
    """
    يستقبل اسم قاعدة البيانات واسم الجدول ويقوم بإرجاع قائمة الأعمدة.
    """
    db_name = request.json['db_name']
    table_name = request.json['table_name']
    conn = None
    try:
        conn = get_db_connection(db_name)
        cursor = conn.cursor()
        cursor.execute(f"PRAGMA table_info({table_name});")
        columns = [row['name'] for row in cursor.fetchall()]
        return jsonify(columns)
    except sqlite3.OperationalError as e:
        return jsonify({"error": f"خطأ في قاعدة البيانات: {e}"}), 500
    finally:
        if conn:
            conn.close()

# مسار لجلب البيانات من جدول معين مع إمكانية البحث
@app.route('/get_data', methods=['POST'])
def get_data():
    """
    يستقبل اسم قاعدة البيانات، اسم الجدول، ومعلومات البحث، ثم يرجع البيانات.
    """
    db_name = request.json['db_name']
    table_name = request.json['table_name']
    search_column = request.json.get('search_column')
    search_text = request.json.get('search_text')

    conn = None
    try:
        conn = get_db_connection(db_name)
        cursor = conn.cursor()

        # بناء استعلام SQL ديناميكي
        query = f"SELECT * FROM {table_name}"
        params = []
        if search_column and search_text:
            query += f" WHERE {search_column} = ?"
            params.append(f"%{search_text}%")

        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        # تحويل البيانات إلى تنسيق مناسب للعرض
        column_names = [description[0] for description in cursor.description]
        data = [dict(row) for row in rows]
        
        return jsonify({'columns': column_names, 'data': data})
    except sqlite3.OperationalError as e:
        return jsonify({"error": f"خطأ في قاعدة البيانات: {e}"}), 500
    finally:
        if conn:
            conn.close()

# تشغيل التطبيق
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=7000)
