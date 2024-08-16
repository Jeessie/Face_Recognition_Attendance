import cv2
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import matplotlib.pyplot as plt
from insightface.data import get_image as ins_get_image
import os
from sqlalchemy.orm import joinedload
from models import db, Student, StudentPhoto, Course, CourseSelection, flask_app, get_student_name_by_sid
from PIL import Image, ImageDraw, ImageFont

from insightface.app import FaceAnalysis

app = FaceAnalysis(providers=['CPUExecutionProvider'])
app.prepare(ctx_id=0, det_size=(640, 640))


# img = ins_get_image('images/few_faces.jpg')
# img = cv2.imread('images/few_faces.jpg')
# img = cv2.imread('images/few_faces2.jpg')
# img = cv2.imread("images/mid_faces.jpg")
# img = cv2.imread("images/mid+_faces.jpg")
# img = cv2.imread("images/large2.jpg")

def faces_embedding(img_path, flag=1):
    img = cv2.imread(img_path)
    # 获取图像中的人脸以及其他信息
    # 获取图像中的人脸以及其他信息
    faces = app.get(img)
    if flag == 0:  # flag==0 单人照片
        # 检查是否检测到人脸
        if len(faces) > 0:
            face = faces[0]  # 因为是单人照片，所以我们只处理第一个检测到的脸部
            if 'embedding' in face:
                # 提取特征向量
                feature_vector = face.embedding
                print("Feature vector extracted successfully.")
                # print(feature_vector)
                return feature_vector
            else:
                print("No embedding found for the face.")
                return None
        else:
            print("No face detected in the image.")
            return None

    else:  # flag==1 合照照片
        feature_vectors = []  # 特征向量列表
        # 对于图像中的每个脸部，提取特征
        for idx, face in enumerate(faces):
            # 可能还需要检查确保'embedding'在返回的结果里，如果app没有准备'recognition'，则可能不存在
            if 'embedding' in face:
                # 获取特征向量
                feature_vector = face.embedding
                feature_vectors.append(feature_vector)
                print(f"Feature vector for face {idx} (length {len(feature_vector)}):")
                print(feature_vector)

        return feature_vectors


def face_detection_show(img):
    faces = app.get(img)

    # 打印人脸数量
    print("Found {} face(s) in this photograph.".format(len(faces)))

    # 在图像上绘制边界框
    for face in faces:
        bbox = face.bbox.astype(int)
        cv2.rectangle(img, (bbox[0], bbox[1]), (bbox[2], bbox[3]), (0, 0, 255), 4)

    # 将BGR图像转换为RGB，因为Matplotlib显示的是RGB格式
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

    # 使用Matplotlib显示结果图像
    plt.figure(figsize=(10, 10))  # 可以调整显示的图像大小
    plt.imshow(img_rgb)
    # 在图像边缘增加空白区域以放置文本
    plt.subplots_adjust(top=0.85)  # 调整上边距
    plt.text(0.01, 0.99, f"Found {len(faces)} face(s).", color='red', fontsize=12, backgroundcolor='None')
    plt.title('Detected Faces_insightface')
    plt.show()

    # 保存图像，如果需要保存为BGR格式的图像，无需转换颜色
    # cv2.imwrite('output_image.jpg', img)


def get_all_face_embeddings(course_cid):
    # # 查询课程
    # course = Course.query.filter_by(cname=course_name, semester=semester).first()
    # if not course:
    #     print("Course not found")
    #     return None, None

    # 使用join加载所有选了这门课的学生的人脸特征
    students = (db.session.query(Student)
                .join(CourseSelection, Student.sid == CourseSelection.sid)
                .join(StudentPhoto, Student.sid == StudentPhoto.sid)
                .filter(CourseSelection.cid == course_cid)
                .options(joinedload(Student.photos))
                .all())
    # # 根据课程ID[cid唯一]查询选课记录，获取所有选了这门课的学生ID
    # selections = CourseSelection.query.filter_by(cid=course.cid).all()
    # student_ids = [selection.sid for selection in selections]

    face_embeddings = []
    student_ids = []
    # 查询这些学生的人脸特征向量
    for student in students:
        student_ids.append(student.sid)
        for photo in student.photos:
            if photo.photo_data:  # 读取二进制存储的数据
                feature_vector = np.frombuffer(photo.photo_data, dtype=np.float32)
                face_embeddings.append(feature_vector)

    return np.array(face_embeddings), student_ids
    # # 查询这些学生的人脸特征向量
    # face_embeddings = []
    # student_photos = StudentPhoto.query.filter(StudentPhoto.sid.in_(student_ids)).all()
    #
    # for photo in student_photos:
    #     if photo.photo_data:
    #         # 确保 photo_data正确解码为 numpy数组
    #         feature_vector = np.frombuffer(photo.photo_data, dtype=np.float32)
    #         face_embeddings.append(feature_vector)

    # return np.array(face_embeddings), student_ids, course.cid  # 返回一个numpy数组，其中包含所有特征向量+学生ID列表


# db_embeddings 是从数据库加载的所有已注册特征向量的列表
# face_embedding 是从实时图像中提取的单个人脸特征向量
def find_matching_identities(face_embeddings, db_embeddings, student_ids, threshold=0.4):
    if np.array(face_embeddings).ndim == 1:
        face_embeddings = face_embeddings.reshape(1, -1)  # 调整形状以匹配
    similarities = cosine_similarity(face_embeddings, db_embeddings)  # 余弦相似度
    matched_sid = []
    for similarity in similarities:
        max_similarity = np.max(similarity)
        if max_similarity > threshold:
            matched_index = np.argmax(similarity)
            matched_sid.append(student_ids[matched_index])  # 将匹配的学生ID添加到列表中
        else:
            matched_sid.append(-1)  # 没有找到足够相似的匹配，返回-1

    return matched_sid  # 返回一个包含所有匹配结果的列表


def face_recognition_show(img_path, names, save_image=False):
    # 打开图像文件
    image = Image.open(img_path)
    draw = ImageDraw.Draw(image)
    faces = app.get(cv2.imread(img_path))

    # 设置中文字体和字体大小（确保有这个字体文件）
    font_path = "simsun.ttc"

    # 在图像上绘制边界框和名称
    for face, name in zip(faces, names):
        bbox = face.bbox.astype(int)
        # 绘制边界框
        draw.rectangle([bbox[0], bbox[1], bbox[2], bbox[3]], outline='red', width=4)
        # 在边界框下方显示姓名
        if name == "Unknown":
            font = ImageFont.truetype(font_path, size=20)  # 字体大小
        else:
            font = ImageFont.truetype(font_path, size=50)  # 字体大小
        draw.text((bbox[0], bbox[3] + 20), name, fill=(0, 255, 0), font=font)
    # 显示图像
    image.show()
    # 如果设置为保存图像
    if save_image:
        # 生成新的文件名
        base_name = os.path.basename(img_path)
        name_part, ext_part = os.path.splitext(base_name)
        new_filename = f"{name_part}_processed2{ext_part}"
        new_path = os.path.join(os.path.dirname(img_path), new_filename)
        # 保存图像
        image.save(new_path)
        print(f"Image saved as {new_filename}")


if __name__ == "__main__":
    file_path = "images/test2.jpg"
    # file_path = "images/unknown.png"
    if os.path.exists(file_path):
        face_vectors = faces_embedding(file_path)
        course_name = '机器学习'
        # print(face_vector)
        with flask_app.app_context():
            # 使用该函数识别人脸
            face_embeddings, student_ids = get_all_face_embeddings(course_cid=1)
            matched_sid = find_matching_identities(face_vectors, face_embeddings, student_ids)
            print(matched_sid)
            names = [get_student_name_by_sid(sid) for sid in matched_sid]
            face_recognition_show(file_path, names, save_image=True)
            # if matched_index != -1:
            #     print(f"Matched with sid: {student_ids[matched_index]}")
            # else:
            #     print("No match found.")
    else:
        print("no file")
