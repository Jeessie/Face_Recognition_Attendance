import cv2
import face_recognition

names = [
    "catherine",
    "william",
]

images = []
for name in names:
    filename = name + ".png"
    image = face_recognition.load_image_file("data/"+filename) #从图片中读取数据
    images.append(image)
unknown_image = face_recognition.load_image_file("one_person.png")

face_encodings = []
for image in images:
    encoding = face_recognition.face_encodings(image)[0] #将人脸的图像数据转换成128位向量
    face_encodings.append(encoding)
unknown_face_encodings = face_recognition.face_encodings(unknown_image)
print(face_encodings)
print(unknown_face_encodings)
print()

face_locations = face_recognition.face_locations(unknown_image) #face_locations存了每张脸的位置信息（为了调用cv2.rectangle）
for i in range(len(unknown_face_encodings)):
    unknown_encoding = unknown_face_encodings[i]
    face_location = face_locations[i]
    top, right, bottom, left = face_location
    cv2.rectangle(unknown_image, (left, top), (right, bottom), (0, 255, 0), 2) #调用cv2.rectangle框出了检测到的每张脸
    results = face_recognition.compare_faces(face_encodings, unknown_encoding)
    # face_recognition.compare_faces将已知人脸的128位向量和每张未知人脸的128位向量做比较，结果存入results数组中。
    # results数组中的每一个元素都是True或者False，长度和人脸个数相等。
    for j in range(len(results)):
        if results[j]:  # results中的每个元素都和已知人脸一一对应，在某一个位置处的元素为True，表示未知人脸被识别成这张已知人脸。
            name = names[j]
            cv2.putText(unknown_image, name, (left-10, top-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
            # 调用cv2.putText在图上标注标签
unknown_image_rgb = cv2.cvtColor(unknown_image, cv2.COLOR_BGR2RGB)

# 将图像大小调整为你想要的大小
new_width = 400  # 设置新的宽度
ratio = float(new_width) / unknown_image.shape[1]
new_height = int(unknown_image.shape[0] * ratio)
resized_image = cv2.resize(unknown_image, (new_width, new_height))

# 将图像从 BGR 转换为 RGB，因为 face_recognition 库的处理需要 RGB 格式的图像
resized_image_rgb = cv2.cvtColor(resized_image, cv2.COLOR_BGR2RGB)

# cv2.imshow("Output", unknown_image_rgb)
cv2.imshow("Output", resized_image_rgb)
cv2.waitKey(0)


# def face_recognition_show(img, names):  #  cv2.putText() 函数不支持 UTF-8 编码的文本，不能显示中文姓名
#     faces = app.get(img)
#
#     # 打印人脸数量
#     print("Found {} face(s) in this photograph.".format(len(faces)))
#
#     # 在图像上绘制边界框和名称
#     for face, name in zip(faces, names):
#         bbox = face.bbox.astype(int)
#         cv2.rectangle(img, (bbox[0], bbox[1]), (bbox[2], bbox[3]), (0, 0, 255), 4)
#         # 在边界框下方显示姓名
#         cv2.putText(img, name, (bbox[0], bbox[3] + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2, cv2.LINE_AA)
#
#     # 将BGR图像转换为RGB，因为Matplotlib显示的是RGB格式
#     img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
#
#     # 使用Matplotlib显示结果图像
#     plt.figure(figsize=(10, 10))  # 可以调整显示的图像大小
#     plt.imshow(img_rgb)
#     plt.subplots_adjust(top=0.85)  # 调整上边距
#     plt.text(0.01, 0.99, f"Found {len(faces)} face(s).", color='red', fontsize=12, backgroundcolor='None')
#     plt.title('Recognized Faces with Names')
#     plt.show()