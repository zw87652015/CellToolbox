classdef SignalSourceController < matlab.apps.AppBase

    % Properties that correspond to app components
    properties (Access = public)
        UIFigure              matlab.ui.Figure
        LogMenu               matlab.ui.container.Menu
        AboutMenu             matlab.ui.container.Menu
        ClearlogMenu          matlab.ui.container.Menu
        GridLayout            matlab.ui.container.GridLayout
        ReadButton            matlab.ui.control.Button
        SetButton             matlab.ui.control.Button
        PulsesTextArea        matlab.ui.control.TextArea
        PulsesTextAreaLabel   matlab.ui.control.Label
        pulsesLabel           matlab.ui.control.Label
        sLabel_4              matlab.ui.control.Label
        TimerTextArea         matlab.ui.control.TextArea
        TimerTextAreaLabel    matlab.ui.control.Label
        DisconnectButton      matlab.ui.control.Button
        ConnectButton         matlab.ui.control.Button
        sLabel_3              matlab.ui.control.Label
        LastingTextArea       matlab.ui.control.TextArea
        LastingTextAreaLabel  matlab.ui.control.Label
        LogTextArea           matlab.ui.control.TextArea
        LogTextAreaLabel      matlab.ui.control.Label
        SavelogButton         matlab.ui.control.Button
        Output1offButton      matlab.ui.control.Button
        Output1onButton       matlab.ui.control.Button
    end


    % Public properties that correspond to the Simulink model
    properties (Access = public, Transient)
        Simulation simulink.Simulation
    end

    
    properties (Access = public)
        currentAppVersion = "v1.2";
        log % String
        res;
        Timer;
        ProcessTimer;
        OutputTimer; % Timer for automatic output turn-off
        DG2052; % VISA connection to DG2052 device
        isConnected = false; % Connection status
        CountdownTimer; % Timer for updating countdown display
        remainingTime = 0; % Remaining time in seconds
        OverlayHandle;
        se1;
        se2;
        combined_edge;
    end
    
    methods (Access = public)
        function dispLogInfo(app, str)
            string = sprintf("-> %s\n", str);
            app.log = strcat(app.log, string);
            app.LogTextArea.Value = app.log;
        end
        

        function autoTurnOffOutput(app)
            % Automatically turn off the output when timer expires
            if ~app.isConnected || isempty(app.DG2052)
                dispLogInfo(app, "Error: DG2052 not connected during auto turn-off.");
                return;
            end
            
            try
                dispLogInfo(app, "Output 1 OFF (auto).");
                app.Output1onButton.Enable = 'on';
                app.Output1offButton.Enable = 'off';
                
                % Clean up the timers
                if ~isempty(app.OutputTimer) && isvalid(app.OutputTimer)
                    delete(app.OutputTimer);
                    app.OutputTimer = [];
                end
                
                app.stopCountdownDisplay();
                
                % Turn off the signal source using existing connection
                fprintf(app.DG2052, ':OUTP1 OFF');
            catch ME
                dispLogInfo(app, "Error during auto turn-off: " + ME.message);
            end
        end

        function startCountdownDisplay(app)
            % Start the countdown timer that updates every 0.1 seconds
            if ~isempty(app.CountdownTimer) && isvalid(app.CountdownTimer)
                stop(app.CountdownTimer);
                delete(app.CountdownTimer);
            end
            
            % Create countdown timer that updates every 0.1 seconds
            app.CountdownTimer = timer('TimerFcn', @(~,~) app.updateCountdownDisplay(), ...
                                     'Period', 0.1, ...
                                     'ExecutionMode', 'fixedRate');
            start(app.CountdownTimer);
            
            % Initial display update
            app.updateCountdownDisplay();
        end
        
        function updateCountdownDisplay(app)
            % Update the countdown display
            if app.remainingTime > 0
                app.TimerTextArea.Value = {sprintf('%.1f', app.remainingTime)};
                app.remainingTime = app.remainingTime - 0.1;
            else
                app.TimerTextArea.Value = {'0'};
                app.stopCountdownDisplay();
            end
        end
        
        function stopCountdownDisplay(app)
            % Stop and clean up the countdown timer
            if ~isempty(app.CountdownTimer) && isvalid(app.CountdownTimer)
                stop(app.CountdownTimer);
                delete(app.CountdownTimer);
                app.CountdownTimer = [];
            end
            app.TimerTextArea.Value = {'0'};
            app.remainingTime = 0;
        end
    end
    
    methods (Access = private)
        % Helper function to combine edges
    end

    % Callbacks that handle component events
    methods (Access = private)

        % Code that executes after component creation
        function startupFcn(app)
            % Initialize button states
            app.ConnectButton.Enable = 'on';
            app.DisconnectButton.Enable = 'off';
            app.Output1onButton.Enable = 'off';
            app.Output1offButton.Enable = 'off';

            % Initialize timer display
            app.TimerTextArea.Value = {'0'};
        end

        % Button pushed function: Output1onButton
        function Output1onButtonPushed(app, event)
            if ~app.isConnected || isempty(app.DG2052)
                dispLogInfo(app, "Error: DG2052 not connected. Please connect first.");
                return;
            end
            
            try
                dispLogInfo(app, "Output 1 ON.")
                app.Output1onButton.Enable = 'off';
                app.Output1offButton.Enable = 'on';
                
                % Turn on the signal source using existing connection
                fprintf(app.DG2052, ':OUTP1 ON');

                % Check if we need to set up an automatic turn-off timer
                try
                    lastingTimeStr = app.LastingTextArea.Value{1};
                    lastingTime = str2double(lastingTimeStr);
                    
                    if ~isnan(lastingTime) && lastingTime > 0
                        % Clean up any existing timer
                        if ~isempty(app.OutputTimer) && isvalid(app.OutputTimer)
                            stop(app.OutputTimer);
                            delete(app.OutputTimer);
                        end
                        
                        % Create and start the auto turn-off timer
                        app.OutputTimer = timer('TimerFcn', @(~,~) app.autoTurnOffOutput(), ...
                                              'StartDelay', lastingTime, ...
                                              'ExecutionMode', 'singleShot');
                        start(app.OutputTimer);
                        
                        % Start countdown display
                        app.remainingTime = lastingTime;
                        app.startCountdownDisplay();

                        dispLogInfo(app, sprintf("Auto turn-off timer set for %.1f seconds.", lastingTime));
                    end
                catch ME
                    dispLogInfo(app, "Warning: Invalid lasting time value. Timer not set.");
                end
            catch ME
                dispLogInfo(app, "Error turning on output: " + ME.message);
                app.Output1onButton.Enable = 'on';
                app.Output1offButton.Enable = 'off';
            end
        end

        % Button pushed function: Output1offButton
        function Output1offButtonPushed(app, event)
            if ~app.isConnected || isempty(app.DG2052)
                dispLogInfo(app, "Error: DG2052 not connected. Please connect first.");
                return;
            end
            
            try
                dispLogInfo(app, "Output 1 OFF.")
                app.Output1onButton.Enable = 'on';
                app.Output1offButton.Enable = 'off';
                
                % Clean up any active timers
                if ~isempty(app.OutputTimer) && isvalid(app.OutputTimer)
                    stop(app.OutputTimer);
                    delete(app.OutputTimer);
                    app.OutputTimer = [];
                end

                app.stopCountdownDisplay();

                % Turn off the signal source using existing connection
                fprintf(app.DG2052, ':OUTP1 OFF');
            catch ME
                dispLogInfo(app, "Error turning off output: " + ME.message);
            end
        end

        % Menu selected function: ClearlogMenu
        function ClearlogMenuSelected(app, event)
            app.log = "";
            app.LogTextArea.Value = "";
        end

        % Menu selected function: AboutMenu
        function AboutMenuSelected(app, event)
            dispLogInfo(app, app.currentAppVersion);
        end

        % Value changed function: LastingTextArea
        function LastingTextAreaValueChanged(app, event)
            value = app.LastingTextArea.Value{1};
            
             % Validate the input
            numValue = str2double(value);
            if isnan(numValue) || numValue < 0
                % Reset to default if invalid
                app.LastingTextArea.Value = {'0'};
                dispLogInfo(app, "Invalid lasting time. Reset to 0.");
            else
                % Update the display to show the validated number
                app.LastingTextArea.Value = {sprintf('%.1f', numValue)};
            end
        end

        % Button pushed function: ConnectButton
        function ConnectButtonPushed(app, event)
            try
                if ~app.isConnected
                    % Try to find available DG2052 device
                    dispLogInfo(app, "Searching for DG2052 device...");
                    
                    % Get list of available VISA resources
                    try
                        hwinfo = instrhwinfo('visa');
                        availableResources = hwinfo.InstalledAdaptors;
                        dispLogInfo(app, "Available VISA adaptors: " + strjoin(availableResources, ', '));
                        
                        % Try different possible connection strings for DG2052
                        connectionStrings = {
                            'USB0::0x1AB1::0x0644::DG2P232400656::0::INSTR',
                            'USB0::0x1AB1::0x0644::DG2P232400656::INSTR',
                            'USB::0x1AB1::0x0644::DG2P232400656::0::INSTR',
                            'USB::0x1AB1::0x0644::DG2P232400656::INSTR'
                        };
                        
                        connected = false;
                        for i = 1:length(connectionStrings)
                            try
                                dispLogInfo(app, "Trying connection: " + connectionStrings{i});
                                app.DG2052 = visa('NI', connectionStrings{i});
                                fopen(app.DG2052);
                                connected = true;
                                dispLogInfo(app, "Connected using: " + connectionStrings{i});
                                break;
                            catch
                                if ~isempty(app.DG2052)
                                    delete(app.DG2052);
                                    app.DG2052 = [];
                                end
                            end
                        end
                        
                        if connected
                            app.isConnected = true;
                            app.ConnectButton.Enable = 'off';
                            app.DisconnectButton.Enable = 'on';
                            app.Output1onButton.Enable = 'on';
                            app.Output1offButton.Enable = 'off';
                            dispLogInfo(app, "DG2052 connected successfully.");
                        else
                            error('Could not connect with any of the attempted connection strings');
                        end
                        
                    catch ME2
                        dispLogInfo(app, "Error getting VISA info: " + ME2.message);
                        % Fallback to original connection attempt
                        app.DG2052 = visa('NI', 'USB0::0x1AB1::0x0644::DG2P232400656::0::INSTR');
                        fopen(app.DG2052);
                        app.isConnected = true;
                        app.ConnectButton.Enable = 'off';
                        app.DisconnectButton.Enable = 'on';
                        app.Output1onButton.Enable = 'on';
                        app.Output1offButton.Enable = 'off';
                        dispLogInfo(app, "DG2052 connected successfully.");
                    end
                else
                    dispLogInfo(app, "DG2052 is already connected.");
                end
            catch ME
                dispLogInfo(app, "Failed to connect to DG2052: " + ME.message);
                dispLogInfo(app, "Please check: 1) Device is connected via USB, 2) Device is powered on, 3) No other software is using the device");
                app.isConnected = false;
                if ~isempty(app.DG2052)
                    try
                        delete(app.DG2052);
                    catch
                    end
                    app.DG2052 = [];
                end
            end
        end

        % Button pushed function: DisconnectButton
        function DisconnectButtonPushed(app, event)
            try
                if app.isConnected && ~isempty(app.DG2052)
                    % Turn off output before disconnecting
                    fprintf(app.DG2052, ':OUTP1 OFF');
                    fclose(app.DG2052);
                    clear app.DG2052;
                    app.DG2052 = [];
                    app.isConnected = false;
                    app.ConnectButton.Enable = 'on';
                    app.DisconnectButton.Enable = 'off';
                    app.Output1onButton.Enable = 'off';
                    app.Output1offButton.Enable = 'off';
                    
                    % Clean up any active timers
                    if ~isempty(app.OutputTimer) && isvalid(app.OutputTimer)
                        stop(app.OutputTimer);
                        delete(app.OutputTimer);
                        app.OutputTimer = [];
                    end
                    
                    app.stopCountdownDisplay();
                    
                    dispLogInfo(app, "DG2052 disconnected and cleared.");
                else
                    dispLogInfo(app, "DG2052 is not connected.");
                end
            catch ME
                dispLogInfo(app, "Error during disconnect: " + ME.message);
                app.isConnected = false;
                app.ConnectButton.Enable = 'on';
                app.DisconnectButton.Enable = 'off';
            end
        end

        % Button pushed function: SavelogButton
        function SavelogButtonPushed(app, event)
            try
                % Generate timestamp for filename
                timestamp = datestr(now, 'yyyy-mm-dd_HH-MM-SS');
                filename = sprintf('log_%s.txt', timestamp);
                
                % Get current working directory
                currentDir = pwd;
                fullPath = fullfile(currentDir, filename);
                
                % Write log content to file
                if ~isempty(app.log)
                    fileID = fopen(fullPath, 'w');
                    if fileID == -1
                        error('Could not create log file');
                    end
                    
                    fprintf(fileID, '%s', app.log);
                    fclose(fileID);
                    
                    dispLogInfo(app, sprintf("Log saved to: %s", fullPath));
                else
                    dispLogInfo(app, "No log content to save.");
                end
                
            catch ME
                dispLogInfo(app, "Error saving log: " + ME.message);
            end
        end

        % Button pushed function: SetButton
        function SetButtonPushed(app, event)
            % if ~app.isConnected || isempty(app.DG2052)
            %     dispLogInfo(app, "Error: DG2052 not connected. Please connect first.");
            %     return;
            % end
            
            try
                % Get values from text areas
                % voltageStr = app.VoltageTextArea.Value{1};
                % widthStr = app.WidthTextArea.Value{1};
                pulsesStr = app.PulsesTextArea.Value{1};
                
                % Validate and convert values
                % voltage = str2double(voltageStr);
                % width = str2double(widthStr);
                pulses = str2double(pulsesStr);
                
                % if isnan(voltage) || isnan(width) || isnan(pulses)
                if isnan(pulses)
                    % dispLogInfo(app, "Error: Invalid input values. Please check Voltage, Width, and Pulses.");
                    dispLogInfo(app, "Error: Invalid input values. Please check Pulses.");
                    return;
                end
                
                % if voltage <= 0 || width <= 0 || pulses <= 0
                if pulses <= 0
                    dispLogInfo(app, "Error: All values must be positive numbers.");
                    return;
                end
                
                % Calculate frequency from width (10us = 50kHz)
                % Formula: frequency = 50000 / (width / 10) = 500000 / width Hz
                % frequency = 500000 / width; % Hz
                
                % Calculate lasting time = pulses + 0.3 seconds
                lastingTime = pulses + 0.3;
                
                % Update the Lasting text area
                app.LastingTextArea.Value = {sprintf('%.1f', lastingTime)};
                
                % dispLogInfo(app, "Setting DG2052 parameters...");
                
                % Log the settings
                % dispLogInfo(app, sprintf("Parameters set - UI Voltage: %.1fV (Applied: %.1fV), Width: %.1fus, Frequency: %.1fHz, Pulses: %.0f, Lasting: %.1fs", ...
                %     voltage, actualVoltage, width, frequency, pulses, lastingTime));
                    
            catch ME
                dispLogInfo(app, "Error setting DG2052 parameters: " + ME.message);
            end
        end

        % Button pushed function: ReadButton
        function ReadButtonPushed(app, event)
            if ~app.isConnected || isempty(app.DG2052)
                dispLogInfo(app, "Error: DG2052 not connected. Please connect first.");
                return;
            end
            
            try
                dispLogInfo(app, "Reading DG2052 current settings...");
                
                % Read waveform type
                fprintf(app.DG2052, ':SOUR1:FUNC?');
                waveform = fscanf(app.DG2052, '%s');
                
                % Read high level voltage
                fprintf(app.DG2052, ':SOUR1:VOLT:HIGH?');
                highVolt = fscanf(app.DG2052, '%f');
                
                % Read low level voltage
                fprintf(app.DG2052, ':SOUR1:VOLT:LOW?');
                lowVolt = fscanf(app.DG2052, '%f');
                
                % Read frequency
                fprintf(app.DG2052, ':SOUR1:FREQ?');
                frequency = fscanf(app.DG2052, '%f');
                
                % Read pulse width
                fprintf(app.DG2052, ':SOUR1:PULS:WIDT?');
                pulseWidth = fscanf(app.DG2052, '%f');
                
                % Read output status
                fprintf(app.DG2052, ':OUTP1?');
                outputStatus = fscanf(app.DG2052, '%d');
                
               % Convert width from seconds to microseconds for display
                width_us = pulseWidth * 1e6;
                
                % Display current settings in log
                dispLogInfo(app, "=== Current DG2052 Settings ===");
                dispLogInfo(app, sprintf("Waveform: %s", strtrim(waveform)));
                dispLogInfo(app, sprintf("High Level (高电平): %.3f V", highVolt));
                dispLogInfo(app, sprintf("Low Level: %.3f V", lowVolt));
                dispLogInfo(app, sprintf("Frequency: %.1f Hz", frequency));
                dispLogInfo(app, sprintf("Pulse Width: %.1f us", width_us));
                if outputStatus == 1
                    statusStr = "ON";
                else
                    statusStr = "OFF";
                end
                dispLogInfo(app, sprintf("Output Status: %s", statusStr));
                dispLogInfo(app, "===============================");
            catch ME
                dispLogInfo(app, "Error reading DG2052 settings: " + ME.message);
            end
        end

        % Callback function
        function VoltageTextAreaValueChanged(app, event)
            value = app.VoltageTextArea.Value{1};
            
            % Validate the input
            numValue = str2double(value);
            if isnan(numValue) || numValue <= 0
                % Reset to default if invalid
                app.VoltageTextArea.Value = {'160'};
                dispLogInfo(app, "Invalid voltage value. Reset to 160V.");
            else
                % Update the display to show the validated number
                app.VoltageTextArea.Value = {sprintf('%.1f', numValue)};
            end
        end

        % Callback function
        function WidthTextAreaValueChanged(app, event)
            value = app.WidthTextArea.Value{1};
            
            % Validate the input
            numValue = str2double(value);
            if isnan(numValue) || numValue <= 0
                % Reset to default if invalid
                app.WidthTextArea.Value = {'10'};
                dispLogInfo(app, "Invalid width value. Reset to 10us.");
            else
                % Update the display to show the validated number
                app.WidthTextArea.Value = {sprintf('%.1f', numValue)};
            end
        end

        % Value changed function: PulsesTextArea
        function PulsesTextAreaValueChanged(app, event)
            value = app.PulsesTextArea.Value{1};
            
            % Validate the input
            numValue = str2double(value);
            if isnan(numValue) || numValue <= 0
                % Reset to default if invalid
                app.PulsesTextArea.Value = {'1'};
                dispLogInfo(app, "Invalid pulses value. Reset to 1.");
                numValue = 1;
            else
                % Update the display to show the validated integer
                app.PulsesTextArea.Value = {sprintf('%.0f', round(numValue))};
                numValue = round(numValue);
            end
            
            % Automatically update Lasting time (Pulses + 0.3 seconds)
            lastingTime = numValue + 0.3;
            app.LastingTextArea.Value = {sprintf('%.1f', lastingTime)};
        end
    end

    % Component initialization
    methods (Access = private)

        % Create UIFigure and components
        function createComponents(app)

            % Create UIFigure and hide until all components are created
            app.UIFigure = uifigure('Visible', 'off');
            app.UIFigure.Position = [100 100 240 356];
            app.UIFigure.Name = 'MATLAB App';

            % Create LogMenu
            app.LogMenu = uimenu(app.UIFigure);
            app.LogMenu.ForegroundColor = [0.4667 0.6745 0.1882];
            app.LogMenu.Text = 'Log';

            % Create AboutMenu
            app.AboutMenu = uimenu(app.LogMenu);
            app.AboutMenu.MenuSelectedFcn = createCallbackFcn(app, @AboutMenuSelected, true);
            app.AboutMenu.Text = 'About.';

            % Create ClearlogMenu
            app.ClearlogMenu = uimenu(app.LogMenu);
            app.ClearlogMenu.MenuSelectedFcn = createCallbackFcn(app, @ClearlogMenuSelected, true);
            app.ClearlogMenu.Text = 'Clear log';

            % Create GridLayout
            app.GridLayout = uigridlayout(app.UIFigure);
            app.GridLayout.ColumnWidth = {72, 28, 26, 63};
            app.GridLayout.RowHeight = {22, 22, 22, 22, 22, 22, 22, 22, 22, 50, 10, '1x'};
            app.GridLayout.RowSpacing = 4.41176470588235;
            app.GridLayout.Padding = [10 4.41176470588235 10 4.41176470588235];

            % Create Output1onButton
            app.Output1onButton = uibutton(app.GridLayout, 'push');
            app.Output1onButton.ButtonPushedFcn = createCallbackFcn(app, @Output1onButtonPushed, true);
            app.Output1onButton.FontColor = [0.298 0.6863 0.3137];
            app.Output1onButton.Layout.Row = 2;
            app.Output1onButton.Layout.Column = [1 2];
            app.Output1onButton.Text = 'Output 1 on';

            % Create Output1offButton
            app.Output1offButton = uibutton(app.GridLayout, 'push');
            app.Output1offButton.ButtonPushedFcn = createCallbackFcn(app, @Output1offButtonPushed, true);
            app.Output1offButton.FontColor = [0.9608 0.2588 0.2118];
            app.Output1offButton.Layout.Row = 2;
            app.Output1offButton.Layout.Column = [3 4];
            app.Output1offButton.Text = 'Output 1 off';

            % Create SavelogButton
            app.SavelogButton = uibutton(app.GridLayout, 'push');
            app.SavelogButton.ButtonPushedFcn = createCallbackFcn(app, @SavelogButtonPushed, true);
            app.SavelogButton.Layout.Row = 9;
            app.SavelogButton.Layout.Column = 1;
            app.SavelogButton.Text = 'Save log';

            % Create LogTextAreaLabel
            app.LogTextAreaLabel = uilabel(app.GridLayout);
            app.LogTextAreaLabel.HorizontalAlignment = 'right';
            app.LogTextAreaLabel.FontSize = 10;
            app.LogTextAreaLabel.Layout.Row = 9;
            app.LogTextAreaLabel.Layout.Column = [1 4];
            app.LogTextAreaLabel.Text = 'Log';

            % Create LogTextArea
            app.LogTextArea = uitextarea(app.GridLayout);
            app.LogTextArea.Editable = 'off';
            app.LogTextArea.FontSize = 10;
            app.LogTextArea.Placeholder = 'Return Info & Logs';
            app.LogTextArea.Layout.Row = [10 12];
            app.LogTextArea.Layout.Column = [1 4];

            % Create LastingTextAreaLabel
            app.LastingTextAreaLabel = uilabel(app.GridLayout);
            app.LastingTextAreaLabel.HorizontalAlignment = 'right';
            app.LastingTextAreaLabel.Layout.Row = 3;
            app.LastingTextAreaLabel.Layout.Column = 1;
            app.LastingTextAreaLabel.Text = 'Lasting';

            % Create LastingTextArea
            app.LastingTextArea = uitextarea(app.GridLayout);
            app.LastingTextArea.ValueChangedFcn = createCallbackFcn(app, @LastingTextAreaValueChanged, true);
            app.LastingTextArea.Placeholder = '0';
            app.LastingTextArea.Layout.Row = 3;
            app.LastingTextArea.Layout.Column = [2 3];
            app.LastingTextArea.Value = {'0'};

            % Create sLabel_3
            app.sLabel_3 = uilabel(app.GridLayout);
            app.sLabel_3.Layout.Row = 3;
            app.sLabel_3.Layout.Column = 4;
            app.sLabel_3.Text = 's';

            % Create ConnectButton
            app.ConnectButton = uibutton(app.GridLayout, 'push');
            app.ConnectButton.ButtonPushedFcn = createCallbackFcn(app, @ConnectButtonPushed, true);
            app.ConnectButton.Layout.Row = 1;
            app.ConnectButton.Layout.Column = [1 2];
            app.ConnectButton.Text = 'Connect';

            % Create DisconnectButton
            app.DisconnectButton = uibutton(app.GridLayout, 'push');
            app.DisconnectButton.ButtonPushedFcn = createCallbackFcn(app, @DisconnectButtonPushed, true);
            app.DisconnectButton.Layout.Row = 1;
            app.DisconnectButton.Layout.Column = [3 4];
            app.DisconnectButton.Text = 'Disconnect';

            % Create TimerTextAreaLabel
            app.TimerTextAreaLabel = uilabel(app.GridLayout);
            app.TimerTextAreaLabel.HorizontalAlignment = 'right';
            app.TimerTextAreaLabel.Layout.Row = 4;
            app.TimerTextAreaLabel.Layout.Column = 1;
            app.TimerTextAreaLabel.Text = 'Timer';

            % Create TimerTextArea
            app.TimerTextArea = uitextarea(app.GridLayout);
            app.TimerTextArea.Editable = 'off';
            app.TimerTextArea.Layout.Row = 4;
            app.TimerTextArea.Layout.Column = [2 3];

            % Create sLabel_4
            app.sLabel_4 = uilabel(app.GridLayout);
            app.sLabel_4.Layout.Row = 4;
            app.sLabel_4.Layout.Column = 4;
            app.sLabel_4.Text = 's';

            % Create pulsesLabel
            app.pulsesLabel = uilabel(app.GridLayout);
            app.pulsesLabel.Layout.Row = 5;
            app.pulsesLabel.Layout.Column = 4;
            app.pulsesLabel.Text = 'pulse(s)';

            % Create PulsesTextAreaLabel
            app.PulsesTextAreaLabel = uilabel(app.GridLayout);
            app.PulsesTextAreaLabel.HorizontalAlignment = 'right';
            app.PulsesTextAreaLabel.Layout.Row = 5;
            app.PulsesTextAreaLabel.Layout.Column = 1;
            app.PulsesTextAreaLabel.Text = 'Pulses';

            % Create PulsesTextArea
            app.PulsesTextArea = uitextarea(app.GridLayout);
            app.PulsesTextArea.ValueChangedFcn = createCallbackFcn(app, @PulsesTextAreaValueChanged, true);
            app.PulsesTextArea.Placeholder = '1';
            app.PulsesTextArea.Layout.Row = 5;
            app.PulsesTextArea.Layout.Column = [2 3];
            app.PulsesTextArea.Value = {'1'};

            % Create SetButton
            app.SetButton = uibutton(app.GridLayout, 'push');
            app.SetButton.ButtonPushedFcn = createCallbackFcn(app, @SetButtonPushed, true);
            app.SetButton.Layout.Row = 8;
            app.SetButton.Layout.Column = [1 2];
            app.SetButton.Text = 'Set';

            % Create ReadButton
            app.ReadButton = uibutton(app.GridLayout, 'push');
            app.ReadButton.ButtonPushedFcn = createCallbackFcn(app, @ReadButtonPushed, true);
            app.ReadButton.Layout.Row = 8;
            app.ReadButton.Layout.Column = [3 4];
            app.ReadButton.Text = 'Read';

            % Show the figure after all components are created
            app.UIFigure.Visible = 'on';
        end
    end

    % App creation and deletion
    methods (Access = public)

        % Construct app
        function app = SignalSourceController

            % Create UIFigure and components
            createComponents(app)

            % Register the app with App Designer
            registerApp(app, app.UIFigure)

            % Execute the startup function
            runStartupFcn(app, @startupFcn)

            if nargout == 0
                clear app
            end
        end

        % Code that executes before app deletion
        function delete(app)

            % Delete UIFigure when app is deleted
            delete(app.UIFigure)
        end
    end
end