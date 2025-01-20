function DetectButtonPushed(app, event)
            frame = app.frameForDetect;
            hh = 2;
            GrayImage = rgb2gray(frame);
            DoubleImage = im2double(GrayImage);
            h = fspecial('gaussian', [3 3], 2);
            DenoisedImage = imfilter(DoubleImage, h, 'replicate');
            M = graythresh(frame(:,:,3));
            BinaryImage = imbinarize(frame(:,:,3), M);
            BinaryImage = ~BinaryImage;
            ROIedge_canny = edge(DenoisedImage,'canny', 0.3);
            ROIedge_prewitt = edge(DenoisedImage,'prewitt');
            ROIedge_roberts = edge(DenoisedImage,'roberts');
            ROIedge_sobel = edge(DenoisedImage,'sobel');
            ROIedge = ROIedge_canny | ROIedge_prewitt | ROIedge_roberts | ROIedge_sobel;
            I = cell(1,8);
            for hh=1:8
                I{1,hh} = filter2(app.W{1,hh}, DenoisedImage);
                I{1,hh} = imbinarize(I{1,hh}, graythresh(I{1,hh}));
            end
            I9 = I{1,1} | I{1,2} | I{1,3} | I{1,4} | I{1,5} | I{1,6} | I{1,7} | I{1,8};
            I9 = imerode(I9, app.se1);
            I9 = imclose(I9, app.se1);
            ROIseg = ROIedge | I9 | BinaryImage;
            Finalseg = imclose(ROIseg, app.se2);
            Finalseg = bwmorph(Finalseg, 'remove');
            Finalseg = imfill(Finalseg, 4, 'holes');
            Finalseg = bwareaopen(Finalseg, 100);
            Finalseg = bwmorph(Finalseg, 'spur', 8);
            Finalseg = bwmorph(Finalseg, 'clean');
            [L_BW,NUM] = bwlabel(Finalseg, 4);
            stats = regionprops(L_BW, 'all');
            figure;imshow(frame);
            for i=1:NUM
                [r,c] = find(L_BW==i);
                S(i) = stats(i).Area;
                L(i) = stats(i).Perimeter;
                C(i) = (L(i)*L(i)) / (4 * pi * S(i));
                if app.minCellSize<S(i) && S(i)<app.maxCellSize
                    if 50<L(i) && L(i)<500
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
            app.processedFrame = getframe(gca).cdata;
        end