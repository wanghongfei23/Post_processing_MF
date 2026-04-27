import cv2
import os

# 获取当前脚本所在目录
script_dir = os.path.dirname(os.path.abspath(__file__))

# 遍历所有目录和子目录
for root, dirs, files in os.walk(script_dir):
    # 收集当前目录中的PNG文件
    png_files = sorted([os.path.join(root, f) for f in files if f.endswith('.png')])
    
    # 检查当前目录中是否存在MP4文件
    mp4_files = [f for f in files if f.endswith('.mp4')]
    
    # 如果存在PNG文件且不存在MP4文件，则生成视频
    if png_files and not mp4_files:
        print(f"处理目录: {root}")
        # 读取第一张图片获取尺寸
        first_image = cv2.imread(png_files[0])
        if first_image is None:
            print(f"无法读取第一张图片: {png_files[0]}")
            continue
        height, width, layers = first_image.shape
        
        # 定义视频编码器和输出视频
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')  # MP4格式
        fps = 10  # 帧率
        output_video_path = os.path.join(root, 'output_video.mp4')
        output_video = cv2.VideoWriter(output_video_path, fourcc, fps, (width, height))
        
        # 遍历所有图片并添加到视频中
        for png_file in png_files:
            image = cv2.imread(png_file)
            if image is None:
                print(f"无法读取图片: {png_file}")
                continue
            output_video.write(image)
            print(f"处理图片: {os.path.basename(png_file)}")
        
        # 释放资源
        output_video.release()
        print(f"视频生成完成: {output_video_path}")
    elif not png_files:
        # 没有PNG文件，跳过
        pass
    else:
        # 已存在MP4文件，跳过
        print(f"目录 {root} 中已存在MP4文件，跳过")
