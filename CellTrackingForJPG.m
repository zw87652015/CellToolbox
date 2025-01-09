I = imread('cellphoto.jpg');
figure,imshow(I),title('Original Image');
text(size(I,2),size(I,1)+15, ...
    'Image of Cells', ...
    'FontSize',7,'HorizontalAlignment','right');
text(size(I,2),size(I,1)+25, ...
    'SUSTech', ...
    'FontSize',7,'HorizontalAlignment','right');
    
GrayImage = rgb2gray(I);
% figure,imshow(GrayImage),title('Gray Image');

%使用 edge 和 sobel 算子计算阈值。调整阈值，再次使用 edge 获得包含分割后的细胞的二值掩膜
[~,threshold] = edge(GrayImage,'sobel');
fudgeFactor = 0.5;
BWs = edge(GrayImage,'sobel',threshold * fudgeFactor);
%显示生成的二元梯度掩膜，显示图像中高对比度的线条
% figure,imshow(BWs,[]),title('Binary Gradient Mask');

%使用线性结构元素膨胀索贝尔图像，填充线条之间的间隙
se90 = strel('line',3,90);
se0 = strel('line',3,0);
BWsdil = imdilate(BWs,[se90 se0]);
% figure,imshow(BWsdil),title('Dilated Gradient Mask');

%使用 imfill 填充图像中的孔洞
BWdfill = imfill(BWsdil,'holes');
% figure,imshow(BWdfill),title('Binary Image with Filled Holes');

%使用 imclearborder 函数删除任何与图像边界连通的对象。要删除对角线连通，请将 imclearborder 函数中的连通性设置为 4。
BWnobord = imclearborder(BWdfill,4);
% figure,imshow(BWnobord),title('Cleared Border Image');

%最后，为了使分割后的对象看起来自然，用菱形结构元素对图像腐蚀9次来平滑处理对象。使用 strel 函数创建菱形结构元素。
seD = strel('diamond',1);
BWfinal = imerode(BWnobord,seD);
for i=2:9
    BWfinal = imerode(BWfinal,seD);
end
CC = bwconncomp(BWfinal);
% Filter out small objects if necessary
minCellSize = 60; % Example threshold, adjust as needed
BWfinal = bwareaopen(BWfinal, minCellSize);
% figure,imshow(BWfinal),title('Segmented Image');

%使用labeloverlay在原始图像上显示掩膜
% figure,imshow(labeloverlay(I,BWfinal)),title('Mask Over Original Image');

%显示分割后的对象的另一种方法是在分割的细胞周围绘制轮廓。使用 bwperim 函数绘制轮廓。
BWoutline = bwperim(BWfinal);
Segout = I; 
Segout(BWoutline) = 255; 
% figure,imshow(Segout),title('Outlined Original Image')

% Get properties of each cell region
stats = regionprops(BWfinal, 'Centroid', 'Area', 'PixelList');

% Create a new binary image for the extended circles
extendedImage = false(size(BWfinal));

% Open file to write circle information
fid = fopen(fullfile('processing', 'circle_info.txt'), 'w');
fprintf(fid, 'Cell\tCenter_X\tCenter_Y\tRadius\n');

% Process each cell
for i = 1:length(stats)
    % Get the cell's pixels
    pixels = stats(i).PixelList;
    centroid = stats(i).Centroid;
    
    % Calculate radius as the maximum distance from centroid to any pixel
    distances = sqrt(sum((pixels - centroid).^2, 2));
    radius = ceil(max(distances));
    
    % Create circle mask
    [xx, yy] = meshgrid(1:size(BWfinal,2), 1:size(BWfinal,1));
    circlemask = (xx - centroid(1)).^2 + (yy - centroid(2)).^2 <= radius^2;
    extendedImage = extendedImage | circlemask;
    
    % Write circle information to file
    fprintf(fid, '%d\t%.2f\t%.2f\t%.2f\n', i, centroid(1), centroid(2), radius);
end

fclose(fid);



%保存分割后的细胞
processingFolder = 'processing';
if ~exist(processingFolder, 'dir')
    mkdir(processingFolder);
end
imageFileName = fullfile(processingFolder, sprintf('1-GrayImage.png'));
imwrite(GrayImage, imageFileName);
imageFileName = fullfile(processingFolder, sprintf('2-BWs.png'));
imwrite(BWs, imageFileName);
imageFileName = fullfile(processingFolder, sprintf('3-BWsdil.png'));
imwrite(BWsdil, imageFileName);
imageFileName = fullfile(processingFolder, sprintf('4-BWdfill.png'));
imwrite(BWdfill, imageFileName);
imageFileName = fullfile(processingFolder, sprintf('5-BWnobord.png'));
imwrite(BWnobord, imageFileName);
imageFileName = fullfile(processingFolder, sprintf('6-BWfinal.png'));
imwrite(BWfinal, imageFileName);
imageFileName = fullfile(processingFolder, sprintf('7-LabelOverlay.png'));
imwrite(labeloverlay(I,BWfinal), imageFileName);
imageFileName = fullfile(processingFolder, sprintf('8-Segout.png'));
imwrite(Segout, imageFileName);
imageFileName = fullfile(processingFolder, '9-Extended.png');
imwrite(extendedImage, imageFileName);
overlayImage = labeloverlay(I, extendedImage, 'Transparency', 0.5);
imageFileName = fullfile(processingFolder, '10-ExtendedOverlay.png');
imwrite(overlayImage, imageFileName);