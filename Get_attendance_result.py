# Get_attendance_result.py
import os
from sqlalchemy import text
from datetime import datetime
from models import db, flask_app,Student, StudentPhoto, Course, CourseSelection,Attendance,get_student_name_by_sid
from insight_recognition import find_matching_identities,faces_embedding,get_all_face_embeddings,face_recognition_show
# matched_sid = find_matching_identities(face_vectors, face_embeddings, student_ids)
# file_path = "images/few_faces.jpg"

def get_recognized_result(file_path,course_cid):
    if os.path.exists(file_path):
        face_vectors = faces_embedding(file_path)
        # print(face_vector)
        # 查询选课学生
        face_embeddings, student_ids = get_all_face_embeddings(course_cid)
        # 匹配人脸
        matched_sid = find_matching_identities(face_vectors, face_embeddings, student_ids)
        # print(matched_sid)
        # names = [get_student_name_by_sid(sid) for sid in matched_sid]
        # face_recognition_show(file_path, names, save_image=False)
        return matched_sid
    else:
        print("no file")
        return None


def record_attendance(recognized_student_ids,course_id):
    # 获取当前时间作为考勤时间
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # 查询该课程的所有学生
    students_in_course = db.session.query(Student).join(CourseSelection, Student.sid == CourseSelection.sid).filter(CourseSelection.cid == course_id).all()
    student_map = {student.sid: student for student in students_in_course}

    # 首先为所有学生创建缺勤记录
    attendance_records = [
        Attendance(cid=course_id,
                   sid=student.sid,
                   attendance_result=False,
                   attendance_time=current_time)
        for student in students_in_course
    ]

    # 根据人脸识别结果更新出勤状态
    for recognized_id in recognized_student_ids:
        if recognized_id in student_map:
            student_record = next((record for record in attendance_records if record.sid == recognized_id), None)
            if student_record:
                student_record.attendance_result = True

    # 一次性批量插入或更新数据库中的对象列表
    db.session.bulk_save_objects(attendance_records)
    db.session.commit()
    print("Attendance update successfully.")
    return current_time

    # if submit:
    #     absent_list = get_absent_students(course_id, current_time)
    #     # print(f"本课共缺勤 {len(absent_list)}人:")
    #     # for stu in absent_list:
    #     #     print(stu.sname)
    #     return absent_list

def get_absent_students(course_id,current_time):
    if current_time:
        absent_students = db.session.query(Student.sname).join(Attendance, Student.sid == Attendance.sid).filter(
            Attendance.cid == course_id,
            Attendance.attendance_result == False,
            Attendance.attendance_time == current_time
        ).all()
        return [student.sname for student in absent_students]
    return []

# def update_attendance(recognized_id,course_id,current_time_str,commit = False):
#     # 查找对应学生的考勤记录并更新
#     if recognized_id != -1:
#         # print(recognized_id)
#         attendance_record = db.session.query(Attendance).filter_by(cid=course_id, sid=recognized_id,
#                                                                    attendance_time=current_time_str).one()
#         attendance_record.attendance_result = True  # 标记为出勤
#
#         if commit:
#             try:
#                 db.session.commit()
#                 print("Attendance update successfully.")
#             except Exception as e:
#                 db.session.rollback()
#                 print(f"Failed to insert attendance: {e}")

if __name__ == "__main__":
    with flask_app.app_context():
        # # 清空 attendance 表
        # db.session.execute(text('DELETE FROM attendance'))
        # db.session.execute(text('ALTER TABLE attendance AUTO_INCREMENT = 1'))
        # db.session.commit()
        recognized_student_ids = get_recognized_result(file_path="images/few_faces.jpg",course_cid= 1)
        record_attendance(recognized_student_ids,1)
