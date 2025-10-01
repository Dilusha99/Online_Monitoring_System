"""
Admin User Creation Script
Run this script to create an admin user or promote existing users to admin
"""

from app06 import app, db
from auth import User
import getpass

def create_admin_user():
    """Create a new admin user"""
    with app.app_context():
        print("\n" + "="*60)
        print("CREATE ADMIN USER")
        print("="*60 + "\n")
        
        username = input("Enter username: ").strip()
        if not username:
            print("❌ Username cannot be empty!")
            return
        
        # Check if user already exists
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            print(f"❌ User '{username}' already exists!")
            return
        
        email = input("Enter email: ").strip()
        if not email:
            print("❌ Email cannot be empty!")
            return
        
        # Check if email already exists
        existing_email = User.query.filter_by(email=email).first()
        if existing_email:
            print(f"❌ Email '{email}' already registered!")
            return
        
        full_name = input("Enter full name: ").strip()
        
        password = getpass.getpass("Enter password: ")
        if len(password) < 6:
            print("❌ Password must be at least 6 characters long!")
            return
        
        confirm_password = getpass.getpass("Confirm password: ")
        if password != confirm_password:
            print("❌ Passwords do not match!")
            return
        
        # Create admin user
        try:
            admin_user = User(
                username=username,
                email=email,
                full_name=full_name,
                role='admin'
            )
            admin_user.set_password(password)
            
            db.session.add(admin_user)
            db.session.commit()
            
            print(f"\n✅ Admin user '{username}' created successfully!")
            print(f"   Email: {email}")
            print(f"   Role: ADMIN")
            
        except Exception as e:
            db.session.rollback()
            print(f"\n❌ Error creating user: {str(e)}")

def promote_to_admin():
    """Promote an existing user to admin"""
    with app.app_context():
        print("\n" + "="*60)
        print("PROMOTE USER TO ADMIN")
        print("="*60 + "\n")
        
        username = input("Enter username to promote: ").strip()
        if not username:
            print("❌ Username cannot be empty!")
            return
        
        user = User.query.filter_by(username=username).first()
        if not user:
            print(f"❌ User '{username}' not found!")
            return
        
        if user.role == 'admin':
            print(f"ℹ️  User '{username}' is already an admin!")
            return
        
        print(f"\nUser Details:")
        print(f"  Username: {user.username}")
        print(f"  Email: {user.email}")
        print(f"  Full Name: {user.full_name or 'Not provided'}")
        print(f"  Current Role: {user.role}")
        
        confirm = input(f"\nPromote '{username}' to admin? (yes/no): ").strip().lower()
        if confirm == 'yes':
            try:
                user.role = 'admin'
                db.session.commit()
                print(f"\n✅ User '{username}' promoted to admin successfully!")
            except Exception as e:
                db.session.rollback()
                print(f"\n❌ Error promoting user: {str(e)}")
        else:
            print("❌ Operation cancelled.")

def list_users():
    """List all users in the system"""
    with app.app_context():
        print("\n" + "="*60)
        print("ALL USERS")
        print("="*60 + "\n")
        
        users = User.query.all()
        if not users:
            print("No users found in the database.")
            return
        
        print(f"{'ID':<5} {'Username':<15} {'Email':<25} {'Role':<10} {'Active':<8}")
        print("-" * 70)
        
        for user in users:
            active_status = "Yes" if user.is_active else "No"
            print(f"{user.id:<5} {user.username:<15} {user.email:<25} {user.role:<10} {active_status:<8}")
        
        print(f"\nTotal users: {len(users)}")
        admin_count = sum(1 for u in users if u.role == 'admin')
        print(f"Admin users: {admin_count}")

def deactivate_user():
    """Deactivate a user account"""
    with app.app_context():
        print("\n" + "="*60)
        print("DEACTIVATE USER")
        print("="*60 + "\n")
        
        username = input("Enter username to deactivate: ").strip()
        if not username:
            print("❌ Username cannot be empty!")
            return
        
        user = User.query.filter_by(username=username).first()
        if not user:
            print(f"❌ User '{username}' not found!")
            return
        
        if not user.is_active:
            print(f"ℹ️  User '{username}' is already deactivated!")
            return
        
        confirm = input(f"\nDeactivate user '{username}'? (yes/no): ").strip().lower()
        if confirm == 'yes':
            try:
                user.is_active = False
                db.session.commit()
                print(f"\n✅ User '{username}' deactivated successfully!")
            except Exception as e:
                db.session.rollback()
                print(f"\n❌ Error deactivating user: {str(e)}")
        else:
            print("❌ Operation cancelled.")

def main():
    """Main menu"""
    while True:
        print("\n" + "="*60)
        print("PLANT MONITORING SYSTEM - USER MANAGEMENT")
        print("="*60)
        print("\n1. Create new admin user")
        print("2. Promote existing user to admin")
        print("3. List all users")
        print("4. Deactivate user")
        print("5. Exit")
        
        choice = input("\nEnter your choice (1-5): ").strip()
        
        if choice == '1':
            create_admin_user()
        elif choice == '2':
            promote_to_admin()
        elif choice == '3':
            list_users()
        elif choice == '4':
            deactivate_user()
        elif choice == '5':
            print("\n👋 Goodbye!")
            break
        else:
            print("\n❌ Invalid choice! Please enter 1-5.")

# if __name__ == "__main__":
#     try:
#         main()
#     except KeyboardInterrupt:
#         print("\n\n👋 Goodbye!")
#     except Exception as e:
#         print(f"\n❌ An error occurred: {str(e)}")
