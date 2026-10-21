from AYLB_LOGIS import app, db
from AYLB_LOGIS.models import User
from werkzeug.security import generate_password_hash

# Push app context
app.app_context().push()

# 1. Add user
new_user = User(username='test_user', email='test@example.com',  phone_no='9999999999', password=generate_password_hash('test123'))
db.session.add(new_user)
db.session.commit()
print("✅ Added user")

# 2. Fetch all
users = User.query.all()
print(f"📊 Total users: {len(users)}")

# 3. Fetch specific
user = User.query.filter_by(username='test_user').first()
print(f"👤 Found: {user.username} - {user.email}")

# 4. Update
# user.email = 'updated@example.com'
# db.session.commit()
# print("✅ Updated user")

# # 5. Delete
# db.session.delete(user)
# db.session.commit()
# print("✅ Deleted user")