function processFrame(app)
    if app.isStreaming && app.isProcessing
        % Get the latest frame from the stored property
        frame = app.latestFrame;
        if isempty(frame)
            return;
        end

        W = cell(1,8);
        W{1} = [5,5,5; -3,0,-3; -3,-3,-3];
        W{2} = [5,5,-3; 5,0,-3; -3,-3,-3];
        W{3} = [5,-3,-3; 5,0,-3; 5,-3,-3];
        W{4} = [-3,-3,-3; 5,0,-3; 5,5,-3];
        W{5} = [-3,-3,-3; -3,0,-3; 5,5,5];
        W{6} = [-3,-3,-3; -3,0,5; -3,5,5];
        W{7} = [-3,-3,5; -3,0,5; -3,-3,5];
        W{8} = [-3,5,5; -3,0,5; -3,-3,-3];

        % 图像处理（使用单精度以提高速度）
        % GrayImage = rgb2gray(frame);
        % DoubleImage = im2single(GrayImage);  % 使用single代替double
        % DenoisedImage = imfilter(DoubleImage, fspecial('gaussian', [3 3], 2), 'replicate');
        % M = graythresh(frame(:,:,3));
        % BinaryImage = imbinarize(frame(:,:,3), M);
        % BinaryImage = ~BinaryImage;
        % 
        % ROIedge = edge(DenoisedImage,'canny', 0.3) | ...
        %  edge(DenoisedImage,'sobel') | ...
        %  edge(DenoisedImage,'prewitt') | ...
        %  edge(DenoisedImage,'roberts');
        
        % Move da+ta to GPU
        try 
            if gpuDeviceCount > 0
                frame_gpu = gpuArray(frame);
                
                % 图像处理（使用GPU加速）
                GrayImage = rgb2gray(frame_gpu);
                DoubleImage = im2single(GrayImage);
                DenoisedImage = imfilter(DoubleImage, gpuArray(fspecial('gaussian', [3 3], 2)), 'replicate');
                
                % M = graythresh(frame_gpu(:,:,3));
                % BinaryImage = imbinarize(frame_gpu(:,:,3), M);
                % BinaryImage = ~BinaryImage;

                % Thresholding using direct comparison
                frame_blue = frame_gpu(:,:,3);
                M = graythresh(gather(frame_blue));  % graythresh needs CPU data
                BinaryImage = frame_blue > (M * 255);  % Direct threshold comparison on GPU
                BinaryImage = ~BinaryImage;
                
                % % Edge detection on GPU
                % ROIedge = edge(DenoisedImage,'canny', 0.3) | ...
                %          edge(DenoisedImage,'sobel') | ...
                %          edge(DenoisedImage,'prewitt') | ...
                %          edge(DenoisedImage,'roberts');
                % Temporarily move to CPU for edge detection
                DenoisedImage_cpu = gather(DenoisedImage);
                ROIedge = edge(DenoisedImage_cpu,'canny', 0.3) | ...
                            edge(DenoisedImage_cpu,'sobel') | ...
                            edge(DenoisedImage_cpu,'prewitt') | ...
                            edge(DenoisedImage_cpu,'roberts');
                ROIedge = gpuArray(ROIedge);

                % Move results back to CPU for further processing
                DenoisedImage = gather(DenoisedImage);
                BinaryImage = gather(BinaryImage);
                ROIedge = gather(ROIedge);
            else
                % Fallback to CPU processing
                GrayImage = rgb2gray(frame);
                DoubleImage = im2single(GrayImage);
                DenoisedImage = imfilter(DoubleImage, fspecial('gaussian', [3 3], 2), 'replicate');
                M = graythresh(frame(:,:,3));
                BinaryImage = frame(:,:,3) > (M * 255);  % Direct threshold comparison on CPU
                BinaryImage = ~BinaryImage;
                ROIedge = edge(DenoisedImage,'canny', 0.3) | ...
                            edge(DenoisedImage,'sobel') | ...
                            edge(DenoisedImage,'prewitt') | ...
                            edge(DenoisedImage,'roberts');
            end
            
            % % Kirsch处理（预分配内存）
            % I = cell(1,8);
            % I9 = false(size(DenoisedImage));
            % 
            % parfor hh=1:8
            %     I{1,hh} = filter2(W{1,hh}, DenoisedImage);
            %     I{1,hh} = imbinarize(I{1,hh}, graythresh(I{1,hh}));
            % end

            % Move Kirsch filters to GPU if available
            if gpuDeviceCount > 0
                W = cellfun(@gpuArray, W, 'UniformOutput', false);
                DenoisedImage_gpu = gpuArray(DenoisedImage);
            end

            I = cell(1,8);
            I9 = false(size(DenoisedImage));

            parfor hh=1:8
                if gpuDeviceCount > 0
                    I{1,hh} = filter2(W{1,hh}, DenoisedImage_gpu);
                    I{1,hh} = I{1,hh} > (graythresh(gather(I{1,hh})) * 255);  % Direct threshold comparison on GPU
                    I{1,hh} = gather(I{1,hh});
                else
                    I{1,hh} = filter2(W{1,hh}, DenoisedImage);
                    I{1,hh} = I{1,hh} > (graythresh(I{1,hh}) * 255);  % Direct threshold comparison on CPU
                end
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
            
            % 标记连通区域
            [L_BW,NUM] = bwlabel(Finalseg, 4);
            if NUM > 0
                stats = regionprops(L_BW, 'Area', 'Perimeter', 'PixelList');
                % 清除之前的矩形
                if ~isempty(app.RectHandles)
                    delete(app.RectHandles);
                    app.RectHandles = [];
                end
            
                % 绘制新的矩形
                app.RectHandles = gobjects(NUM, 1);
                hold(app.UIAxes, 'on');
                rect_count = 0;
                
                for i = 1:NUM
                    S = stats(i).Area;
                    L = stats(i).Perimeter;
                    C = (L*L) / (4 * pi * S);
                    
                    if 1000<S && S<6000 && 100<L && L<500 && 0.8<C && C<1.8
                        pixels = stats(i).PixelList;
                        rmin = min(pixels(:,2)); rmax = max(pixels(:,2));
                        cmin = min(pixels(:,1)); cmax = max(pixels(:,1));
                        w = cmax-cmin+1;
                        h = rmax-rmin+1;
                        
                        if (h>w && 1.5*w>h) || (w>h && 1.5*h>w) || (h==w)
                            rect_count = rect_count + 1;
                            app.RectHandles(rect_count) = rectangle(app.UIAxes, ...
                                'Position', [cmin rmin w h], ...
                                'EdgeColor', 'g', 'LineWidth', 2);
                        end
                    end
                end
            end

            % 删除未使用的句柄预分配
            app.RectHandles(rect_count+1:end) = [];
            hold(app.UIAxes, 'off');
        catch ME
            dispLogInfo(app, "Error processing frame: " + ME.message);
        end
    end    
end

function StartlivedetectionButtonPushed(app, event)
    app.isProcessing = ~app.isProcessing;
    if app.isProcessing
        if isempty(gcp('nocreate'))
            parpool('Processes');  % Initialize parallel pool
        end
        app.StartlivedetectionButton.Text = "Stop live detection";
        app.StartlivedetectionButton.FontColor = "#f54236";
        dispLogInfo(app, "Cell detection started.");             
        
        % 预创建结构元素
        app.se1 = strel('disk', 1);
        app.se2 = strel('disk', 3);

        if isempty(app.ProcessTimer) || ~isvalid(app.ProcessTimer)
            app.ProcessTimer = timer('ExecutionMode', 'fixedRate', ...
                'Period', app.DetectionRate, ...  % 按照DetectionRate频率处理
                'TimerFcn', @(~,~) processFrame(app));
        end
        start(app.ProcessTimer);
    else
        app.StartlivedetectionButton.Text = "Start live detection";
        app.StartlivedetectionButton.FontColor = "#000000";
        dispLogInfo(app, "Cell detection stopped.");
        
        if ~isempty(app.ProcessTimer) && isvalid(app.ProcessTimer)
            stop(app.ProcessTimer);
            delete(app.ProcessTimer);
        end

        % Clean up GPU if it was used
        if gpuDeviceCount > 0
            % Reset GPU device
            gpuDevice(1);
        end

        % Clean up parallel pool asynchronously
        if ~isempty(gcp('nocreate'))
            parfeval(@delete, 0, gcp('nocreate'));
        end

        % Clean up display
        if ~isempty(app.RectHandles)
            delete(app.RectHandles);
            app.RectHandles = [];
        end
    end
end

function SnapshotButtonPushed(app, event)
    % Get the current frame at full resolution
    frame = app.latestFrame;
    if isempty(frame)
        dispLogInfo(app, 'No frame available to capture');
        return;
    end
    
    % Draw detection boxes on the full resolution image
    img = frame;
    if ~isempty(app.RectHandles)
        % Get all rectangle positions
        for i = 1:length(app.RectHandles)
            pos = app.RectHandles(i).Position;
            % Draw rectangle on the full resolution image
            img = insertShape(img, 'Rectangle', pos, 'Color', 'red', 'LineWidth', 2);
        end
    end
    
    % Create filename with current timestamp using datetime
    timestamp = string(datetime('now'), 'yyyy-MM-dd_HH_mm_ss');
    filename = sprintf('CellDetection-%s.png', timestamp);
    
    % Save the image
    imwrite(img, filename);
    
    % Display confirmation message
    dispLogInfo(app, sprintf('Snapshot saved as %s', filename));
end