from app.database import db

def show_users():
    """Показать всех пользователей в БД"""
    session = db.get_session()
    try:
        users = session.query(db.User).all()
        print("📊 Пользователи в базе данных:")
        for user in users:
            print(f"ID: {user.id}, Telegram: {user.telegram_id}, Username: {user.username}")
        return users
    finally:
        session.close()

if __name__ == "__main__":
    show_users()