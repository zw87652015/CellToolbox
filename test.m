function StartcamButtonPushed(app, event)
        if app.isStreaming
            res = app.cam.Resolution;
            width = str2double(res(1:strfind(res,'x')-1));
            height = str2double(res(strfind(res,'x')+1:end));
            if isempty(app.UIAxes.Children)
                app.ImageHandle = image(app.UIAxes, zeros(width,height,3));
            end
            app.UIAxes.XLim = [0 width];
            app.UIAxes.YLim = [0 height];
            app.UIAxes.DataAspectRatio = [1 1 1];
            app.UIAxes.Visible = 'off';
            
            if isempty(app.Timer) || ~isvalid(app.Timer)
                app.Timer = timer('ExecutionMode', 'fixedRate', ...
                    'Period', 1/30, ...  % Reduce to 30 Hz for better stability
                    'BusyMode', 'drop', ... % Drop frames if system is busy
                    'TimerFcn', @(~,~) updateFrame(app));
            end
            start(app.Timer);
        else
            if ~isempty(app.Timer) && isvalid(app.Timer)
                stop(app.Timer);
            end
        end
end

function updateFrame(app)
    if app.isStreaming
        try
            frame = snapshot(app.cam);
            if ~isempty(frame)
                app.ImageHandle.CData = frame;
                drawnow limitrate; % More efficient update
                
                % Store the latest frame for processing
                app.latestFrame = frame;
            end
        catch ME
            % Handle any camera errors silently
            warning('Camera error: %s', ME.message);
        end
    end
end