# Face-Recognition
Developed an intelligent attendance management system using face recognition technology to identify students in group photos, logging absentee names and syncing data to a database. It utilizes MySql to store data, employs Flask framework, and uses InsightFace for face detection and recognition, allowing administrators and teachers in universities to manage class attendance conveniently through login for operations

* 系统主页
<img width="416" alt="image" src="https://github.com/user-attachments/assets/cf2f384a-89f3-402c-9938-441c0303bcd0"></br>
* 课程管理模块</br>
<img width="416" alt="image" src="https://github.com/user-attachments/assets/db474c0b-6378-4047-9fd1-29911d6760b6"><img width="414" alt="image" src="https://github.com/user-attachments/assets/2171f881-4e29-4278-8762-8bc49a2fe7e8"></br>
* 选课管理模块</br>
<img width="416" alt="image" src="https://github.com/user-attachments/assets/03324a74-20c2-4286-979b-051c1bea7b81"><img width="416" alt="image" src="https://github.com/user-attachments/assets/a14856c6-add4-4cfd-888f-9acd774e9c2b"></br>
* 拍照考勤&考勤管理模块</br>
<img width="416" alt="image" src="https://github.com/user-attachments/assets/1f94c1f1-a4c9-472c-a036-d90c68401c14"><img width="416" alt="image" src="https://github.com/user-attachments/assets/41353768-e505-41ae-a8d0-264536575da8"><img width="414" alt="image" src="https://github.com/user-attachments/assets/dfcf1ee7-e5d7-4d98-b1d7-59e09ebeaa28"></br>
* 管理员信息管理模块</br>
<img width="416" alt="image" src="https://github.com/user-attachments/assets/66396c16-a549-4312-b696-3661202c3115"><img width="413" alt="image" src="https://github.com/user-attachments/assets/ec24bcbb-9cc1-4cb2-b33d-036de443b247"></br>

# Environment
* python 3.9
* numpy 1.26.4
* MySQL 5.7
* flask-3.0.3.dist-info, flask_sqlalchemy-3.1.1.dist-info
* insightface 0.7.3
* opencv-python-headless 4.9.0.80, openpyxl 3.1.2, openssl 3.0.13
      
# File Introduction
* .py--程序code文件
  * models.py 实现Flask框架的配置，利用SQLAlchemy连接Mysql数据库，利用封装的ORM实现数据表设计的结构，以及对数据表的查询
  * app.py 包含所有的路由函数，实现前后端的数据传输和交互
  * insight_recognition.py 提取照片的人脸特征，实现人脸识别
  * Get_data.py 处理单条或批量的输入数据，将数据按数据表格式提交到数据库
  * Get_attendance_result.py 根据人脸识别结果，得到考勤结果，并记录到数据库中
  * 其余的py后缀文件均为测试文件
* templates 前端网页的html文件
* static 网页格式设置
* Upload_images/images 均为用于测试的合照（上传至前端网页的借口）

# Running
* 运行app.py,点击网页进入系统
<img width="741" alt="1731422786635" src="https://github.com/user-attachments/assets/59357214-bf5f-49ef-83c5-7d69e72b3178">
