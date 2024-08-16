# Get_data.py
import pandas as pd
import os
import pickle
from models import db, Student, StudentPhoto, Course, CourseSelection, flask_app
from insight_recognition import faces_embedding
from sqlalchemy import text

stu_file = '../学生信息收集.xlsx'
pic_path = '../stu_imgs'
course_file = '../课程信息.xlsx'
class_selection_file = '../选课学生名单.xlsx'

stu_error_list = []  # 存储无法检测到人脸的图片信息

def insert_student_and_Photo(sna,snum,scl,stu_pic,commit=False):
    # 单独增加信息
    student = Student(
        sname=sna,
        snumber=snum,
        sclass=scl,
    )
    # 添加到数据库会话
    db.session.add(student)
    db.session.flush()  # 这将提供student实例的自动生成的ID

    # 读取照片文件
    photo_path = os.path.join(pic_path, stu_pic)
    if os.path.exists(photo_path):
        # with open(photo_path, 'rb') as photo_file:
        #     photo_data = photo_file.read()
        feature_vector = faces_embedding(photo_path, 0)  # 直接存储人脸特征向量
        if feature_vector is not None:
            # 序列化特征向量
            serialized_vector = pickle.dumps(feature_vector)
            student_photo = StudentPhoto(
                sid=student.sid,
                photo_data=serialized_vector
            )
            db.session.add(student_photo)
        else:
            print(f"Failed to extract feature from photo {stu_pic}")
            stu_error_list.append({'sid': student.sid, 'photo': photo_path, 'snumber': snum})
            # 方便后续处理错误图片--不能检测到人脸
    else:
        print(f'Photo {stu_pic} not found.')
        stu_error_list.append({'sid': student.sid, 'photo': photo_path, 'snumber': snum})
        # 处理无对应图片的错误

    # 单独提交会话
    if commit:
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            print(f"Error committing to database: {e}")

def import_students_and_Photos(file_path):
    # 读取Excel文件
    df = pd.read_excel(file_path, engine='openpyxl')
    # print(df)
    # 遍历DataFrame中的每一行
    for index, row in df.iterrows():
        insert_student_and_Photo(row['name'],row['number'], row['class'], row['photo'])

    # 批次提交会话
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Error committing to database: {e}")

    # 打印错误列表
    if stu_error_list:
        print("Errors encountered with the following photos:")
        for error in stu_error_list:
            print(error)

def insert_Course(cna,cnum,tn,sem,cred,commit=False):
    # 单独：
    # 创建Course实例
    course = Course(
        cname=cna,
        cnumber=cnum,
        teacher_name=tn,
        semester=sem,
        credit = cred
    )
    # 添加到数据库会话
    db.session.add(course)
    db.session.flush()  # 这将提供course实例的自动生成的ID

    # 单独提交会话
    if commit:
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            print(f"Error committing to database: {e}")

def import_Course(file_path):
    # 读取Excel文件
    df = pd.read_excel(file_path, engine='openpyxl')
    # print(df)
    # 遍历DataFrame中的每一行
    for index, row in df.iterrows():
        insert_Course(row['course_name'],row['course_number'],row['teacher_name'], row['semester'], row['credit'])

    # 批次提交会话
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Error committing to database: {e}")

def insert_CourseSelection(student_name, student_number, course_id,commit = False):
    # 查询学生ID(sid)
    student = Student.query.filter_by(sname=student_name, snumber=student_number).first()
    if not student:
        print(f"No student found for {student_name} with number {student_number}")
        return False
    # # 查询课程ID(cid)
    # course = Course.query.filter_by(cname=course_name,semester = seme).first()
    # if not course:
    #     print(f"No course found with name {course_name}")
    #     return False

    # 创建选课记录
    new_selection = CourseSelection(sid=student.sid, cid=course_id)
    db.session.add(new_selection)
    if commit:
        try:
            db.session.commit()
            print("Course selection added successfully.")
        except Exception as e:
            db.session.rollback()
            print(f"Failed to insert course selection: {e}")
    return True

def import_CourseSelection(file_path,course_id):
    # 读取Excel文件
    df = pd.read_excel(file_path, engine='openpyxl')
    # 遍历DataFrame中的每一行
    for index, row in df.iterrows():
        insert_CourseSelection(row['name'], row['number'], course_id)

    # 批次提交会话
    try:
        db.session.commit()
        print("Course selection added successfully.")
    except Exception as e:
        db.session.rollback()
        print(f"Error committing to database: {e}")

def import_Attendance():
    return


if __name__ == "__main__":
    with flask_app.app_context():
        # # 清空 student 表
        # db.session.execute(text('DELETE FROM course'))
        # # 清空学生表
        # db.session.execute(text('ALTER TABLE course AUTO_INCREMENT = 1'))
        # db.session.commit()

    # 导入数据：
        #import_students_and_Photos(stu_file)  # 批量导入学生信息
        # import_Course(course_file)
        import_CourseSelection(class_selection_file, '机器学习', '2023-2024-下')
