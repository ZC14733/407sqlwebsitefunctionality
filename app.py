from flask import Flask, request, jsonify, render_template, abort, redirect
from flask_login import LoginManager, login_user, logout_user, login_required, current_user, UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from flask_mysqldb import MySQL

app = Flask(__name__)
app.secret_key = 'your_secret_key' # required for session cookies

# MySQL configurations
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'your_password'
app.config['MYSQL_DB'] = 'rrsql'

mysql = MySQL(app)

# --- Flask-Login Config ---
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

def is_manager():
    return current_user.role in ['Manager']

def role_required(*roles):
    def wrapper (fn):
        @wraps(fn)
        def decorated_view(*args, **kwargs):
            if not current_user.is_authenticated or current_user.role not in roles:
                return abort(403)
            return fn(*args, **kwargs)
        return decorated_view
    return wrapper

class User(UserMixin):
    def __init__(self, id, username, password, role):
        self.id = id
        self.name = username
        self.password = password
        self.role = role

@login_manager.user_loader
def load_user(user_id):
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM users WHERE id = %s", (user_id))
    user_data = cur.fetchone()
    cur.close()
    if user_data:
        return User(*user_data)
    return None

@app.route('/index', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM users WHERE username = %s", (username,))
        user_data = cur.fetchone()
        cur.close()

        if user_data and check_password_hash(user_data[3], password):
            user = User(*user_data)
            login_user(user)
            return redirect('/')
        else: 
            return render_template('index.html', error="Invalid credentials")
    return render_template('index.html')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/create_promo', methods=['GET', 'POST'])
@login_required
def create_promo():
    if request.method == 'POST':
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO Promotion (Description, DiscountAmount, StartDate, EndDate, ManagerID) VALUES (%s, %s, %s, %s, %s)", (request.form['description'], request.form['discount_amount'], 
              request.form['start_date'], request.form['end_date'], current_user.id))
        mysql.connection.commit()
        cur.close()
    return render_template('create_promo.html')

@app.route('/customer_profile/<int:customer_id>')
@login_required
def customer_profile(customer_id):
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM CustomerInformation WHERE CustomerID = %s", (customer_id,))
    customer = cur.fetchone()
    cur.close()
    return render_template('customer_profile.html', customer=customer)

@app.route('/customers')
@login_required
def customers():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM CustomerInformation")
    customers = cur.fetchall()
    cur.close()
    return render_template('customer.html', customers=customers)

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')

@app.route('/new_customer', methods=['GET', 'POST'])
@login_required
def new_customer():
    if request.method == 'POST':
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO CustomerInformation (FirstName, LastName, Email, PhoneNumber, Preferences) VALUES (%s, %s, %s, %s, %s)", (request.form['first_name'], request.form['last_name'], request.form['email'], 
              request.form['phone_number'], request.form['preferences']))
        mysql.connection.commit()
        cur.close()
    return render_template('new_customer.html')

@app.route('/new_product', methods=['GET', 'POST'])
@login_required
def new_product():
    if request.method == 'POST':
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO Product (Color, Brand, Category, Size, Quantity, AvailabilityStatus) VALUES (%s, %s, %s, %s, %s, %s)", (request.form['color'], request.form['brand'], request.form['category'], 
              request.form['size'], request.form['quantity'], request.form['availability_status']))
        mysql.connection.commit()
        cur.close()
    return render_template('new_product.html')

@app.route('/product_info/<int:product_id>')
@login_required
def product_info(product_id):
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM Product WHERE ProductID = %s", (product_id,))
    product = cur.fetchone()
    cur.close()
    return render_template('product_info.html', product=product)

@app.route('/product_update/<int:product_id>', methods=['GET', 'POST'])
@login_required
def product_update(product_id):
    cur = mysql.connection.cursor()
    if request.method == 'POST':
        cur.execute("UPDATE Product SET Color = %s, Brand = %s, Category = %s, Size = %s, Quantity = %s, AvailabilityStatus = %s WHERE ProductID = %s", (request.form['color'], request.form['brand'], request.form['category'], 
              request.form['size'], request.form['quantity'], request.form['availability_status'], product_id))
        mysql.connection.commit()
    cur.execute("SELECT * FROM Product WHERE ProductID = %s", (product_id,))
    product = cur.fetchone()
    cur.close()
    return render_template('product_update.html', product=product)

@app.route('/promo_dashboard')
@login_required
def promo_dashboard():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM Promotion")
    promotions = cur.fetchall()
    cur.close()
    return render_template('promo_dashboard.html', promotions=promotions)

@app.route('/promo_manage/<int:promo_id>', methods=['GET', 'POST'])
@login_required
def promo_manage(promo_id):
    cur = mysql.connection.cursor()
    if request.method == 'POST':
        cur.execute("UPDATE Promotion SET Description = %s, DiscountAmount = %s, StartDate = %s, EndDate = %s WHERE PromotionID = %s", (request.form['description'], request.form['discount_amount'], 
              request.form['start_date'], request.form['end_date'], promo_id))
        mysql.connection.commit()
    cur.execute("SELECT * FROM Promotion WHERE PromotionID = %s", (promo_id,))
    promotion = cur.fetchone()
    cur.close()
    return render_template('promo_manage.html', promotion=promotion)

@app.route('/promo_metrics')
@login_required
def promo_metrics():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM PromotionMetrics")
    metrics = cur.fetchall()
    cur.close()
    return render_template('promo_metrics.html', metrics=metrics)

@app.route('/update_customer_profile/<int:customer_id>', methods=['GET', 'POST'])
@login_required
def update_customer_profile(customer_id):
    cur = mysql.connection.cursor()
    if request.method == 'POST':
        cur.execute("UPDATE CustomerInformation SET FirstName = %s, LastName = %s, Email = %s, PhoneNumber = %s, Preferences = %s WHERE CustomerID = %s", (request.form['first_name'], request.form['last_name'], request.form['email'], 
              request.form['phone_number'], request.form['preferences'], customer_id))
        mysql.connection.commit()
    cur.execute("SELECT * FROM CustomerInformation WHERE CustomerID = %s", (customer_id,))
    customer = cur.fetchone()
    cur.close()
    return render_template('update_customer_profile.html', customer=customer)

