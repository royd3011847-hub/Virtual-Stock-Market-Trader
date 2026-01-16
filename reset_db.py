from app import app, db   # change "app" if your file name is different

with app.app_context():
    db.drop_all()
    db.create_all()
    print("Database reset successfully.")
