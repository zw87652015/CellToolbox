Org = imread('Cellphoto.jpg');
% figure,imshow(Org),title('Original Image');
text(size(I,2),size(I,1)+15, ...
    'Image of Cells', ...
    'FontSize',7,'HorizontalAlignment','right');
text(size(I,2),size(I,1)+25, ...
    'SUSTech', ...
    'FontSize',7,'HorizontalAlignment','right');

hh = 2;

GrayImage = rgb2gray(Org);
% figure,imshow(GrayImage),title('Gray Image');

DoubleImage = im2double(GrayImage);
[m,n] = size(DoubleImage);
h = fspecial('gaussian', [3 3], 2);
DenoisedImage = imfilter(DoubleImage, h, 'replicate');
% figure,imshow(DenoisedImage),title('Denoised Image');

M = graythresh(Org(:,:,3));
BinaryImage = imbinarize(Org(:,:,3), M);
BinaryImage = ~BinaryImage;
% figure,imshow(BinaryImage),title('Binary Image');

% Canny Edge Detection
ROIedge_canny = edge(DenoisedImage,'canny', 0.3);
% figure,imshow(ROIedge_canny),title('Canny Edge Detection');

% Prewitt Edge Detection
ROIedge_prewitt = edge(DenoisedImage,'prewitt');
% figure,imshow(ROIedge_prewitt),title('Prewitt Edge Detection');

% Roberts Edge Detection
ROIedge_roberts = edge(DenoisedImage,'roberts');
% figure,imshow(ROIedge_roberts),title('Roberts Edge Detection');

% Sobel Edge Detection
ROIedge_sobel = edge(DenoisedImage,'sobel');
% figure,imshow(ROIedge_sobel),title('Sobel Edge Detection');

% Edge detection combination
ROIedge = ROIedge_canny | ROIedge_prewitt | ROIedge_roberts | ROIedge_sobel;
% figure,imshow(ROIedge),title('Edge Detection Combination');

% Kirsch segmentation
W{1,1} = [5,5,5;
          -3,0,-3;
          -3,-3,-3]; % Kirsch 1
W{1,2} = [5,5,-3;
          5,0,-3;
          -3,-3,-3]; % Kirsch 2
W{1,3} = [5,-3,-3;
          5,0,-3;
          5,-3,-3]; % Kirsch 3
W{1,4} = [-3,-3,-3;
          5,0,-3;
          5,5,-3]; % Kirsch 4
W{1,5} = [-3,-3,-3;
          -3,0,-3;
          5,5,5]; % Kirsch 5
W{1,6} = [-3,-3,-3;
          -3,0,5;
          -3,5,5]; % Kirsch 6
W{1,7} = [-3,-3,5;
          -3,0,5;
          -3,-3,5]; % Kirsch 7
W{1,8} = [-3,5,5;
          -3,0,5;
          -3,-3,-3]; % Kirsch 8
I = cell(1,8);  % Initialize I as a 1x8 cell array
for hh=1:8
    I{1,hh} = filter2(W{1,hh}, DenoisedImage);
    I{1,hh} = imbinarize(I{1,hh}, graythresh(I{1,hh}));
end

I9 = I{1,1} | I{1,2} | I{1,3} | I{1,4} | I{1,5} | I{1,6} | I{1,7} | I{1,8};
imageFileName = fullfile(processingFolder, sprintf('9-KirschSegmentation1.png'));
imwrite(I9, imageFileName);

se = strel('disk', 1);
I9 = imerode(I9, se);
I9 = imclose(I9, se);
imageFileName = fullfile(processingFolder, sprintf('10-KirschSegmentation2.png'));
imwrite(I9, imageFileName);

ROIseg = ROIedge | I9 | BinaryImage;
imageFileName = fullfile(processingFolder, sprintf('11-ROIedgeORI9ORBinary.png'));
imwrite(ROIseg, imageFileName);

se = strel('disk', 3);
Finalseg = imclose(ROIseg, se);
Finalseg = bwmorph(Finalseg, 'remove');
imageFileName = fullfile(processingFolder, sprintf('12-ClosingAndRemove.png'));
imwrite(Finalseg, imageFileName);

Finalseg = imfill(Finalseg, 4, 'holes');
imageFileName = fullfile(processingFolder, sprintf('13-HolesFilled.png'));
imwrite(Finalseg, imageFileName);

Finalseg = bwareaopen(Finalseg, 100);
imageFileName = fullfile(processingFolder, sprintf('14-SmallAreaRemoved.png'));
imwrite(Finalseg, imageFileName);

Finalseg = bwmorph(Finalseg, 'spur', 8);
imageFileName = fullfile(processingFolder, sprintf('15-SpursRemoved.png'));
imwrite(Finalseg, imageFileName);

Finalseg = bwmorph(Finalseg, 'clean');
imageFileName = fullfile(processingFolder, sprintf('16-Cleaned.png'));
imwrite(Finalseg, imageFileName);

[LabImage1, XNum] = bwlabeln(Finalseg, 4);
[m1, n1] = size(LabImage1);
stats = regionprops(LabImage1, 'all');
RGBX = label2rgb(LabImage1, @jet, 'k');
imageFileName = fullfile(processingFolder, sprintf('17-Labelled.png'));
imwrite(RGBX, imageFileName);

[L_BW,NUM] = bwlabel(Finalseg, 4);
imageFileName = fullfile(processingFolder, sprintf('18-L_BW.png'));
imwrite(L_BW, imageFileName);

stats = regionprops(L_BW, 'all');

figure;imshow(Org);
for i=1:NUM
    [r,c] = find(L_BW==i);
    S(i) = stats(i).Area;
    L(i) = stats(i).Perimeter;
    C(i) = (L(i)*L(i)) / (4 * pi * S(i));
    if 1000<S(i) && S(i)<5900
        if 100<L(i) && L(i)<300
            if 0.8<C(i) && C(i)<1.8
                rmin = min(r); rmax = max(r);
                cmin = min(c); cmax = max(c);
                w = cmax-cmin+1;
                h = rmax-rmin+1;
                hold on
                if (h>w && 1.5*w>h) || (w>h && 1.5*h>w) || (h==w)
                    rectangle('Position', [cmin rmin w h]);
                    drawnow;
                end
            end
        end
    end
end

% Save the extended circles image
processingFolder = 'processing';
if ~exist(processingFolder, 'dir')
    mkdir(processingFolder);
end
imageFileName = fullfile(processingFolder, sprintf('1-GrayImage.png'));
imwrite(GrayImage, imageFileName);
imageFileName = fullfile(processingFolder, sprintf('2-DenoisedImage.png'));
imwrite(DenoisedImage, imageFileName);
imageFileName = fullfile(processingFolder, sprintf('3-BinaryImage.png'));
imwrite(BinaryImage, imageFileName);

imageFileName = fullfile(processingFolder, sprintf('4-CannyEdgeDetection.png'));
imwrite(ROIedge_canny, imageFileName);
imageFileName = fullfile(processingFolder, sprintf('5-PrewittEdgeDetection.png'));
imwrite(ROIedge_prewitt, imageFileName);
imageFileName = fullfile(processingFolder, sprintf('6-RobertsEdgeDetection.png'));
imwrite(ROIedge_roberts, imageFileName);
imageFileName = fullfile(processingFolder, sprintf('7-SobelEdgeDetection.png'));
imwrite(ROIedge_sobel, imageFileName);
imageFileName = fullfile(processingFolder, sprintf('8-EdgeDetectionCombination.png'));
imwrite(ROIedge, imageFileName);