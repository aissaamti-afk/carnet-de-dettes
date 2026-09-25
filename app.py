from flask import Flask, request, redirect, url_for, render_template_string, flash
import sqlite3
from datetime import datetime
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent
DB = APP_DIR / "daftar.db"

app = Flask(__name__)
app.secret_key = "change-this-secret-key"

HTML = r"""
<!doctype html>
<html lang="ar" dir="rtl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>دفتر الديون Pro</title>
<style>
*{box-sizing:border-box}body{margin:0;background:#f5f7fb;color:#18212f;font-family:Arial,sans-serif}
header{background:#17324d;color:white;padding:18px;text-align:center}
.container{max-width:900px;margin:auto;padding:16px}
.cards{display:grid;grid-template-columns:repeat(3,1fr);gap:10px}
.card{background:white;border-radius:14px;padding:16px;box-shadow:0 2px 10px #00000010}
.big{font-size:24px;font-weight:bold;margin-top:8px}
form{background:white;padding:16px;border-radius:14px;margin:14px 0;box-shadow:0 2px 10px #00000010}
input,select,button{width:100%;padding:12px;margin:6px 0;border:1px solid #d8dee8;border-radius:10px;font-size:16px}
button{background:#17324d;color:white;border:0;cursor:pointer}
a{color:#17324d;text-decoration:none}
.customer{background:white;border-radius:14px;padding:14px;margin:10px 0;display:flex;justify-content:space-between;gap:10px;align-items:center}
.debt{font-weight:bold}.negative{color:#198754}.positive{color:#c0392b}
table{width:100%;border-collapse:collapse;background:white;border-radius:12px;overflow:hidden}
th,td{padding:10px;border-bottom:1px solid #eee;text-align:right}
.small{color:#667085;font-size:13px}.actions{display:grid;grid-template-columns:1fr 1fr;gap:8px}
@media(max-width:600px){.cards{grid-template-columns:1fr}.customer{align-items:flex-start;flex-direction:column}.actions{grid-template-columns:1fr}}
</style>
</head>
<body>
<header><h1>📒 دفتر الديون Pro</h1><div>إدارة ديون المحل بسهولة</div></header>
<div class="container">
{% with messages=get_flashed_messages() %}
{% for m in messages %}<div class="card" style="margin:10px 0">{{m}}</div>{% endfor %}
{% endwith %}
{{ body|safe }}
</div>
</body></html>
"""

def db():
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    return con

def init_db():
    con = db()
    con.executescript("""
    CREATE TABLE IF NOT EXISTS customers(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        phone TEXT DEFAULT '',
        created_at TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS transactions(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_id INTEGER NOT NULL,
        kind TEXT NOT NULL CHECK(kind IN ('debt','payment')),
        amount REAL NOT NULL,
        description TEXT DEFAULT '',
        created_at TEXT NOT NULL,
        FOREIGN KEY(customer_id) REFERENCES customers(id)
    );
    """)
    con.commit()
    con.close()

def balance(customer_id):
    con=db()
    row=con.execute("""SELECT
        COALESCE(SUM(CASE WHEN kind='debt' THEN amount ELSE 0 END),0) -
        COALESCE(SUM(CASE WHEN kind='payment' THEN amount ELSE 0 END),0) b
        FROM transactions WHERE customer_id=?""",(customer_id,)).fetchone()
    con.close()
    return row["b"]

def money(x):
    return f"{x:,.2f} دج"

@app.route("/")
def home():
    con=db()
    customers=con.execute("SELECT * FROM customers ORDER BY name").fetchall()
    total=sum(balance(c["id"]) for c in customers)
    con.close()
    body = render_template_string("""
    <div class="cards">
      <div class="card">💰 إجمالي الديون<div class="big">{{money(total)}}</div></div>
      <div class="card">👥 عدد الزبائن<div class="big">{{customers|length}}</div></div>
      <div class="card">📱 التطبيق<div class="big">V3</div></div>
    </div>

    <form method="get" action="/">
      <input name="q" placeholder="🔎 البحث عن زبون..." value="{{request.args.get('q','')}}">
      <button>بحث</button>
    </form>

    <div class="actions">
      <a href="{{url_for('add_customer')}}"><button type="button">➕ إضافة زبون</button></a>
    </div>

    <h2>الزبائن</h2>
    {% for c in customers if (not request.args.get('q') or request.args.get('q').lower() in c['name'].lower() or request.args.get('q') in (c['phone'] or '')) %}
      {% set b=balance(c['id']) %}
      <div class="customer">
        <div><a href="{{url_for('customer', cid=c['id'])}}"><strong>👤 {{c['name']}}</strong></a>
        <div class="small">{{c['phone'] or 'بدون هاتف'}}</div></div>
        <div class="debt {{'negative' if b<=0 else 'positive'}}">{{money(b)}}</div>
      </div>
    {% else %}
      <div class="card">لا يوجد زبائن.</div>
    {% endfor %}
    """, customers=customers,total=total,money=money)
    return render_template_string(HTML,body=body)

@app.route("/customer/add", methods=["GET","POST"])
def add_customer():
    if request.method=="POST":
        name=request.form.get("name","").strip()
        phone=request.form.get("phone","").strip()
        if not name:
            flash("اكتب اسم الزبون.")
            return redirect(url_for("add_customer"))
        con=db()
        con.execute("INSERT INTO customers(name,phone,created_at) VALUES(?,?,?)",
                    (name,phone,datetime.now().isoformat(timespec="seconds")))
        con.commit(); con.close()
        flash("تمت إضافة الزبون.")
        return redirect(url_for("home"))
    body="""<h2>➕ إضافة زبون</h2>
    <form method="post">
      <label>اسم الزبون</label><input name="name" required>
      <label>رقم الهاتف</label><input name="phone" inputmode="tel">
      <button>حفظ الزبون</button>
      <a href="/">إلغاء</a>
    </form>"""
    return render_template_string(HTML,body=body)

@app.route("/customer/<int:cid>")
def customer(cid):
    con=db()
    c=con.execute("SELECT * FROM customers WHERE id=?",(cid,)).fetchone()
    tx=con.execute("SELECT * FROM transactions WHERE customer_id=? ORDER BY id DESC",(cid,)).fetchall()
    con.close()
    if not c: return "الزبون غير موجود",404
    body=render_template_string("""
    <a href="/">← الرئيسية</a>
    <h2>👤 {{c['name']}}</h2>
    <div class="card">الهاتف: {{c['phone'] or 'غير مسجل'}}<br>
    <strong>المتبقي: {{money(balance(c['id']))}}</strong></div>

    <div class="actions">
      <a href="{{url_for('transaction',cid=c['id'],kind='debt')}}"><button type="button">➕ إضافة دين</button></a>
      <a href="{{url_for('transaction',cid=c['id'],kind='payment')}}"><button type="button">💵 تسجيل دفعة</button></a>
    </div>

    <h3>🧾 العمليات</h3>
    <table><tr><th>النوع</th><th>المبلغ</th><th>الوصف</th><th>التاريخ</th></tr>
    {% for t in tx %}
    <tr><td>{{'دين' if t['kind']=='debt' else 'دفعة'}}</td>
    <td>{{money(t['amount'])}}</td><td>{{t['description']}}</td>
    <td>{{t['created_at'].replace('T',' ')}}</td></tr>
    {% else %}<tr><td colspan="4">لا توجد عمليات.</td></tr>{% endfor %}
    </table>
    """,c=c,tx=tx,money=money,balance=balance)
    return render_template_string(HTML,body=body)

@app.route("/customer/<int:cid>/transaction",methods=["GET","POST"])
def transaction(cid):
    kind=request.args.get("kind","debt")
    if kind not in ("debt","payment"): kind="debt"
    con=db(); c=con.execute("SELECT * FROM customers WHERE id=?",(cid,)).fetchone(); con.close()
    if not c: return "الزبون غير موجود",404
    if request.method=="POST":
        amount=float(request.form.get("amount","0"))
        desc=request.form.get("description","").strip()
        if amount<=0:
            flash("المبلغ يجب أن يكون أكبر من صفر.")
            return redirect(request.url)
        con=db()
        con.execute("INSERT INTO transactions(customer_id,kind,amount,description,created_at) VALUES(?,?,?,?,?)",
                    (cid,kind,amount,desc,datetime.now().isoformat(timespec="seconds")))
        con.commit(); con.close()
        flash("تم تسجيل العملية.")
        return redirect(url_for("customer",cid=cid))
    title="إضافة دين" if kind=="debt" else "تسجيل دفعة"
    body=render_template_string("""<a href="{{url_for('customer',cid=c['id'])}}">← رجوع</a>
    <h2>{{title}} — {{c['name']}}</h2>
    <form method="post">
      <label>المبلغ بالدينار</label><input name="amount" type="number" step="0.01" min="0.01" required>
      <label>الوصف</label><input name="description" placeholder="مثال: مواد غذائية">
      <button>{{title}}</button>
    </form>""",c=c,title=title)
    return render_template_string(HTML,body=body)

init_db()

if __name__=="__main__":
    print("دفتر الديون Pro يعمل على: http://127.0.0.1:5000")
    app.run(host="127.0.0.1",port=5000,debug=False)
