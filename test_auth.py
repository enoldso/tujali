#!/usr/bin/env python3
"""
Test script to verify authentication and department access
"""
from models import init_db, User, check_password_hash

def test_authentication():
    print("Testing authentication system...")
    
    # Initialize database
    init_db()
    
    # Test user credentials
    test_credentials = [
        ('admin', 'admin123'),
        ('finance', 'finance123'),
        ('lab', 'lab123'),
        ('clinical', 'clinical123'),
        ('nurse', 'nurse123')
    ]
    
    print("\nTesting login credentials:")
    for username, password in test_credentials:
        user = User.get_by_username(username)
        if user:
            is_valid = check_password_hash(user.password_hash, password)
            print(f"  {username}/{password}: {'✓ VALID' if is_valid else '✗ INVALID'} - Role: {user.role}, Department: {user.department}")
        else:
            print(f"  {username}: ✗ USER NOT FOUND")
    
    print(f"\nTotal users in database: {len(User.get_all())}")

if __name__ == "__main__":
    test_authentication()