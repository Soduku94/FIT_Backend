import random
import uuid
from faker import Faker
from slugify import slugify
from app.extensions import db
from app.models.user_model import User, UserRole
from app.models.news_model import News, NewsStatus
from app.models.resource_model import Category, Paper, Dataset

fake = Faker('vi_VN')

def seed_all():
    """Chay toan bo qua trinh tao du lieu mau."""
    print("--- Bat dau qua trinh tao du lieu mau ---")
    
    # 1. Tao Users
    users = seed_users()
    
    # 2. Tao Categories
    categories = seed_categories()
    
    # 3. Tao News
    seed_news(users)
    
    # 4. Tao Resources (Papers & Datasets)
    seed_resources(users, categories)
    
    print("--- Hoan thanh khoi tao du lieu mau ---")

def seed_users():
    """Tao cac tai khoan mau."""
    print("- Dang tao nguoi dung...")
    
    # Tai khoan co dinh
    fixed_users = [
        {
            'user_code': 'admin_fit',
            'email': 'admin@fit.edu.vn',
            'full_name': 'Quan tri vien FIT',
            'role': UserRole.ADMIN,
            'dept': 'Van phong Khoa'
        },
        {
            'user_code': 'ED001',
            'email': 'editor001@fit.edu.vn',
            'full_name': 'Bien tap vien Noi dung',
            'role': UserRole.EDITOR,
            'dept': 'Ban Truyen thong'
        },
        {
            'user_code': 'GV001',
            'email': 'gv001@fit.edu.vn',
            'full_name': 'TS. Nguyen Van A',
            'role': UserRole.LECTURER,
            'dept': 'Bo mon He thong thong tin'
        },
        {
            'user_code': '20240001',
            'email': 'sv20240001@student.edu.vn',
            'full_name': 'Tran Thi Sinh Vien',
            'role': UserRole.STUDENT,
            'dept': 'Khoa CNTT',
            'class': 'K65-CNTT'
        }
    ]
    
    created_users = []
    
    for u_data in fixed_users:
        user = User.query.filter_by(user_code=u_data['user_code']).first()
        if not user:
            user = User(
                user_code=u_data['user_code'],
                email=u_data['email'],
                full_name=u_data['full_name'],
                role=u_data['role'],
                department=u_data['dept'],
                class_name=u_data.get('class')
            )
            user.set_password(u_data['user_code'].lower() + '123' if 'admin' not in u_data['user_code'] else 'admin123')
            db.session.add(user)
        created_users.append(user)
    
    # Them Giang vien ngau nhien
    for i in range(5):
        code = f"GV{100 + i}"
        if not User.query.filter_by(user_code=code).first():
            user = User(
                user_code=code,
                email=f"teacher{100+i}@fit.edu.vn",
                full_name=fake.name(),
                role=UserRole.LECTURER,
                department=random.choice(['Bo mon HTTT', 'Bo mon KHMT', 'Bo mon KTPM', 'Bo mon MMT & TT'])
            )
            user.set_password('123456')
            db.session.add(user)
            created_users.append(user)

    # Them Sinh vien ngau nhien
    for i in range(20):
        code = f"2024{1000 + i}"
        if not User.query.filter_by(user_code=code).first():
            user = User(
                user_code=code,
                email=f"sv{code}@student.edu.vn",
                full_name=fake.name(),
                role=UserRole.STUDENT,
                department='Khoa CNTT',
                class_name=f"K65-{random.choice(['CNTT', 'KHMT', 'KTPM'])}"
            )
            user.set_password('123456')
            db.session.add(user)
            created_users.append(user)
            
    db.session.commit()
    return User.query.all()

def seed_categories():
    """Tao cac danh muc tai nguyen."""
    print("- Dang tao danh muc...")
    cat_names = [
        ('Tri tue nhan tao', 'Cac tai lieu ve AI, Machine Learning, Deep Learning'),
        ('Phat trien Web', 'Tai lieu ve React, Vue, Node.js, Flask'),
        ('An toan thong tin', 'Tai lieu ve bao mat, ma hoa, mang'),
        ('Khoa hoc du lieu', 'Tai lieu ve Big Data, Data Mining'),
        ('Cong nghe phan mem', 'Quy trinh phat trien, Testing, Clean Code')
    ]
    
    categories = []
    for name, desc in cat_names:
        cat = Category.query.filter_by(name=name).first()
        if not cat:
            cat = Category(name=name, description=desc)
            db.session.add(cat)
        categories.append(cat)
    
    db.session.commit()
    return Category.query.all()

def seed_news(users):
    """Tao cac bai viet tin tuc mau."""
    print("- Dang tao bai viet tin tuc...")
    editors = [u for u in users if u.role in [UserRole.EDITOR, UserRole.ADMIN]]
    if not editors: return
    
    categories = ['Su kien', 'Giai thuong', 'Thong bao', 'Do an xuat sac', 'Nghien cuu']
    
    for i in range(15):
        title = fake.sentence(nb_words=10)
        slug = slugify(title)
        
        # Kiem tra slug trung
        if News.query.filter_by(slug=slug).first():
            slug += f"-{i}"
            
        news = News(
            title=title,
            slug=slug,
            content=f"<p>{fake.paragraph(nb_sentences=10)}</p><p>{fake.paragraph(nb_sentences=5)}</p>",
            category=random.choice(categories),
            status=random.choice([NewsStatus.PUBLISHED, NewsStatus.DRAFT]),
            author_id=random.choice(editors).id,
            thumbnail_url=f"https://picsum.photos/seed/{i}/800/400"
        )
        db.session.add(news)
    
    db.session.commit()

def seed_resources(users, categories):
    """Tao cac bai bao va bo du lieu mau."""
    print("- Dang tao tai lieu va dataset...")
    lecturers = [u for u in users if u.role == UserRole.LECTURER]
    students = [u for u in users if u.role == UserRole.STUDENT]
    uploaders = lecturers + students
    
    if not uploaders: return

    # Tao Papers
    for i in range(20):
        authors_list = [fake.name() for _ in range(random.randint(1, 3))]
        paper = Paper(
            title=fake.sentence(nb_words=8),
            description=fake.text(max_nb_chars=500),
            authors=authors_list,
            tags=[fake.word() for _ in range(3)],
            publication_year=random.randint(2018, 2024),
            journal_name=f"Journal of {fake.word().capitalize()} Science",
            doi=f"10.1234/{uuid.uuid4().hex[:8]}",
            file_url="sample_paper.pdf",
            status=random.choice(['approved', 'pending', 'approved']), # Uu tien approved
            uploader_id=random.choice(uploaders).id,
            category_id=random.choice(categories).id if categories else None,
            view_count=random.randint(0, 1000),
            download_count=random.randint(0, 200)
        )
        db.session.add(paper)

    # Tao Datasets
    for i in range(10):
        dataset = Dataset(
            title=f"Dataset for {fake.sentence(nb_words=5)}",
            description=fake.text(max_nb_chars=300),
            authors=[fake.name() for _ in range(random.randint(1, 2))],
            tags=[fake.word() for _ in range(2)],
            file_size=f"{random.randint(1, 500)} MB",
            data_format=random.choice(['CSV', 'JSON', 'ZIP', 'Images']),
            license_type=random.choice(['MIT', 'Open Source', 'Internal']),
            github_url=f"https://github.com/fit-hust/dataset-{i}",
            file_url="dataset.zip",
            status=random.choice(['approved', 'pending', 'approved']),
            uploader_id=random.choice(uploaders).id,
            category_id=random.choice(categories).id if categories else None,
            view_count=random.randint(0, 500),
            download_count=random.randint(0, 100)
        )
        db.session.add(dataset)

    db.session.commit()
