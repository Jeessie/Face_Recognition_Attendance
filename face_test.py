import face_recognition
import matplotlib.pyplot as plt
import matplotlib.patches as patches

# 加载图像
# image = face_recognition.load_image_file("images/few_faces2.jpg")
# image = face_recognition.load_image_file("images/mid+_faces.jpg")
image = face_recognition.load_image_file("images/large2.jpg")

# 使用默认的HOG模型进行人脸检测
face_locations = face_recognition.face_locations(image)

# 打印人脸位置
print("Found {} face(s) in this photograph.".format(len(face_locations)))

# 创建显示图像的窗口
fig, ax = plt.subplots(figsize=(10, 10))
ax.imshow(image)

# 在图像上画出每个人脸的框
for face_location in face_locations:
    top, right, bottom, left = face_location
    # 创建一个矩形框
    rect = patches.Rectangle((left, top), right - left, bottom - top, linewidth=1, edgecolor='r', facecolor='none')
    # 将矩形框添加到图像中
    ax.add_patch(rect)

plt.text(0.01, 0.99,f"Found {len(face_locations)} face(s).", color='red', fontsize=12, backgroundcolor='None')
plt.title('Detected Faces_recognition')
# 显示图像
plt.show()




