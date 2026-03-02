from flask import Flask, render_template, request, redirect, url_for, flash, session
# Update this line based on your folder name
from python.models import *
from python.utils import *
import os
import re


app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY")
if not app.secret_key:
    raise ValueError("SECRET_KEY environment variable must be set")


# Using a relative path for the SQLite DB
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'stock_tracker.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

# Ensure database tables are created
with app.app_context():
    db.create_all()

@app.route('/')
def home():
    if "user_id" in session:
        return redirect(url_for('portfolio'))
    return redirect(url_for('login'))

#login page
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            session['user_id'] = user.id
            session['username'] = user.username
            flash('Login successful!', 'success')
            return redirect(url_for('portfolio'))
        else:
            flash('Invalid credentials', 'danger')
    return render_template('login.html')

#logout
@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

#register page
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        if User.query.filter_by(username=username).first():
            flash("Username already exists")
        else:
            user = User(username=username)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            flash("User registered! Please login.", "success")
            return redirect(url_for("login"))
    return render_template("register.html")


@app.route('/home', methods=["GET", "POST"])
def home_page():
    if "user_id" in session:
        return render_template('home.html', username=session['username'])
    flash("Please log in to access this page.")
    return redirect(url_for('login'))

@app.route('/portfolioViewer')
def portfolio():
    if "user_id" not in session:
        flash("Please log in to access this page.")
        return redirect(url_for('login'))
    user = db.session.get(User, session['user_id'])
    if user is None:
        session.clear()
        flash("Session expired. Please log in again.")
        return redirect(url_for('login'))
    if user.Portfolio is None:
        return redirect(url_for("portfolioCreator"))
    return render_template('portfolioViewer.html', portfolio=user.Portfolio, username=session['username'])

@app.route('/portfolioCreator', methods=['GET', 'POST'])
def portfolioCreator():
    if "user_id" not in session :
        flash("Please log in to access this page.")
        return redirect(url_for('login'))
    if request.method == 'POST':
        user = db.session.get(User, session['user_id'])
        if user.Portfolio is not None:
            flash("You already have a portfolio.")
            return redirect(url_for('portfolio'))
        duration_days = float(request.form['duration_days'])
        starting_money = float(request.form['starting_money'])
        portfolio = Portfolio(user_id=user.id, duration_days=duration_days, starting_money=starting_money, money=starting_money, holdings={})
        db.session.add(portfolio)
        db.session.commit()
        return redirect(url_for('portfolio'))
    return render_template('portfolioCreator.html', username=session['username'])

@app.route('/portfolioTrader', methods=['GET', 'POST'])
def portfolioTrader():
    if "user_id" not in session:
        flash("Please log in to access this page.")
        return redirect(url_for('login'))
    user = db.session.get(User, session['user_id'])
    if user.Portfolio is None:
        flash("You don't have a portfolio yet.")
        return redirect(url_for('portfolioCreator'))
    if request.method == 'POST':
        action = request.form['action']
        ticker = request.form['ticker'].upper()
        # Validate ticker format (1-5 uppercase letters)
        if not bool(re.match(r'^[A-Z]{1,5}$', ticker)):
            flash("Invalid ticker symbol", 'danger')
            return redirect(url_for('portfolioTrader'))
        # Check if the ticker on banned list
        if(is_ETF(ticker)):
            flash("ETF's, such as " + ticker + " are not allowed.", 'danger')
            return redirect(url_for('portfolioTrader'))
        if(is_russell_2000(ticker)):
            flash("Russell 2000 indices, such as " + ticker + " are not allowed.", 'danger')
            return redirect(url_for('portfolioTrader'))
        if(is_mutual_fund(ticker)):
            flash("Mutual funds, such as " + ticker + " are not allowed.", 'danger')
            return redirect(url_for('portfolioTrader'))
        if(is_banned_prefix(ticker)):
            flash("Tickers starting with " + ticker[:3] + " are not allowed.", 'danger')
            return redirect(url_for('portfolioTrader'))
        portfolio = user.Portfolio
        try:
            if action == 'buy':
                amount = float(request.form['amount'])
                shares = money_to_shares(amount, ticker) 
                price = get_current_price(ticker) 
                portfolio.buy_holding(ticker, shares, price)
            elif action == 'sell':
                sell_all = request.form.get('sell_all')
                if sell_all:
                    portfolio.sell_holding(ticker)
                else:
                    shares = float(request.form['amount'])
                    portfolio.sell_holding_shares(ticker, shares)
                
            db.session.add(portfolio)        
            db.session.commit()
        except Exception as e:
            if(float(request.form['amount']) > portfolio.money and action == 'buy'):
                flash("Insufficient funds to complete purchase", 'danger')
            else:
                flash("Stock ticker " + ticker + " not found", 'danger')
    return render_template('portfolioTrader.html', portfolio=user.Portfolio, username=session['username'])

@app.route('/delete_portfolio', methods=['POST'])
def delete_portfolio():
    if "user_id" not in session:
        flash("Please log in to access this page.")
        return redirect(url_for('login'))
    
    user = db.session.get(User, session['user_id'])
    
    if user.Portfolio is None:
        flash("You don't have a portfolio to delete.", 'info')
        return redirect(url_for('index'))
    
    try:
        db.session.delete(user.Portfolio)
        db.session.commit()
        flash("Portfolio deleted successfully.", 'success')
    except Exception as e:
        db.session.rollback()
        flash(f"Error deleting portfolio: {str(e)}", 'danger')
    
    return redirect(url_for('portfolioCreator'))

if __name__ == '__main__':
    app.run(debug=True)

# To run the app, use the command:
#python3 app.py

#activate virtual environment:
#.\venv\Scripts\Activate

#command to set a secret key
#export SECRET_KEY="some_long_random_string_here"

#deactivate virtual environment:
#deactivate