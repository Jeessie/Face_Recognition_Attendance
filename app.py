from flask import render_template, request, session, redirect, url_for, jsonify, flash
from flask_sqlalchemy.session import Session
from sqlalchemy import func
from sqlalchemy.orm import joinedload
from werkzeug.utils import secure_filename
import os
import pickle
from sqlalchemy.orm import scoped_session, sessionmaker
import pandas as pd

from Get_data import insert_student_and_Photo, insert_Course, insert_CourseSelection, import_CourseSelection
from insight_recognition import faces_embedding
from models import flask_app, Course, User, db, get_student_name_by_sid, Attendance, Student, StudentPhoto, \
    remove_student_from_course, get_students_in_course, CourseSelection
from Get_attendance_result import get_recognized_result, record_attendance, get_absent_students
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash

login_manager = LoginManager()
login_manager.init_app(flask_app)
login_manager.login_view = 'login'
# 配置会话管理
# db_session = scoped_session(sessionmaker(bind=db.engine))

# 用户加载函数
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# 路由：登录页面
@flask_app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            # 根据用户角色重定向到不同的首页
            if user.role == 'admin':
                return redirect(url_for('admin_dashboard'))
            elif user.role == 'teacher':
                return redirect(url_for('teacher_dashboard'))
            else:
                flash('Invalid user role.')
                return redirect(url_for('login'))
        else:
            flash('Invalid username or password')
    return render_template('login.html')


# 路由：注册页面
@flask_app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role = request.form['role']
        name = request.form['name']

        # 检查用户名是否已被占用
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Username already taken')
            return redirect(url_for('register'))  # 这里做重定向

        # 创建新用户并存储到数据库
        new_user = User(username=username, password_hash=generate_password_hash(password), role=role, name=name)
        db.session.add(new_user)
        db.session.commit()
        flash('Registration successful! Redirecting to login...')
        return redirect(url_for('login'))  # 成功后重定向到登录页面
    return render_template('register.html')


# 路由：登出页面
@flask_app.route('/logout')
@login_required
def logout():
    logout_user()  # 清除用户的登录会话
    return redirect(url_for('login'))  # 重定向到登录页面


# 定义首页路由
@flask_app.route('/')
def index():
    return render_template('index.html')

# 路由：管理员页面
@flask_app.route('/admin_dashboard')
@login_required
def admin_dashboard():
    students = Student.query.options(joinedload(Student.photos)).all() # 获取所有学生信息
    return render_template('admin_dashboard.html',students=students)  # 显示管理员专用的首页界面

@flask_app.route('/update_student_photo', methods=['POST'])
def update_student_photo():
    sid = request.form['sid']
    if 'photo' not in request.files:
        return jsonify(success=False, error="No file part")

    file = request.files['photo']
    if file.filename == '':
        return jsonify(success=False, error="No selected file")

    if file:
        filename = secure_filename(file.filename)
        file_path = os.path.join(flask_app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)

        # 提取人脸特征
        feature_vector = faces_embedding(file_path, 0)
        if feature_vector is not None:
            serialized_vector = pickle.dumps(feature_vector)

            # 查找并更新学生照片数据
            student_photo = StudentPhoto.query.filter_by(sid=sid).first()
            if student_photo:
                student_photo.photo_data = serialized_vector
                db.session.commit()
                print("success")
                return jsonify(success=True)
            else:
                return jsonify(success=False, error="Student photo not found")
        else:
            return jsonify(success=False, error="Failed to extract features from photo")

    return jsonify(success=False, error="File upload failed")

@flask_app.route('/add_student', methods=['GET', 'POST'])  # 学生信息
@login_required
def add_student():
    if request.method == 'POST':
        sname = request.form['sname']
        snumber = request.form['snumber']
        sclass = request.form['sclass']
        if 'photo' in request.files:
            file = request.files['photo']
            if file.filename == '':
                flash('No selected file')
                return redirect(request.url)
            filename = secure_filename(file.filename)
            save_path = os.path.join(flask_app.config['UPLOAD_FOLDER'], filename)
            file.save(save_path)

            # Create a new course instance and add it to the database
            insert_student_and_Photo(sna=sname,snum=snumber,scl=sclass,stu_pic=save_path,commit=True)
            # 成功后
            return jsonify({'success': True})
    # 如果有错误
    return jsonify({'success': False, 'error': 'Detailed error message'})

@flask_app.route('/delete_student/<int:sid>', methods=['DELETE'])
def delete_student(sid):
    try:
        student = Student.query.get(sid)
        if student:
            # 删除学生照片
            StudentPhoto.query.filter_by(sid=sid).delete()
            CourseSelection.query.filter_by(sid=sid).delete()
            Attendance.query.filter_by(sid=sid).delete()
            # 删除学生记录
            db.session.delete(student)
            db.session.commit()
            return jsonify(success=True)
        else:
            return jsonify(success=False, error="Student not found")
    except Exception as e:
        db.session.rollback()
        return jsonify(success=False, error=str(e))


# 路由：教师页面
@flask_app.route('/teacher_dashboard')
@login_required
def teacher_dashboard():
    courses = Course.query.all()  # 获取所有课程
    return render_template('teacher_dashboard.html', courses=courses)  # 显示教师专用的首页界面


@flask_app.route('/register_course', methods=['GET', 'POST'])  # 教师注册课程
@login_required
def register_course():
    if request.method == 'POST':
        cname = request.form['cname']
        cnumber = request.form['cnumber']
        teacher_name = request.form['teacher_name']
        semester = request.form['semester']
        credit = int(request.form['credit'])

        # Create a new course instance and add it to the database
        insert_Course(cna=cname, cnum=cnumber, tn=teacher_name, sem=semester, cred=credit, commit=True)
        # 假设成功后
        return jsonify({'success': True})
    # 如果有错误
    return jsonify({'success': False, 'error': 'Detailed error message'})


@flask_app.route('/mycourse')
@login_required
def mycourse():
    # print("Current user:", current_user.name)  # 打印当前用户名称
    mycourses = Course.query.filter_by(teacher_name=current_user.name).all()
    print("Courses found:", len(mycourses))  # 打印找到的课程数量
    if request.args.get('format') == 'json':
        courses_data = [{'id': course.cid, 'name': course.cname, 'semester': course.semester} for course in mycourses]
        return jsonify(courses_data)
    return render_template('mycourse.html', mycourses=mycourses)

@flask_app.route('/upload_students/<int:course_id>', methods=['POST'])
@login_required
def upload_students(course_id):
    if 'studentFile' in request.files and request.files['studentFile'].filename!='':
        category = 'danger'
        file = request.files['studentFile']
        if file and file.filename.endswith('.xlsx'):
            import_CourseSelection(file, course_id)
            message = "学生文件上传成功"
            category = "success"
        else:
            message = "请上传一个有效的 .xlsx 文件"
        return redirect(url_for('mycourse', message=message, category=category))
    elif 'studentName' in request.form and 'studentId' in request.form:
        student_name = request.form['studentName']  # 学生姓名
        student_number = request.form['studentId']  # 学生学号
        category = 'danger'
        if student_name !='' and student_number!='':
            print(student_name,student_number)
            Flag = insert_CourseSelection(student_name, student_number, course_id, commit=True)  # 插入选课学生信息
            if not Flag:
                message = "学生不存在"
            else:
                message = "学生添加成功"
                category = "success"
            return redirect(url_for('mycourse', message=message, category=category))
    return redirect(url_for('mycourse',message = "请提供学生信息或上传文件"))


@flask_app.route('/manage_course/<int:course_id>', methods=['GET', 'POST'])
@login_required
def manage_course(course_id):
    if request.method == 'POST':
        data = request.get_json()
        # student_id = request.form.get('student_id')
        student_id = data.get('student_id')
        flask_app.logger.debug(f'Received student_id: {student_id}')
        if student_id:
            # remove_student_from_course(student_id, course_id)
            # message = "学生删除成功"
            # category = "success"
            # return redirect(url_for('manage_course', course_id=course_id, message=message, category=category))
            if remove_student_from_course(student_id, course_id):
                return jsonify({"success": True, "message": "学生删除成功"})
            else:
                return jsonify({"success": False, "message": "学生删除失败"})
    students = get_students_in_course(course_id)
    # return render_template('manage_course.html', course_id=course_id, students=students)
    return jsonify({"students": students})


# 路由：考勤结果页面
@flask_app.route('/attendance')
@login_required
def attendance():
    return render_template('attendance.html')


@flask_app.route('/get_absent_students')
@login_required
def get_absent_students_api():
    if 'course_id' and 'current_time' in session:
        course_id = session.get('course_id')
        current_time = session['current_time']
        absent_students = get_absent_students(course_id, current_time)
        print("absent_students: ", absent_students)
        return jsonify(absent_students)
    return jsonify([])  # 如果没有数据，返回空列表


@flask_app.route('/upload_photo', methods=['POST'])
@login_required
def upload_photo():
    course_cid = request.form.get('course_name')
    session['course_id'] = course_cid

    if 'photo' in request.files:
        # Initialize session data if not already done
        if 'recognized_ids' not in session:
            session['recognized_ids'] = []
        photos = request.files.getlist('photo')
        for photo in photos:
            if photo.filename:
                filename = secure_filename(photo.filename)
                save_path = os.path.join(flask_app.config['UPLOAD_FOLDER'], filename)
                photo.save(save_path)
                # Perform face recognition and store recognized IDs
                recognized_ids = get_recognized_result(save_path, course_cid)
                session['recognized_ids'].extend(recognized_ids)
                print("Current session['recognized_ids']:", session['recognized_ids'])
        return jsonify({'message': f'{len(photos)} photos uploaded successfully'})
    return 'No photo uploaded'


@flask_app.route('/submit_attendance', methods=['POST'])
@login_required
def submit_attendance():
    if 'recognized_ids' in session and 'course_id' in session:
        current_time = record_attendance(session['recognized_ids'], session['course_id'])
        session['current_time'] = current_time  # 将考勤时间存储到session
        session.pop('recognized_ids', None)  # Clear the session after recording attendance
        return jsonify({'message': 'Attendance recorded successfully!'})
    return jsonify({'message': 'No data to submit'}), 400


@flask_app.route('/attendance_management')
@login_required
def attendance_management():
    mycourses = Course.query.options(joinedload(Course.attendance_records)).filter_by(
        teacher_name=current_user.name).all()
    # 组织数据
    results = []
    courses = []
    for course in mycourses:
        courses.append({
            'course_id': course.cid,
            'course_name': course.cname,
            'semester': course.semester
        })
        for attendance in course.attendance_records:
            flask_app.logger.debug(f'Attendance Record: {attendance}')  # 添加调试日志
            results.append({
                'id': attendance.id,  # 添加考勤记录的ID
                'course_name': course.cname,
                'student_name': get_student_name_by_sid(attendance.sid),
                'attendance_result': attendance.attendance_result,
                'attendance_time': attendance.attendance_time.strftime("%Y-%m-%d %H:%M:%S")  # 格式化时间
            })

    return render_template('attendance_management.html', results=results, courses=courses)



@flask_app.route('/modify_attendance', methods=['POST'])
@login_required
def modify_attendance():
    data = request.get_json()
    attendance_id = data.get('attendance_id')
    attendance_result = data.get('attendance_result') == 'true'

    flask_app.logger.debug(f'Attendance ID: {attendance_id}')
    flask_app.logger.debug(f'Attendance Result: {attendance_result}')
    attendance = db.session.get(Attendance, attendance_id)
    if attendance:
        attendance.attendance_result = attendance_result
        db.session.commit()
        return jsonify({"success": True, "message": "考勤记录修改成功"})
    return jsonify({"success": False, "message": "考勤记录修改失败"})

@flask_app.route('/delete_attendance/<int:attendance_id>', methods=['POST'])
@login_required
def delete_attendance(attendance_id):
    attendance = db.session.get(Attendance, attendance_id)
    if attendance:
        db.session.delete(attendance)
        db.session.commit()
        return jsonify({"success": True, "message": "考勤记录删除成功"})
    return jsonify({"success": False, "message": "考勤记录删除失败"})



@flask_app.route('/api/attendance_counts/<int:course_id>')
def get_attendance_counts(course_id):
    # 查询指定课程的每个考勤时间的出勤人数
    attendance_data = db.session.query(
        Attendance.attendance_time, func.count(Attendance.id).label('count')
    ).filter(
        Attendance.cid == course_id,
        Attendance.attendance_result == True  # 假设attendance_result为True表示出勤
    ).group_by(
        Attendance.attendance_time
    ).order_by(
        Attendance.attendance_time
    ).all()

    # 格式化查询结果为字典列表
    results = [{
        'time': attendance_time.strftime("%Y-%m-%d %H:%M:%S"),
        'count': count
    } for attendance_time, count in attendance_data]

    return jsonify(results)


if __name__ == '__main__':
    flask_app.run(debug=True)
    # import os
    # print("Current working directory:", os.getcwd())
    # recognized_student_ids, course_id = get_recognized_result()
    # absent_stus = record_attendance(recognized_student_ids, course_id, submit=True)
    # attendance_results = [absent_stu.sname for absent_stu in absent_stus]
    # print(attendance_results)
