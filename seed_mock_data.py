from datetime import date

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models import *

def get_session(db_url: str):
    engine = create_engine(db_url, echo=False, future=True)
    Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return Session()


def seed_data():
    db_url = "postgresql://postgres:1465@localhost:5432/pharmacy_db"
    session = get_session(db_url)

    # Очистка старых данных (опционально)
    session.query(Sale).delete()
    session.query(Prescription).delete()
    session.query(Medicine).delete()
    session.query(MedicineType).delete()
    session.query(Supplier).delete()
    session.query(Customer).delete()
    session.query(User).delete()
    session.query(Employee).delete()
    session.commit()

    # Поставщики
    supplier1 = Supplier(name="Фарм-Мир", address="Москва, ул. Пушкина, 1", phone="+7-495-111-11-11")
    supplier2 = Supplier(name="Здоровье+", address="СПб, Невский пр., 10", phone="+7-812-222-22-22")
    supplier3 = Supplier(name="ЛекТрейд", address="Казань, ул. Ленина, 5", phone="+7-843-333-33-33")

    # Типы лекарств
    t1 = MedicineType(name="Антибиотик")
    t2 = MedicineType(name="Обезболивающее")
    t3 = MedicineType(name="Противовирусное")
    t4 = MedicineType(name="Антисептик")
    t5 = MedicineType(name="Жаропонижающее")

    # Лекарства
    m1 = Medicine(name="Амоксиклав", price=320.0, quantity=25, prescription_required=True, supplier=supplier1, types=[t1])
    m2 = Medicine(name="Парацетамол", price=50.0, quantity=100, prescription_required=False, supplier=supplier1, types=[t2, t5])
    m3 = Medicine(name="Ибупрофен", price=75.0, quantity=80, prescription_required=False, supplier=supplier2, types=[t2, t5])
    m4 = Medicine(name="Граммидин", price=180.0, quantity=40, prescription_required=False, supplier=supplier3, types=[t4])
    m5 = Medicine(name="Арбидол", price=290.0, quantity=60, prescription_required=False, supplier=supplier2, types=[t3])
    m6 = Medicine(name="Супракс", price=520.0, quantity=20, prescription_required=True, supplier=supplier3, types=[t1])
    m7 = Medicine(name="Колдрекс", price=400.0, quantity=30, prescription_required=False, supplier=supplier1, types=[t5, t4])
    m8 = Medicine(name="Стрепсилс", price=150.0, quantity=50, prescription_required=False, supplier=supplier3, types=[t4])
    m9 = Medicine(name="Анаферон", price=250.0, quantity=70, prescription_required=False, supplier=supplier2, types=[t3])
    m10 = Medicine(name="Нурофен", price=180.0, quantity=45, prescription_required=False, supplier=supplier1, types=[t2, t5])

    # Клиенты
    c1 = Customer(name="Иванов Иван", address="Москва", phone="+7-999-111-22-33")
    c2 = Customer(name="Петрова Анна", address="СПб", phone="+7-999-222-33-44")
    c3 = Customer(name="Сидоров Алексей", address="Казань", phone="+7-999-333-44-55")
    c4 = Customer(name="Мария Кузнецова", address="Екатеринбург", phone="+7-999-444-55-66")
    c5 = Customer(name="Дмитрий Смирнов", address="Новосибирск", phone="+7-999-555-66-77")

    # Сотрудники
    e1 = Employee(name="Ольга Павлова", position="Фармацевт", salary=40000)
    e2 = Employee(name="Михаил Титов", position="Фармацевт", salary=42000)
    e3 = Employee(name="Елена Орлова", position="Администратор", salary=55000)

    # Рецепты (на лекарства, которые требуют рецепт)
    p1 = Prescription(customer=c1, medicine=m1, employee=e1, date=date(2024, 5, 20), quantity=1)
    p2 = Prescription(customer=c2, medicine=m6, employee=e2, date=date(2024, 5, 21), quantity=2)

    # Продажи
    s1 = Sale(customer=c1, medicine=m1, employee=e1, date=date(2024, 5, 22), quantity=1, price=320.0)
    s2 = Sale(customer=c2, medicine=m2, employee=e2, date=date(2024, 5, 22), quantity=2, price=100.0)
    s3 = Sale(customer=c3, medicine=m3, employee=e1, date=date(2024, 5, 23), quantity=1, price=75.0)

    session.add_all([
        supplier1, supplier2, supplier3,
        t1, t2, t3, t4, t5,
        m1, m2, m3, m4, m5, m6, m7, m8, m9, m10,
        c1, c2, c3, c4, c5,
        e1, e2, e3,
        p1, p2,
        s1, s2, s3
    ])

    session.commit()
    session.close()
    print("Тестовые данные успешно добавлены.")


if __name__ == '__main__':
    seed_data()
