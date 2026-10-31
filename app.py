from datetime import datetime, date, timedelta
from decimal import Decimal, ROUND_HALF_UP
from functools import wraps
import os, secrets
from flask import Flask, request, jsonify, session, render_template
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

from dotenv import load_dotenv

BASE = os.path.abspath(os.path.dirname(__file__))

# Load .env from the parent project folder
load_dotenv(dotenv_path=os.path.join(BASE, '..', '.env'))

DATABASE_URL = os.environ.get('DATABASE_URL')
SECRET_KEY = os.environ.get('SECRET_KEY')

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL missing. Check your .env file.")

if not SECRET_KEY:
    raise RuntimeError("SECRET_KEY missing. Check your .env file.")

app = Flask(__name__)

app.config.update(
    SECRET_KEY=SECRET_KEY,
    SQLALCHEMY_DATABASE_URI=DATABASE_URL,
    SQLALCHEMY_TRACK_MODIFICATIONS=False,
    SQLALCHEMY_ENGINE_OPTIONS={
        'connect_args': {'sslmode': 'require'}
    },
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax'
)

db = SQLAlchemy(app)

class User(db.Model):
    id=db.Column(db.Integer,primary_key=True); name=db.Column(db.String(100),nullable=False); email=db.Column(db.String(180),unique=True,nullable=False); password=db.Column(db.String(255),nullable=False); role=db.Column(db.String(20),default='customer'); created_at=db.Column(db.DateTime,default=datetime.utcnow)
class Customer(db.Model):
    id=db.Column(db.Integer,primary_key=True); name=db.Column(db.String(120),nullable=False); email=db.Column(db.String(180),nullable=False); company=db.Column(db.String(140),default=''); phone=db.Column(db.String(40),default=''); status=db.Column(db.String(20),default='Active'); user_id=db.Column(db.Integer,db.ForeignKey('user.id')); created_at=db.Column(db.DateTime,default=datetime.utcnow)
class Product(db.Model):
    id=db.Column(db.Integer,primary_key=True); name=db.Column(db.String(140),nullable=False); kind=db.Column(db.String(40),default='Service'); price=db.Column(db.Float,default=0); cost=db.Column(db.Float,default=0); notes=db.Column(db.Text,default=''); variants=db.Column(db.Text,default=''); active=db.Column(db.Boolean,default=True)
class Plan(db.Model):
    id=db.Column(db.Integer,primary_key=True); name=db.Column(db.String(140),nullable=False); product_id=db.Column(db.Integer,db.ForeignKey('product.id')); price=db.Column(db.Float,default=0); interval=db.Column(db.String(20),default='monthly'); min_qty=db.Column(db.Integer,default=1); start_date=db.Column(db.Date); end_date=db.Column(db.Date); auto_close=db.Column(db.Boolean,default=False); allow_pause=db.Column(db.Boolean,default=True); allow_renew=db.Column(db.Boolean,default=True); active=db.Column(db.Boolean,default=True)
class Tax(db.Model):
    id=db.Column(db.Integer,primary_key=True); name=db.Column(db.String(80)); rate=db.Column(db.Float,default=0); active=db.Column(db.Boolean,default=True)
class Discount(db.Model):
    id=db.Column(db.Integer,primary_key=True); name=db.Column(db.String(100)); kind=db.Column(db.String(20),default='percent'); value=db.Column(db.Float,default=0); min_qty=db.Column(db.Integer,default=1); max_uses=db.Column(db.Integer,default=0); used=db.Column(db.Integer,default=0); starts=db.Column(db.Date); ends=db.Column(db.Date); active=db.Column(db.Boolean,default=True)
class Subscription(db.Model):
    id=db.Column(db.Integer,primary_key=True); number=db.Column(db.String(30),unique=True); customer_id=db.Column(db.Integer,db.ForeignKey('customer.id')); plan_id=db.Column(db.Integer,db.ForeignKey('plan.id')); product_id=db.Column(db.Integer,db.ForeignKey('product.id')); qty=db.Column(db.Integer,default=1); unit_price=db.Column(db.Float,default=0); variant=db.Column(db.String(100),default=''); status=db.Column(db.String(30),default='Draft'); start_date=db.Column(db.Date); expiry_date=db.Column(db.Date); next_bill=db.Column(db.Date); payment_terms=db.Column(db.String(40),default='Due on receipt'); discount_id=db.Column(db.Integer,db.ForeignKey('discount.id')); created_at=db.Column(db.DateTime,default=datetime.utcnow)
class Invoice(db.Model):
    id=db.Column(db.Integer,primary_key=True); number=db.Column(db.String(30),unique=True); subscription_id=db.Column(db.Integer,db.ForeignKey('subscription.id')); customer_id=db.Column(db.Integer,db.ForeignKey('customer.id')); issue_date=db.Column(db.Date,default=date.today); due_date=db.Column(db.Date); subtotal=db.Column(db.Float,default=0); discount=db.Column(db.Float,default=0); tax=db.Column(db.Float,default=0); total=db.Column(db.Float,default=0); paid=db.Column(db.Float,default=0); status=db.Column(db.String(20),default='Draft'); description=db.Column(db.String(240),default='Subscription billing')
class Payment(db.Model):
    id=db.Column(db.Integer,primary_key=True); invoice_id=db.Column(db.Integer,db.ForeignKey('invoice.id')); method=db.Column(db.String(40)); amount=db.Column(db.Float); paid_on=db.Column(db.Date,default=date.today); note=db.Column(db.String(240),default='')
class QuoteTemplate(db.Model):
    id=db.Column(db.Integer,primary_key=True); name=db.Column(db.String(120)); plan_id=db.Column(db.Integer,db.ForeignKey('plan.id')); validity_days=db.Column(db.Integer,default=14)
class ResetToken(db.Model):
    id=db.Column(db.Integer,primary_key=True); user_id=db.Column(db.Integer,db.ForeignKey('user.id')); token=db.Column(db.String(100),unique=True); expires=db.Column(db.DateTime)

def iso(v): return v.isoformat() if v else None
def money(v): return round(float(v or 0),2)
def role_required(*roles):
    def deco(fn):
        @wraps(fn)
        def wrapped(*a,**kw):
            u=User.query.get(session.get('uid'))
            if not u: return jsonify(error='Authentication required'),401
            if roles and u.role not in roles: return jsonify(error='Permission denied'),403
            return fn(*a,**kw)
        return wrapped
    return deco
def current_user(): return User.query.get(session.get('uid'))
def payload(): return request.get_json(silent=True) or request.form.to_dict()
def safe_user(u): return {'id':u.id,'name':u.name,'email':u.email,'role':u.role}
def as_dict(obj, fields): return {f:(iso(getattr(obj,f)) if isinstance(getattr(obj,f),date) else getattr(obj,f)) for f in fields}
def next_date(d,interval):
    if interval=='daily': return d+timedelta(days=1)
    if interval=='weekly': return d+timedelta(days=7)
    if interval=='yearly': return d.replace(year=d.year+1)
    # month-safe
    m=d.month%12+1; y=d.year+(d.month//12); import calendar
    return d.replace(year=y,month=m,day=min(d.day,calendar.monthrange(y,m)[1]))
def variant_surcharge(product, selected):
    if not selected or not product.variants: return 0.0
    for item in product.variants.split(','):
        if ':' in item:
            name,delta=item.strip().split(':',1)
            if name.strip().lower()==selected.strip().lower():
                try: return float(delta.strip().replace('+',''))
                except ValueError: return 0.0
    return 0.0

def invoice_build(s):
    # Idempotency: only one invoice per subscription and billing cycle (issue date = next_bill)
    existing=Invoice.query.filter_by(subscription_id=s.id,issue_date=s.next_bill).first()
    if existing: return existing,False
    p=Product.query.get(s.product_id); plan=Plan.query.get(s.plan_id)
    subtotal=money(s.unit_price*s.qty); disc=0
    if s.discount_id:
        d=Discount.query.get(s.discount_id)
        if d and d.active and (not d.starts or d.starts<=date.today()) and (not d.ends or d.ends>=date.today()) and (not d.max_uses or d.used<d.max_uses) and s.qty>=d.min_qty:
            disc=money(min(subtotal,d.value if d.kind=='fixed' else subtotal*d.value/100)); d.used+=1
    taxable=max(0,subtotal-disc); rate=sum(t.rate for t in Tax.query.filter_by(active=True).all()); tax=money(taxable*rate/100); total=money(taxable+tax)
    inv=Invoice(number=f'INV-{datetime.utcnow():%y%m}-{secrets.randbelow(90000)+10000}',subscription_id=s.id,customer_id=s.customer_id,issue_date=s.next_bill,due_date=s.next_bill+timedelta(days=15),subtotal=subtotal,discount=disc,tax=tax,total=total,status='Confirmed')
    db.session.add(inv); return inv,True

@app.get('/')
def index(): return render_template('index.html')
@app.get('/api/me')
def me():
    u=current_user(); return jsonify(user=safe_user(u) if u else None)
@app.post('/api/register')
def register():
    d=payload(); email=d.get('email','').strip().lower(); pw=d.get('password','')
    if not email or not d.get('name') or len(pw)<=8 or not any(c.isupper() for c in pw) or not any(c.islower() for c in pw) or not any(not c.isalnum() for c in pw): return jsonify(error='Use a password longer than 8 characters with uppercase, lowercase and a special character.'),400
    if User.query.filter_by(email=email).first(): return jsonify(error='This email already has an account.'),409
    u=User(name=d['name'],email=email,password=generate_password_hash(pw),role='customer'); db.session.add(u); db.session.flush(); db.session.add(Customer(name=u.name,email=email,company=d.get('company',''),user_id=u.id)); db.session.commit(); session['uid']=u.id; return jsonify(user=safe_user(u))
@app.post('/api/login')
def login():
    d=payload(); u=User.query.filter_by(email=d.get('email','').lower()).first()
    if not u or not check_password_hash(u.password,d.get('password','')): return jsonify(error='Invalid email or password.'),401
    session['uid']=u.id; return jsonify(user=safe_user(u))
@app.post('/api/logout')
def logout(): session.clear(); return jsonify(ok=True)
@app.post('/api/forgot')
def forgot():
    u=User.query.filter_by(email=payload().get('email','').lower()).first()
    if u:
        token=secrets.token_urlsafe(24); db.session.add(ResetToken(user_id=u.id,token=token,expires=datetime.utcnow()+timedelta(hours=1))); db.session.commit()
        # Demo mode: print reset URL to server console. Configure SMTP for production.
        print(f"PASSWORD RESET (demo): http://localhost:5000/reset/{token}")
    return jsonify(message='If the account exists, a reset link has been generated. In demo mode check the server console.')
@app.get('/reset/<token>')
def reset_page(token):
    t=ResetToken.query.filter_by(token=token).first()
    if not t or t.expires<datetime.utcnow(): return 'This password reset link is invalid or expired.',400
    return render_template('reset.html',token=token)

@app.post('/api/reset/<token>')
def reset(token):
    d=payload(); t=ResetToken.query.filter_by(token=token).first(); pw=d.get('password','')
    if not t or t.expires<datetime.utcnow(): return jsonify(error='Reset link is invalid or expired.'),400
    if len(pw)<=8 or not any(c.isupper() for c in pw) or not any(c.islower() for c in pw) or not any(not c.isalnum() for c in pw): return jsonify(error='Password does not meet the security rules.'),400
    u=User.query.get(t.user_id); u.password=generate_password_hash(pw); db.session.delete(t); db.session.commit(); return jsonify(ok=True)

@app.get('/api/dashboard')
@role_required('admin','staff')
def dashboard():
    active=Subscription.query.filter_by(status='Active').count(); outstanding=sum(max(0,i.total-i.paid) for i in Invoice.query.filter(Invoice.status!='Paid').all()); revenue=sum(p.amount for p in Payment.query.all()); overdue=Invoice.query.filter(Invoice.due_date<date.today(),Invoice.status!='Paid').all()
    monthly=[]
    for n in range(5,-1,-1):
        first=(date.today().replace(day=1)-timedelta(days=1)).replace(day=1) if n==1 else date.today().replace(day=1)
        # month offset
        y=date.today().year; m=date.today().month-n
        while m<=0: m+=12; y-=1
        rows=Payment.query.filter(db.extract('year',Payment.paid_on)==y,db.extract('month',Payment.paid_on)==m).all(); monthly.append({'month':date(y,m,1).strftime('%b'),'revenue':money(sum(x.amount for x in rows))})
    return jsonify(active=active,revenue=money(revenue),outstanding=money(outstanding),overdue=len(overdue),subscriptions=Subscription.query.count(),customers=Customer.query.count(),invoices=Invoice.query.count(),monthly=monthly,overdue_list=[dict(id=i.id,number=i.number,due=iso(i.due_date),total=i.total,paid=i.paid,customer=Customer.query.get(i.customer_id).name if Customer.query.get(i.customer_id) else '') for i in overdue[:8]])

# Generic read endpoints
@app.get('/api/<entity>')
@role_required('admin','staff','customer')
def list_entity(entity):
    u=current_user(); maps={'products':(Product,['id','name','kind','price','cost','notes','variants','active']),'plans':(Plan,['id','name','product_id','price','interval','min_qty','start_date','end_date','auto_close','allow_pause','allow_renew','active']),'customers':(Customer,['id','name','email','company','phone','status','user_id']),'subscriptions':(Subscription,['id','number','customer_id','plan_id','product_id','qty','unit_price','variant','status','start_date','expiry_date','next_bill','payment_terms','discount_id']),'invoices':(Invoice,['id','number','subscription_id','customer_id','issue_date','due_date','subtotal','discount','tax','total','paid','status','description']),'payments':(Payment,['id','invoice_id','method','amount','paid_on','note']),'discounts':(Discount,['id','name','kind','value','min_qty','max_uses','used','starts','ends','active']),'taxes':(Tax,['id','name','rate','active']),'templates':(QuoteTemplate,['id','name','plan_id','validity_days']),'team':(User,['id','name','email','role'])}
    if entity not in maps: return jsonify(error='Unknown resource'),404
    model,fields=maps[entity]; q=model.query
    if entity=='team' and u.role!='admin': return jsonify(error='Permission denied'),403
    if u.role=='customer':
        c=Customer.query.filter_by(user_id=u.id).first()
        if entity=='subscriptions': q=q.filter_by(customer_id=c.id if c else -1)
        elif entity=='invoices': q=q.filter_by(customer_id=c.id if c else -1)
        elif entity=='customers': q=q.filter_by(user_id=u.id)
        else: return jsonify(error='Permission denied'),403
    rows=q.order_by(model.id.desc()).all(); out=[]
    for o in rows:
        x=as_dict(o,fields)
        if entity=='team': x.pop('password',None)
        if entity=='subscriptions':
            x['customer']=Customer.query.get(o.customer_id).name if Customer.query.get(o.customer_id) else ''; x['plan']=Plan.query.get(o.plan_id).name if Plan.query.get(o.plan_id) else ''; x['product']=Product.query.get(o.product_id).name if Product.query.get(o.product_id) else ''
        if entity=='invoices': x['customer']=Customer.query.get(o.customer_id).name if Customer.query.get(o.customer_id) else ''; x['balance']=money(o.total-o.paid)
        if entity=='payments': x['invoice']=Invoice.query.get(o.invoice_id).number if Invoice.query.get(o.invoice_id) else ''
        out.append(x)
    return jsonify(out)

@app.post('/api/<entity>')
@role_required('admin','staff')
def create_entity(entity):
    d=payload();
    if entity in ('products','plans','discounts','taxes','templates') and current_user().role!='admin': return jsonify(error='Only admin can manage catalog, tax and discount rules.'),403
    models={'products':Product,'plans':Plan,'customers':Customer,'subscriptions':Subscription,'discounts':Discount,'taxes':Tax,'templates':QuoteTemplate}
    if entity=='team':
        if current_user().role!='admin': return jsonify(error='Only admin can add staff.'),403
        pw=d.get('password','')
        if len(pw)<=8 or not any(c.isupper() for c in pw) or not any(c.islower() for c in pw) or not any(not c.isalnum() for c in pw): return jsonify(error='Password must be longer than 8 characters and include uppercase, lowercase and special character.'),400
        email=d.get('email','').lower()
        if User.query.filter_by(email=email).first(): return jsonify(error='Email already exists.'),409
        u=User(name=d['name'],email=email,password=generate_password_hash(pw),role='staff'); db.session.add(u); db.session.commit(); return jsonify(id=u.id),201
    if entity not in models: return jsonify(error='Unsupported resource'),404
    model=models[entity]
    if entity=='customers': obj=Customer(name=d['name'],email=d['email'],company=d.get('company',''),phone=d.get('phone',''),status=d.get('status','Active'))
    elif entity=='products': obj=Product(name=d['name'],kind=d.get('kind','Service'),price=float(d.get('price',0)),cost=float(d.get('cost',0)),notes=d.get('notes',''),variants=d.get('variants',''))
    elif entity=='plans': obj=Plan(name=d['name'],product_id=d.get('product_id'),price=float(d.get('price',0)),interval=d.get('interval','monthly'),min_qty=int(d.get('min_qty',1)),start_date=date.fromisoformat(d['start_date']) if d.get('start_date') else None,end_date=date.fromisoformat(d['end_date']) if d.get('end_date') else None,auto_close=bool(d.get('auto_close')),allow_pause=bool(d.get('allow_pause',True)),allow_renew=bool(d.get('allow_renew',True)))
    
    elif entity=='subscriptions':
        plan=Plan.query.get(int(d['plan_id']))
        if not plan:
            return jsonify(error='Selected plan does not exist.'),404

        prod=Product.query.get(plan.product_id)
        if not prod:
            return jsonify(error='Product linked to this plan does not exist.'),404

        try:
            qty=int(d.get('qty') or 1)
        except (TypeError,ValueError):
            return jsonify(error='Quantity must be a valid positive whole number.'),400

        if qty < 1:
            return jsonify(error='Quantity must be at least 1.'),400

        start=date.fromisoformat(d.get('start_date') or date.today().isoformat())
        expiry=date.fromisoformat(d['expiry_date']) if d.get('expiry_date') else None

        obj=Subscription(
            number=f'SUB-{datetime.utcnow():%y%m}-{secrets.randbelow(90000)+10000}',
            customer_id=int(d['customer_id']),
            plan_id=plan.id,
            product_id=prod.id,
            qty=qty,
            unit_price=(float(d['unit_price']) if d.get('unit_price') not in (None,'') else float(plan.price))+variant_surcharge(prod,d.get('variant','')),
            variant=d.get('variant',''),
            status=d.get('status','Draft'),
            start_date=start,
            expiry_date=expiry,
            next_bill=start,
            payment_terms=d.get('payment_terms','Due on receipt'),
            discount_id=int(d['discount_id']) if d.get('discount_id') else None
        )

    elif entity=='discounts': obj=Discount(name=d['name'],kind=d.get('kind','percent'),value=float(d.get('value',0)),min_qty=int(d.get('min_qty',1)),max_uses=int(d.get('max_uses',0)),starts=date.fromisoformat(d['starts']) if d.get('starts') else None,ends=date.fromisoformat(d['ends']) if d.get('ends') else None)
    elif entity=='taxes': obj=Tax(name=d['name'],rate=float(d.get('rate',0)))
    else: obj=QuoteTemplate(name=d['name'],plan_id=int(d['plan_id']),validity_days=int(d.get('validity_days',14)))
    db.session.add(obj); db.session.commit(); return jsonify(id=obj.id),201

@app.patch('/api/<entity>/<int:oid>')
@role_required('admin','staff')
def update_entity(entity,oid):
    d=payload();
    if entity in ('products','plans','discounts','taxes') and current_user().role!='admin': return jsonify(error='Only admin can update this resource.'),403
    maps={'products':Product,'plans':Plan,'customers':Customer,'subscriptions':Subscription,'discounts':Discount,'taxes':Tax,'invoices':Invoice}; model=maps.get(entity)
    if not model: return jsonify(error='Unsupported resource'),404
    o=model.query.get_or_404(oid)
    allowed=set(c.name for c in model.__table__.columns)-{'id','number','created_at','password'}
    for k,v in d.items():
        if k in allowed:
            col=getattr(model,k).property.columns[0]
            if isinstance(col.type,db.Date) and v: v=date.fromisoformat(v)
            setattr(o,k,v)
    db.session.commit(); return jsonify(ok=True)

@app.post('/api/subscriptions/<int:sid>/action')
@role_required('admin','staff')
def subscription_action(sid):
    s=Subscription.query.get_or_404(sid); action=payload().get('action'); transitions={'quote':'Quotation','confirm':'Confirmed','activate':'Active','close':'Closed','pause':'Paused','resume':'Active'}
    if action not in transitions: return jsonify(error='Invalid action'),400
    if action=='pause' and not Plan.query.get(s.plan_id).allow_pause: return jsonify(error='This plan does not allow pausing.'),400
    s.status=transitions[action]; db.session.commit(); return jsonify(status=s.status)
@app.post('/api/billing/run')
@role_required('admin','staff')
def run_billing():
    today=date.today(); due=Subscription.query.filter(Subscription.status=='Active',Subscription.next_bill<=today).all(); created=[]
    for s in due:
        inv,new=invoice_build(s)
        if new: created.append(inv.number)
        plan=Plan.query.get(s.plan_id); s.next_bill=next_date(s.next_bill,plan.interval)
        if s.expiry_date and s.next_bill>s.expiry_date and plan.auto_close: s.status='Closed'
    db.session.commit(); return jsonify(created=len(created),invoices=created,message=f'{len(created)} invoice(s) generated; duplicate cycles were skipped.')
@app.post('/api/templates/<int:tid>/quote')
@role_required('admin','staff')
def quote_from_template(tid):
    d=payload(); t=QuoteTemplate.query.get_or_404(tid); plan=Plan.query.get_or_404(t.plan_id); product=Product.query.get_or_404(plan.product_id)
    customer=Customer.query.get(int(d.get('customer_id',1)))
    if not customer: return jsonify(error='Select a valid customer.'),400
    start=date.fromisoformat(d.get('start_date') or date.today().isoformat())
    sub=Subscription(number=f'SUB-{datetime.utcnow():%y%m}-{secrets.randbelow(90000)+10000}',customer_id=customer.id,plan_id=plan.id,product_id=product.id,qty=max(plan.min_qty,1),unit_price=plan.price,status='Quotation',start_date=start,expiry_date=start+timedelta(days=t.validity_days),next_bill=start,payment_terms='Due on receipt')
    db.session.add(sub); db.session.commit(); return jsonify(id=sub.id,number=sub.number,status=sub.status,expiry_date=iso(sub.expiry_date)),201

@app.post('/api/invoices/<int:iid>/action')
@role_required('admin','staff')
def invoice_action(iid):
    i=Invoice.query.get_or_404(iid); a=payload().get('action')
    if a=='confirm': i.status='Confirmed'
    elif a=='send': i.status='Sent'
    elif a=='cancel':
        if i.paid: return jsonify(error='A paid invoice cannot be cancelled.'),400
        i.status='Cancelled'
    elif a=='print': return jsonify(print_url=f'/invoice/{iid}/print')
    else: return jsonify(error='Invalid action'),400
    db.session.commit(); return jsonify(status=i.status)
@app.post('/api/payments')
@role_required('admin','staff')
def add_payment():
    d=payload(); i=Invoice.query.get_or_404(int(d['invoice_id'])); amount=money(d.get('amount',0))
    if amount<=0 or amount>money(i.total-i.paid)+0.001: return jsonify(error='Payment must be positive and cannot exceed the outstanding balance.'),400
    p=Payment(invoice_id=i.id,method=d.get('method','Bank transfer'),amount=amount,paid_on=date.fromisoformat(d.get('paid_on') or date.today().isoformat()),note=d.get('note','')); i.paid=money(i.paid+amount); i.status='Paid' if i.paid>=i.total else 'Partially Paid'; db.session.add(p); db.session.commit(); return jsonify(id=p.id,status=i.status)
@app.get('/invoice/<int:iid>/print')
@role_required('admin','staff','customer')
def print_invoice(iid):
    i=Invoice.query.get_or_404(iid); u=current_user()
    if u.role=='customer':
        c=Customer.query.filter_by(user_id=u.id).first()
        if not c or c.id!=i.customer_id: return 'Forbidden',403
    return render_template('invoice.html',invoice=i,customer=Customer.query.get(i.customer_id))
@app.get('/api/reports')
@role_required('admin','staff')
def reports():
    inv=Invoice.query.all(); subs=Subscription.query.all(); payments=Payment.query.all()
    return jsonify(total_billed=money(sum(x.total for x in inv)),collected=money(sum(x.amount for x in payments)),outstanding=money(sum(max(0,x.total-x.paid) for x in inv if x.status!='Cancelled')),active=len([s for s in subs if s.status=='Active']),by_status={k:sum(1 for s in subs if s.status==k) for k in ['Draft','Quotation','Confirmed','Active','Paused','Closed']})

def seed():
    admin=User(name='Alex Morgan',email='admin@brightloop.demo',password=generate_password_hash('Brightloop@2026'),role='admin'); staff=User(name='Jamie Lee',email='staff@brightloop.demo',password=generate_password_hash('Staff@Brightloop26'),role='staff'); custu=User(name='Taylor Reed',email='customer@brightloop.demo',password=generate_password_hash('Customer@2026'),role='customer'); db.session.add_all([admin,staff,custu]); db.session.flush()
    c1=Customer(name='Taylor Reed',email=custu.email,company='Northstar Studio',phone='+91 98765 43210',user_id=custu.id); c2=Customer(name='Maya Patel',email='maya@northstar.io',company='Northstar Labs',phone='+91 91234 56789'); db.session.add_all([c1,c2]); db.session.flush()
    p1=Product(name='Brightloop Workspace',kind='Software',price=2499,cost=620,notes='Collaborative workspace subscription',variants='Standard:0, Odoo:+560'); p2=Product(name='Analytics Pro',kind='Add-on',price=999,cost=210,notes='Advanced analytics module'); db.session.add_all([p1,p2]); db.session.flush()
    pl1=Plan(name='Growth Monthly',product_id=p1.id,price=2499,interval='monthly',min_qty=1,allow_pause=True,allow_renew=True); pl2=Plan(name='Enterprise Annual',product_id=p1.id,price=24990,interval='yearly',min_qty=5,allow_pause=False); pl3=Plan(name='Analytics Monthly',product_id=p2.id,price=999,interval='monthly'); db.session.add_all([pl1,pl2,pl3]); db.session.add_all([Tax(name='GST',rate=18),Discount(name='Seat expansion',kind='percent',value=10,min_qty=5,max_uses=100),QuoteTemplate(name='Enterprise proposal',plan_id=pl2.id,validity_days=21)]); db.session.flush()
    s1=Subscription(number='SUB-2601-10021',customer_id=c1.id,plan_id=pl1.id,product_id=p1.id,qty=3,unit_price=2499,status='Active',start_date=date.today()-timedelta(days=35),next_bill=date.today()-timedelta(days=2)); s2=Subscription(number='SUB-2601-10022',customer_id=c2.id,plan_id=pl3.id,product_id=p2.id,qty=2,unit_price=999,status='Active',start_date=date.today()-timedelta(days=10),next_bill=date.today()+timedelta(days=20)); s3=Subscription(number='SUB-2601-10023',customer_id=c2.id,plan_id=pl2.id,product_id=p1.id,qty=10,unit_price=24990,status='Quotation',start_date=date.today(),next_bill=date.today()); db.session.add_all([s1,s2,s3]); db.session.flush()
    i1=Invoice(number='INV-2601-10001',subscription_id=s1.id,customer_id=c1.id,issue_date=date.today()-timedelta(days=15),due_date=date.today()-timedelta(days=1),subtotal=7497,tax=1349.46,total=8846.46,paid=5000,status='Partially Paid'); i2=Invoice(number='INV-2601-10002',subscription_id=s2.id,customer_id=c2.id,issue_date=date.today()-timedelta(days=8),due_date=date.today()+timedelta(days=7),subtotal=1998,tax=359.64,total=2357.64,paid=2357.64,status='Paid'); db.session.add_all([i1,i2]); db.session.flush(); db.session.add_all([Payment(invoice_id=i1.id,method='Bank transfer',amount=5000,paid_on=date.today()-timedelta(days=5),note='Part payment'),Payment(invoice_id=i2.id,method='UPI',amount=2357.64,paid_on=date.today()-timedelta(days=3),note='Paid in full')]); db.session.commit()

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        if not User.query.first():
            seed()

    app.run(debug=False, port=5000)