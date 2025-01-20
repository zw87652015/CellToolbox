import cv2

def read_usb_capture():
    # 选择摄像头的编号
    cap = cv2.VideoCapture(0)
    # 添加这句是可以用鼠标拖动弹出的窗体
    cv2.namedWindow('real_img', cv2.WINDOW_NORMAL)
    while(cap.isOpened()):
        # 读取摄像头的画面
        ret, frame = cap.read()
        # 真实图
        cv2.imshow('real_img', frame)
        # 按下'q'就退出
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    # 释放画面
    cap.release()
    cv2.destroyAllWindows()


if __name__ == '__main__':
    read_usb_capture()