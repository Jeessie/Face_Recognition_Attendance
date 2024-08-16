# models.py 定义数据库模型
import os
from flask import Flask
from flask_login import UserMixin
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
from werkzeug.security import generate_password_hash, check_password_hash

flask_app = Flask(__name__, template_folder='templates')  # 创建了一个 Flask 应用实例，并将其赋值给变量 app

# 设置应用程序的配置信息
flask_app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root:root@localhost:3306/face_rec'
flask_app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
flask_app.config['SECRET_KEY'] = b'\x82#\xce0\xce\x01-\x84\xf0O\xc9\x82t\x15\xf3\xe9\xf4A>\xa2\xf8\x93l\xc1'

base_dir = os.path.dirname(os.path.abspath(__file__))
flask_app.config['UPLOAD_FOLDER'] = os.path.join(base_dir, 'uploaded_images')  # 设置上传目录

db = SQLAlchemy(flask_app)  # 创建了一个 SQLAlchemy 实例，并将其与 Flask 应用实例绑定

class Student(db.Model):
    # 设置数据库中真实表名
    __tablename__ = "student"

    sid = db.Column("sid", db.Integer, primary_key=True, autoincrement=True, doc="学生id")
    sname = db.Column("sname", db.String(255), nullable=False, doc="姓名")
    snumber = db.Column("snumber", db.String(255), nullable=False, unique=True, doc="学号")
    sclass = db.Column("major_class", db.String(255), nullable=False, doc="班级")
    # sgender = db.Column(db.Enum("男", "女"), doc="性别")
    # 添加关系到StudentPhoto
    photos = db.relationship('StudentPhoto', backref='student')

class StudentPhoto(db.Model):
    __tablename__ = "student_photo"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True,doc="照片ID")
    sid = db.Column(db.Integer, db.ForeignKey("student.sid"), doc="学生ID")
    photo_data = db.Column(db.LargeBinary, nullable=False, doc="照片数据（人脸特征）")

class Course(db.Model):  # 修改后
    __tablename__ = "course"

    cid = db.Column("cid", db.Integer, primary_key=True,autoincrement=True,doc="课程ID")
    cname = db.Column("cname", db.String(255), nullable=False, doc="课程名称")
    cnumber = db.Column("cnumber",db.String(255), nullable=False, doc="课程编号")
    teacher_name = db.Column("teacher_name", db.String(255), nullable=False, doc="教师姓名")
    semester = db.Column("semester", db.String(255), nullable=False, doc="学期")
    credit = db.Column("credit",db.Integer,nullable=False, doc="学分")
    attendance_records = db.relationship('Attendance', backref='course')

class CourseSelection(db.Model):
    __tablename__ = "course_selection"

    id = db.Column(db.Integer, primary_key=True,autoincrement=True,doc="选课ID")
    sid = db.Column(db.Integer, db.ForeignKey("student.sid"), doc="学生ID")
    cid = db.Column(db.Integer, db.ForeignKey("course.cid"), doc="课程ID")

class Attendance(db.Model):
    __tablename__ = "attendance"

    id = db.Column(db.Integer, primary_key=True, doc="考勤ID")
    cid = db.Column(db.Integer, db.ForeignKey("course.cid"), doc="课程ID")
    sid = db.Column(db.Integer, db.ForeignKey("student.sid"), doc="学生ID")
    attendance_result = db.Column(db.Boolean, nullable=False, doc="考勤结果")
    attendance_time = db.Column(db.DateTime, nullable=False, doc="考勤时间")

# 用户密码账户 权限管理
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.Enum('admin', 'teacher'), nullable=False)
    name = db.Column(db.String(255), nullable=False)

    # 定义构造函数
    def __init__(self, username, password_hash, role,name):
        self.username = username
        self.password_hash = password_hash
        self.role = role
        self.name = name
    # 密码加密和验证
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


def get_student_name_by_sid(student_id):
    # 数据库查询来获取学生姓名
    result = db.session.query(Student).filter_by(sid=student_id).first()
    return result.sname if result else "Unknown"

def get_students_in_course(course_id):
    selections = CourseSelection.query.filter_by(cid=course_id).all()
    students = []
    for selection in selections:
        student = Student.query.get(selection.sid)  # 从 Student 表中获取对应的学生记录，并将其赋值给变量 student
        if student:
            students.append({
                'sid': student.sid,
                'sname': student.sname,
                'snumber': student.snumber
            })
    return students
def remove_student_from_course(student_id, course_id):
    selection = CourseSelection.query.filter_by(cid=course_id, sid=student_id).first()
    if selection:
        db.session.delete(selection)
        db.session.commit()
        return True
    return False

if __name__ == '__main__':
#第一种更新和创建数据库，这种会清空数据数据
    with flask_app.app_context():
        # db.drop_all()  # 删除表
        # db.create_all()
        # db.reflect()

    # 执行一个原生 SQL 命令来修改course表结构
    #     db.session.execute(text("ALTER TABLE course CHANGE start_time semester VARCHAR(20) NOT NULL;"))
    #     db.session.execute(text("ALTER TABLE course ADD COLUMN credit INT NOT NULL;"))
        db.session.execute(text("ALTER TABLE course MODIFY cnumber VARCHAR(255) NOT NULL;"))

        # 获取数据库中的所有数据表信息
        tables = db.metadata.tables.keys()
        print("数据库中的数据表：", tables)
