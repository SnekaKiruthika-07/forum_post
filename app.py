from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Replace with your actual secret key
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///forum.db'
db = SQLAlchemy(app)

# Database Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    bio = db.Column(db.String(200))

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(1000), nullable=False)
    likes = db.Column(db.Integer, default=0)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

# Routes
@app.route('/')
def home():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        # Check if the user exists in the database
        user = User.query.filter_by(email=email).first()
        
        # Verify password and handle login
        if user and check_password_hash(user.password, password):  # Verify password
            session['user_id'] = user.id  # Store user ID in session
            session.permanent = True  # Keep session alive even after browser is closed
            return redirect(url_for('dashboard'))  # Redirect to the dashboard page
        
        # If the credentials are invalid, display an error message
        else:
            error_message = "Invalid email or password"
            return render_template('login.html', error=error_message)
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        
        # Check if email already exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            return render_template('register.html', error="Email already registered. Please log in or use a different email.")
        
        # Create new user with hashed password
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        new_user = User(name=name, email=email, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()

        # After registration, automatically log the user in and redirect to the dashboard
        session['user_id'] = new_user.id
        session.permanent = True  # Keep session alive
        return redirect(url_for('dashboard'))
    
    return render_template('register.html')


@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user = User.query.get(session['user_id'])
    posts = Post.query.all()

    if request.method == 'POST':
        content = request.form['content']
        new_post = Post(content=content, user_id=user.id)
        db.session.add(new_post)
        db.session.commit()
        return redirect(url_for('dashboard'))
    
    return render_template('dashboard.html', posts=posts, user=user)

@app.route('/logout')
def logout():
    session.pop('user_id', None)  # Remove the user ID from the session
    return redirect(url_for('login'))

@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user = User.query.get(session['user_id'])

    if request.method == 'POST':
        user.name = request.form['name']
        user.bio = request.form['bio']
        db.session.commit()
        return redirect(url_for('profile'))
    
    return render_template('profile.html', user=user)

@app.route('/like_post/<int:post_id>')
def like_post(post_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    post = Post.query.get(post_id)
    post.likes += 1
    db.session.commit()
    return redirect(url_for('dashboard'))

if __name__ == "__main__":
    # Use app context to create tables
    with app.app_context():
        db.create_all()  # Creates the database tables if they don't exist

    app.run(debug=True)
