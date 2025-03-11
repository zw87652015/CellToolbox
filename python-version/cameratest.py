import cv2
import os
from datetime import datetime

def read_usb_capture():
    # 选择摄像头的编号
    cap = cv2.VideoCapture(1)
    # 设置摄像头分辨率
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1024)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 576)
    
    # 获取实际的分辨率
    actual_width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
    actual_height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
    print(f"实际设置的分辨率: {actual_width}x{actual_height}")
    
    # 添加这句是可以用鼠标拖动弹出的窗体
    cv2.namedWindow('real_img', cv2.WINDOW_NORMAL)
    
    # 确保保存目录存在
    save_dir = os.path.join(os.path.dirname(__file__), 'camera-test')
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)
        
    print("按空格键拍照，按q键退出")
    
    while(cap.isOpened()):
        # 读取摄像头的画面
        ret, frame = cap.read()
        if ret:
            # 显示当前帧的大小
            height, width = frame.shape[:2]
            print(f"当前帧大小: {width}x{height}", end='\r')
            # 真实图
            cv2.imshow('real_img', frame)
            
            # 检测按键
            key = cv2.waitKey(1) & 0xFF
            # 按空格键拍照
            if key == ord(' '):
                # 生成文件名（使用时间戳）
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = os.path.join(save_dir, f'photo_{timestamp}.jpg')
                # 保存图片
                cv2.imwrite(filename, frame)
                print(f"\n照片已保存: {filename}")
            # 按q键退出
            elif key == ord('q'):
                break
                
    # 释放画面
    cap.release()
    cv2.destroyAllWindows()


if __name__ == '__main__':
    read_usb_capture()