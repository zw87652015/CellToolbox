I = imread('cellphoto.jpg');
figure,imshow(I),title('Original Image');
text(size(I,2),size(I,1)+15, ...
    'Image of Cells', ...
    'FontSize',7,'HorizontalAlignment','right');
text(size(I,2),size(I,1)+25, ....
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

%最后，为了使分割后的对象看起来自然，用菱形结构元素对图像腐蚀两次来平滑处理对象。使用 strel 函数创建菱形结构元素。
seD = strel('diamond',1);
BWfinal = imerode(BWnobord,seD);
imageFileName = fullfile(processingFolder, sprintf('BWfinal-ErosionTimes-1.png'));
imwrite(BWfinal, imageFileName);

for i=2:10
    BWfinal = imerode(BWfinal,seD);
    imageFileName = fullfile(processingFolder, sprintf('BWfinal-ErosionTimes-%d.png',i));
    imwrite(BWfinal, imageFileName);
end



