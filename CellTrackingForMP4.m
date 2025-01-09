% 读取视频文件
videoFile = 'cellvideo.mp4'; % 替换为你的视频文件路径
video = VideoReader(videoFile);

% 创建视频显示窗口
figure('Name', 'Cell Detection');
frameRate = video.FrameRate; % 获取视频帧率
frameInterval = 0.2; % 每 0.2 秒处理一帧
frameStep = round(frameRate * frameInterval); % 对应的帧步长

% 数据记录初始化
cellData = {}; % 用于保存细胞轮廓和中心点

frameIdx = 1; % 初始化帧计数器

% 遍历视频帧
while hasFrame(video)
    % 获取当前帧
    frame = readFrame(video);

    % 检查是否是要处理的帧
    if mod(frameIdx, frameStep) == 0
        % 图像预处理
        grayFrame = rgb2gray(frame); % 转为灰度图
        blurredFrame = imgaussfilt(grayFrame, 2); % 高斯滤波
        binaryFrame = imbinarize(blurredFrame, 'adaptive'); % 自适应二值化
        binaryFrame = imopen(binaryFrame, strel('disk', 3)); % 去噪（形态学开运算）

        % 细胞轮廓检测
        [boundaries, labels] = bwboundaries(binaryFrame, 'noholes'); % 获取轮廓

        % 初始化轮廓显示和中心点
        hold on;
        imshow(frame); % 显示当前帧
        for k = 1:length(boundaries)
            boundary = boundaries{k}; % 第 k 个轮廓
            plot(boundary(:,2), boundary(:,1), 'g', 'LineWidth', 1); % 绘制轮廓

            % 计算中心点
            stats = regionprops(labels, 'Centroid');
            centroid = stats(k).Centroid;
            plot(centroid(1), centroid(2), 'ro'); % 绘制中心点

            % 保存轮廓和中心点
            cellData{end+1} = struct('FrameIdx', frameIdx, ...
                                     'Boundary', boundary, ...
                                     'Centroid', centroid);
        end
        hold off;

        pause(0.1); % 控制显示速度
    end

    % 增加帧计数器
    frameIdx = frameIdx + 1;
end

% 保存数据到文件
save('cellData.mat', 'cellData');
disp('数据已保存到 cellData.mat');
