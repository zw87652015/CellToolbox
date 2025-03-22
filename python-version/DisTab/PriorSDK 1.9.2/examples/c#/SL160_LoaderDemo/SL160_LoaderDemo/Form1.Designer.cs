namespace SL160_LoaderDemo
{
    partial class Form1
    {
        /// <summary>
        /// Required designer variable.
        /// </summary>
        private System.ComponentModel.IContainer components = null;

        /// <summary>
        /// Clean up any resources being used.
        /// </summary>
        /// <param name="disposing">true if managed resources should be disposed; otherwise, false.</param>
        protected override void Dispose(bool disposing)
        {
            if (disposing && (components != null))
            {
                components.Dispose();
            }
            base.Dispose(disposing);
        }

        #region Windows Form Designer generated code

        /// <summary>
        /// Required method for Designer support - do not modify
        /// the contents of this method with the code editor.
        /// </summary>
        private void InitializeComponent()
        {
            this.components = new System.ComponentModel.Container();
            System.ComponentModel.ComponentResourceManager resources = new System.ComponentModel.ComponentResourceManager(typeof(Form1));
            this.menuStrip1 = new System.Windows.Forms.MenuStrip();
            this.connectToolStripMenuItem = new System.Windows.Forms.ToolStripMenuItem();
            this.editINIToolStripMenuItem = new System.Windows.Forms.ToolStripMenuItem();
            this.loaderINIToolStripMenuItem = new System.Windows.Forms.ToolStripMenuItem();
            this.optionsToolStripMenuItem = new System.Windows.Forms.ToolStripMenuItem();
            this.singleStepModeToolStripMenuItem = new System.Windows.Forms.ToolStripMenuItem();
            this.doSoakToolStripMenuItem = new System.Windows.Forms.ToolStripMenuItem();
            this.scanOnlySoakToolStripMenuItem = new System.Windows.Forms.ToolStripMenuItem();
            this.stageRasterEnabledToolStripMenuItem = new System.Windows.Forms.ToolStripMenuItem();
            this.redoCalibrationToolStripMenuItem = new System.Windows.Forms.ToolStripMenuItem();
            this.checkCalibrationToolStripMenuItem = new System.Windows.Forms.ToolStripMenuItem();
            this.joystickToolStripMenuItem = new System.Windows.Forms.ToolStripMenuItem();
            this.previewOnToolStripMenuItem = new System.Windows.Forms.ToolStripMenuItem();
            this.ReInitialiseToolStripMenuItem = new System.Windows.Forms.ToolStripMenuItem();
            this.loggingToolStripMenuItem = new System.Windows.Forms.ToolStripMenuItem();
            this.enabledToolStripMenuItem = new System.Windows.Forms.ToolStripMenuItem();
            this.ManualoolStripMenuItem = new System.Windows.Forms.ToolStripMenuItem();
            this.helpToolStripMenuItem = new System.Windows.Forms.ToolStripMenuItem();
            this.grpStatus = new System.Windows.Forms.GroupBox();
            this.lblEject = new System.Windows.Forms.Label();
            this.lblStallError = new System.Windows.Forms.Label();
            this.lblSlideSensorError = new System.Windows.Forms.Label();
            this.lblCommsError = new System.Windows.Forms.Label();
            this.lblCassetteNotScanned = new System.Windows.Forms.Label();
            this.lblNotIdle = new System.Windows.Forms.Label();
            this.lblSlideOnStage = new System.Windows.Forms.Label();
            this.lblInvalidCassette = new System.Windows.Forms.Label();
            this.lblInvalidSlide = new System.Windows.Forms.Label();
            this.lblNotSetup = new System.Windows.Forms.Label();
            this.lblNotInitialised = new System.Windows.Forms.Label();
            this.lblNotConnected = new System.Windows.Forms.Label();
            this.lblError = new System.Windows.Forms.Label();
            this.grpAction = new System.Windows.Forms.GroupBox();
            this.btnPreview = new System.Windows.Forms.Button();
            this.btnLoadHotels = new System.Windows.Forms.Button();
            this.btnEjectHotels = new System.Windows.Forms.Button();
            this.btnToHotel = new System.Windows.Forms.Button();
            this.btnToStage = new System.Windows.Forms.Button();
            this.grpHotel1 = new System.Windows.Forms.GroupBox();
            this.btnScan1 = new System.Windows.Forms.Button();
            this.btnSingle = new System.Windows.Forms.Button();
            this.btnStop = new System.Windows.Forms.Button();
            this.grpHotel2 = new System.Windows.Forms.GroupBox();
            this.btnScan2 = new System.Windows.Forms.Button();
            this.lblstate = new System.Windows.Forms.ToolStripStatusLabel();
            this.lbltime = new System.Windows.Forms.ToolStripStatusLabel();
            this.lblSoakCount = new System.Windows.Forms.ToolStripStatusLabel();
            this.lbllasterror = new System.Windows.Forms.ToolStripStatusLabel();
            this.statusStrip = new System.Windows.Forms.StatusStrip();
            this.toolTip1 = new System.Windows.Forms.ToolTip(this.components);
            this.grpNosePiece = new System.Windows.Forms.GroupBox();
            this.MC11_H = new System.Windows.Forms.Button();
            this.MC11_2 = new System.Windows.Forms.Button();
            this.MC11_1 = new System.Windows.Forms.Button();
            this.grpCube = new System.Windows.Forms.GroupBox();
            this.btnCubeShutter = new System.Windows.Forms.Button();
            this.HH313_6 = new System.Windows.Forms.Button();
            this.HH313_5 = new System.Windows.Forms.Button();
            this.HH313_4 = new System.Windows.Forms.Button();
            this.HH313_3 = new System.Windows.Forms.Button();
            this.HH313_2 = new System.Windows.Forms.Button();
            this.HH313_1 = new System.Windows.Forms.Button();
            this.HH313_H = new System.Windows.Forms.Button();
            this.grpStage = new System.Windows.Forms.GroupBox();
            this.txtXStep = new System.Windows.Forms.TextBox();
            this.btnF = new System.Windows.Forms.Button();
            this.btnR = new System.Windows.Forms.Button();
            this.btnH = new System.Windows.Forms.Button();
            this.btnL = new System.Windows.Forms.Button();
            this.btnB = new System.Windows.Forms.Button();
            this.lblY = new System.Windows.Forms.Label();
            this.lblX = new System.Windows.Forms.Label();
            this.label18 = new System.Windows.Forms.Label();
            this.label17 = new System.Windows.Forms.Label();
            this.txtZStep = new System.Windows.Forms.TextBox();
            this.btnD = new System.Windows.Forms.Button();
            this.btnZH = new System.Windows.Forms.Button();
            this.btnU = new System.Windows.Forms.Button();
            this.grpZ = new System.Windows.Forms.GroupBox();
            this.lblZ = new System.Windows.Forms.Label();
            this.label4 = new System.Windows.Forms.Label();
            this.grpLed = new System.Windows.Forms.GroupBox();
            this.lvl4 = new System.Windows.Forms.Label();
            this.lvl3 = new System.Windows.Forms.Label();
            this.lvl2 = new System.Windows.Forms.Label();
            this.lvl1 = new System.Windows.Forms.Label();
            this.Label12 = new System.Windows.Forms.Label();
            this.Label11 = new System.Windows.Forms.Label();
            this.Label10 = new System.Windows.Forms.Label();
            this.Label9 = new System.Windows.Forms.Label();
            this.lblFluor4 = new System.Windows.Forms.Label();
            this.btnLed4 = new System.Windows.Forms.Button();
            this.lblFluor3 = new System.Windows.Forms.Label();
            this.btnLed3 = new System.Windows.Forms.Button();
            this.lblFluor2 = new System.Windows.Forms.Label();
            this.btnLed2 = new System.Windows.Forms.Button();
            this.lblFluor1 = new System.Windows.Forms.Label();
            this.btnLed1 = new System.Windows.Forms.Button();
            this.HScrollBar4 = new System.Windows.Forms.HScrollBar();
            this.HScrollBar3 = new System.Windows.Forms.HScrollBar();
            this.HScrollBar2 = new System.Windows.Forms.HScrollBar();
            this.HScrollBar1 = new System.Windows.Forms.HScrollBar();
            this.btnShutter4 = new System.Windows.Forms.Button();
            this.menuStrip1.SuspendLayout();
            this.grpStatus.SuspendLayout();
            this.grpAction.SuspendLayout();
            this.grpHotel1.SuspendLayout();
            this.grpHotel2.SuspendLayout();
            this.statusStrip.SuspendLayout();
            this.grpNosePiece.SuspendLayout();
            this.grpCube.SuspendLayout();
            this.grpStage.SuspendLayout();
            this.grpZ.SuspendLayout();
            this.grpLed.SuspendLayout();
            this.SuspendLayout();
            // 
            // menuStrip1
            // 
            this.menuStrip1.Items.AddRange(new System.Windows.Forms.ToolStripItem[] {
            this.connectToolStripMenuItem,
            this.editINIToolStripMenuItem,
            this.optionsToolStripMenuItem,
            this.loggingToolStripMenuItem,
            this.ManualoolStripMenuItem,
            this.helpToolStripMenuItem});
            this.menuStrip1.Location = new System.Drawing.Point(0, 0);
            this.menuStrip1.Name = "menuStrip1";
            this.menuStrip1.ShowItemToolTips = true;
            this.menuStrip1.Size = new System.Drawing.Size(549, 28);
            this.menuStrip1.TabIndex = 0;
            this.menuStrip1.Text = "menuStrip1";
            // 
            // connectToolStripMenuItem
            // 
            this.connectToolStripMenuItem.Name = "connectToolStripMenuItem";
            this.connectToolStripMenuItem.Size = new System.Drawing.Size(75, 24);
            this.connectToolStripMenuItem.Text = "Connect";
            this.connectToolStripMenuItem.ToolTipText = "Establish connection to the SL160. On first connection\r\nyou will need to supply t" +
    "he COM port number the SL160\r\nis connected to.";
            this.connectToolStripMenuItem.Click += new System.EventHandler(this.connectToolStripMenuItem_Click);
            // 
            // editINIToolStripMenuItem
            // 
            this.editINIToolStripMenuItem.DropDownItems.AddRange(new System.Windows.Forms.ToolStripItem[] {
            this.loaderINIToolStripMenuItem});
            this.editINIToolStripMenuItem.Enabled = false;
            this.editINIToolStripMenuItem.Name = "editINIToolStripMenuItem";
            this.editINIToolStripMenuItem.Size = new System.Drawing.Size(47, 24);
            this.editINIToolStripMenuItem.Text = "Edit";
            // 
            // loaderINIToolStripMenuItem
            // 
            this.loaderINIToolStripMenuItem.Name = "loaderINIToolStripMenuItem";
            this.loaderINIToolStripMenuItem.Size = new System.Drawing.Size(144, 24);
            this.loaderINIToolStripMenuItem.Text = "loader INI";
            this.loaderINIToolStripMenuItem.ToolTipText = resources.GetString("loaderINIToolStripMenuItem.ToolTipText");
            this.loaderINIToolStripMenuItem.Click += new System.EventHandler(this.loaderINIToolStripMenuItem_Click);
            // 
            // optionsToolStripMenuItem
            // 
            this.optionsToolStripMenuItem.DropDownItems.AddRange(new System.Windows.Forms.ToolStripItem[] {
            this.singleStepModeToolStripMenuItem,
            this.doSoakToolStripMenuItem,
            this.scanOnlySoakToolStripMenuItem,
            this.stageRasterEnabledToolStripMenuItem,
            this.redoCalibrationToolStripMenuItem,
            this.checkCalibrationToolStripMenuItem,
            this.joystickToolStripMenuItem,
            this.previewOnToolStripMenuItem,
            this.ReInitialiseToolStripMenuItem});
            this.optionsToolStripMenuItem.Enabled = false;
            this.optionsToolStripMenuItem.Name = "optionsToolStripMenuItem";
            this.optionsToolStripMenuItem.Size = new System.Drawing.Size(73, 24);
            this.optionsToolStripMenuItem.Text = "Options";
            // 
            // singleStepModeToolStripMenuItem
            // 
            this.singleStepModeToolStripMenuItem.CheckOnClick = true;
            this.singleStepModeToolStripMenuItem.Name = "singleStepModeToolStripMenuItem";
            this.singleStepModeToolStripMenuItem.Size = new System.Drawing.Size(219, 24);
            this.singleStepModeToolStripMenuItem.Text = "Single Step Mode";
            this.singleStepModeToolStripMenuItem.ToolTipText = resources.GetString("singleStepModeToolStripMenuItem.ToolTipText");
            this.singleStepModeToolStripMenuItem.Click += new System.EventHandler(this.singleStepModeToolStripMenuItem_Click);
            // 
            // doSoakToolStripMenuItem
            // 
            this.doSoakToolStripMenuItem.CheckOnClick = true;
            this.doSoakToolStripMenuItem.Name = "doSoakToolStripMenuItem";
            this.doSoakToolStripMenuItem.Size = new System.Drawing.Size(219, 24);
            this.doSoakToolStripMenuItem.Text = "Full Soak";
            this.doSoakToolStripMenuItem.ToolTipText = "start or stop a continuous soak cycle of loading\r\nand unloading trays from apartm" +
    "ents to stage.";
            this.doSoakToolStripMenuItem.Click += new System.EventHandler(this.doSoakToolStripMenuItem_Click);
            // 
            // scanOnlySoakToolStripMenuItem
            // 
            this.scanOnlySoakToolStripMenuItem.CheckOnClick = true;
            this.scanOnlySoakToolStripMenuItem.Name = "scanOnlySoakToolStripMenuItem";
            this.scanOnlySoakToolStripMenuItem.Size = new System.Drawing.Size(219, 24);
            this.scanOnlySoakToolStripMenuItem.Text = "Scan Hotel Soak";
            this.scanOnlySoakToolStripMenuItem.ToolTipText = "soak cycle performing just hotel scanning";
            this.scanOnlySoakToolStripMenuItem.Click += new System.EventHandler(this.scanOnlySoakToolStripMenuItem_Click);
            // 
            // stageRasterEnabledToolStripMenuItem
            // 
            this.stageRasterEnabledToolStripMenuItem.CheckOnClick = true;
            this.stageRasterEnabledToolStripMenuItem.Name = "stageRasterEnabledToolStripMenuItem";
            this.stageRasterEnabledToolStripMenuItem.Size = new System.Drawing.Size(219, 24);
            this.stageRasterEnabledToolStripMenuItem.Text = "Stage Raster Enabled";
            this.stageRasterEnabledToolStripMenuItem.ToolTipText = "during a full soak perform a simple raster pattern \r\nof the stage to simulate a r" +
    "eal life scanning application.";
            // 
            // redoCalibrationToolStripMenuItem
            // 
            this.redoCalibrationToolStripMenuItem.Name = "redoCalibrationToolStripMenuItem";
            this.redoCalibrationToolStripMenuItem.Size = new System.Drawing.Size(219, 24);
            this.redoCalibrationToolStripMenuItem.Text = "Redo Calibration";
            this.redoCalibrationToolStripMenuItem.ToolTipText = "select which parts of the calibration to invalidate\r\nThis will cause the calibrat" +
    "ion procdure to be run\r\nautomatically after the next connect. \r\n";
            this.redoCalibrationToolStripMenuItem.Click += new System.EventHandler(this.redoCalibrationToolStripMenuItem_Click);
            // 
            // checkCalibrationToolStripMenuItem
            // 
            this.checkCalibrationToolStripMenuItem.Name = "checkCalibrationToolStripMenuItem";
            this.checkCalibrationToolStripMenuItem.Size = new System.Drawing.Size(219, 24);
            this.checkCalibrationToolStripMenuItem.Text = "Check Calibration";
            this.checkCalibrationToolStripMenuItem.ToolTipText = "Perform a step by step guide to testing the calibration. \r\nNote: can be done manu" +
    "ally also from the GUI.";
            this.checkCalibrationToolStripMenuItem.Click += new System.EventHandler(this.checkCalibrationToolStripMenuItem_Click);
            // 
            // joystickToolStripMenuItem
            // 
            this.joystickToolStripMenuItem.Name = "joystickToolStripMenuItem";
            this.joystickToolStripMenuItem.Size = new System.Drawing.Size(219, 24);
            this.joystickToolStripMenuItem.Text = "Joystick";
            this.joystickToolStripMenuItem.ToolTipText = "Configure some basic joystick setup parameters";
            this.joystickToolStripMenuItem.Click += new System.EventHandler(this.joystickToolStripMenuItem_Click);
            // 
            // previewOnToolStripMenuItem
            // 
            this.previewOnToolStripMenuItem.Checked = true;
            this.previewOnToolStripMenuItem.CheckOnClick = true;
            this.previewOnToolStripMenuItem.CheckState = System.Windows.Forms.CheckState.Checked;
            this.previewOnToolStripMenuItem.Name = "previewOnToolStripMenuItem";
            this.previewOnToolStripMenuItem.Size = new System.Drawing.Size(219, 24);
            this.previewOnToolStripMenuItem.Text = "Preview On";
            this.previewOnToolStripMenuItem.CheckedChanged += new System.EventHandler(this.previewOnToolStripMenuItem_CheckedChanged);
            // 
            // ReInitialiseToolStripMenuItem
            // 
            this.ReInitialiseToolStripMenuItem.Name = "ReInitialiseToolStripMenuItem";
            this.ReInitialiseToolStripMenuItem.Size = new System.Drawing.Size(219, 24);
            this.ReInitialiseToolStripMenuItem.Text = "ReInitialise";
            this.ReInitialiseToolStripMenuItem.Click += new System.EventHandler(this.ReInitialiseToolStripMenuItem_Click);
            // 
            // loggingToolStripMenuItem
            // 
            this.loggingToolStripMenuItem.CheckOnClick = true;
            this.loggingToolStripMenuItem.DropDownItems.AddRange(new System.Windows.Forms.ToolStripItem[] {
            this.enabledToolStripMenuItem});
            this.loggingToolStripMenuItem.Name = "loggingToolStripMenuItem";
            this.loggingToolStripMenuItem.Size = new System.Drawing.Size(76, 24);
            this.loggingToolStripMenuItem.Text = "Logging";
            this.loggingToolStripMenuItem.ToolTipText = "Controls logging of API calls to file\r\nPriorSDK.log in the application directory." +
    "";
            // 
            // enabledToolStripMenuItem
            // 
            this.enabledToolStripMenuItem.CheckOnClick = true;
            this.enabledToolStripMenuItem.Name = "enabledToolStripMenuItem";
            this.enabledToolStripMenuItem.Size = new System.Drawing.Size(99, 24);
            this.enabledToolStripMenuItem.Text = "Off";
            this.enabledToolStripMenuItem.Click += new System.EventHandler(this.enabledToolStripMenuItem_Click);
            // 
            // ManualoolStripMenuItem
            // 
            this.ManualoolStripMenuItem.Enabled = false;
            this.ManualoolStripMenuItem.Name = "ManualoolStripMenuItem";
            this.ManualoolStripMenuItem.Size = new System.Drawing.Size(111, 24);
            this.ManualoolStripMenuItem.Text = "Manual Move";
            this.ManualoolStripMenuItem.Click += new System.EventHandler(this.ManualoolStripMenuItem_Click);
            // 
            // helpToolStripMenuItem
            // 
            this.helpToolStripMenuItem.Name = "helpToolStripMenuItem";
            this.helpToolStripMenuItem.Size = new System.Drawing.Size(53, 24);
            this.helpToolStripMenuItem.Text = "Help";
            this.helpToolStripMenuItem.ToolTipText = "Help";
            this.helpToolStripMenuItem.Click += new System.EventHandler(this.helpToolStripMenuItem_Click);
            // 
            // grpStatus
            // 
            this.grpStatus.BackColor = System.Drawing.SystemColors.Control;
            this.grpStatus.Controls.Add(this.lblEject);
            this.grpStatus.Controls.Add(this.lblStallError);
            this.grpStatus.Controls.Add(this.lblSlideSensorError);
            this.grpStatus.Controls.Add(this.lblCommsError);
            this.grpStatus.Controls.Add(this.lblCassetteNotScanned);
            this.grpStatus.Controls.Add(this.lblNotIdle);
            this.grpStatus.Controls.Add(this.lblSlideOnStage);
            this.grpStatus.Controls.Add(this.lblInvalidCassette);
            this.grpStatus.Controls.Add(this.lblInvalidSlide);
            this.grpStatus.Controls.Add(this.lblNotSetup);
            this.grpStatus.Controls.Add(this.lblNotInitialised);
            this.grpStatus.Controls.Add(this.lblNotConnected);
            this.grpStatus.Controls.Add(this.lblError);
            this.grpStatus.Font = new System.Drawing.Font("Microsoft Sans Serif", 8.25F, System.Drawing.FontStyle.Regular, System.Drawing.GraphicsUnit.Point, ((byte)(0)));
            this.grpStatus.ForeColor = System.Drawing.SystemColors.ControlText;
            this.grpStatus.Location = new System.Drawing.Point(354, 56);
            this.grpStatus.Name = "grpStatus";
            this.grpStatus.Padding = new System.Windows.Forms.Padding(0);
            this.grpStatus.RightToLeft = System.Windows.Forms.RightToLeft.No;
            this.grpStatus.Size = new System.Drawing.Size(184, 458);
            this.grpStatus.TabIndex = 779;
            this.grpStatus.TabStop = false;
            this.grpStatus.Text = "Loader Status";
            // 
            // lblEject
            // 
            this.lblEject.BackColor = System.Drawing.SystemColors.Control;
            this.lblEject.BorderStyle = System.Windows.Forms.BorderStyle.Fixed3D;
            this.lblEject.Cursor = System.Windows.Forms.Cursors.Default;
            this.lblEject.Font = new System.Drawing.Font("Times New Roman", 7.8F, System.Drawing.FontStyle.Regular, System.Drawing.GraphicsUnit.Point, ((byte)(0)));
            this.lblEject.ForeColor = System.Drawing.SystemColors.ControlText;
            this.lblEject.Location = new System.Drawing.Point(8, 325);
            this.lblEject.Name = "lblEject";
            this.lblEject.RightToLeft = System.Windows.Forms.RightToLeft.No;
            this.lblEject.Size = new System.Drawing.Size(164, 23);
            this.lblEject.TabIndex = 762;
            this.lblEject.TextAlign = System.Drawing.ContentAlignment.MiddleCenter;
            this.toolTip1.SetToolTip(this.lblEject, "hotel shuttle ejected state");
            // 
            // lblStallError
            // 
            this.lblStallError.BackColor = System.Drawing.SystemColors.Control;
            this.lblStallError.BorderStyle = System.Windows.Forms.BorderStyle.Fixed3D;
            this.lblStallError.Cursor = System.Windows.Forms.Cursors.Default;
            this.lblStallError.Font = new System.Drawing.Font("Times New Roman", 7.8F, System.Drawing.FontStyle.Regular, System.Drawing.GraphicsUnit.Point, ((byte)(0)));
            this.lblStallError.ForeColor = System.Drawing.SystemColors.ControlText;
            this.lblStallError.Location = new System.Drawing.Point(8, 418);
            this.lblStallError.Name = "lblStallError";
            this.lblStallError.RightToLeft = System.Windows.Forms.RightToLeft.No;
            this.lblStallError.Size = new System.Drawing.Size(164, 23);
            this.lblStallError.TabIndex = 761;
            this.lblStallError.TextAlign = System.Drawing.ContentAlignment.MiddleCenter;
            this.toolTip1.SetToolTip(this.lblStallError, "an axis has stalled status");
            // 
            // lblSlideSensorError
            // 
            this.lblSlideSensorError.BackColor = System.Drawing.SystemColors.Control;
            this.lblSlideSensorError.BorderStyle = System.Windows.Forms.BorderStyle.Fixed3D;
            this.lblSlideSensorError.Cursor = System.Windows.Forms.Cursors.Default;
            this.lblSlideSensorError.Font = new System.Drawing.Font("Times New Roman", 7.8F, System.Drawing.FontStyle.Regular, System.Drawing.GraphicsUnit.Point, ((byte)(0)));
            this.lblSlideSensorError.ForeColor = System.Drawing.SystemColors.ControlText;
            this.lblSlideSensorError.Location = new System.Drawing.Point(8, 387);
            this.lblSlideSensorError.Name = "lblSlideSensorError";
            this.lblSlideSensorError.RightToLeft = System.Windows.Forms.RightToLeft.No;
            this.lblSlideSensorError.Size = new System.Drawing.Size(164, 23);
            this.lblSlideSensorError.TabIndex = 759;
            this.lblSlideSensorError.TextAlign = System.Drawing.ContentAlignment.MiddleCenter;
            this.toolTip1.SetToolTip(this.lblSlideSensorError, "unexpected tray sensor status");
            // 
            // lblCommsError
            // 
            this.lblCommsError.BackColor = System.Drawing.SystemColors.Control;
            this.lblCommsError.BorderStyle = System.Windows.Forms.BorderStyle.Fixed3D;
            this.lblCommsError.Cursor = System.Windows.Forms.Cursors.Default;
            this.lblCommsError.Font = new System.Drawing.Font("Times New Roman", 7.8F, System.Drawing.FontStyle.Regular, System.Drawing.GraphicsUnit.Point, ((byte)(0)));
            this.lblCommsError.ForeColor = System.Drawing.SystemColors.ControlText;
            this.lblCommsError.Location = new System.Drawing.Point(8, 356);
            this.lblCommsError.Name = "lblCommsError";
            this.lblCommsError.RightToLeft = System.Windows.Forms.RightToLeft.No;
            this.lblCommsError.Size = new System.Drawing.Size(164, 23);
            this.lblCommsError.TabIndex = 758;
            this.lblCommsError.TextAlign = System.Drawing.ContentAlignment.MiddleCenter;
            this.toolTip1.SetToolTip(this.lblCommsError, "comms error status");
            // 
            // lblCassetteNotScanned
            // 
            this.lblCassetteNotScanned.BackColor = System.Drawing.SystemColors.Control;
            this.lblCassetteNotScanned.BorderStyle = System.Windows.Forms.BorderStyle.Fixed3D;
            this.lblCassetteNotScanned.Cursor = System.Windows.Forms.Cursors.Default;
            this.lblCassetteNotScanned.Font = new System.Drawing.Font("Times New Roman", 7.8F, System.Drawing.FontStyle.Regular, System.Drawing.GraphicsUnit.Point, ((byte)(0)));
            this.lblCassetteNotScanned.ForeColor = System.Drawing.SystemColors.ControlText;
            this.lblCassetteNotScanned.Location = new System.Drawing.Point(8, 294);
            this.lblCassetteNotScanned.Name = "lblCassetteNotScanned";
            this.lblCassetteNotScanned.RightToLeft = System.Windows.Forms.RightToLeft.No;
            this.lblCassetteNotScanned.Size = new System.Drawing.Size(164, 23);
            this.lblCassetteNotScanned.TabIndex = 22;
            this.lblCassetteNotScanned.TextAlign = System.Drawing.ContentAlignment.MiddleCenter;
            this.toolTip1.SetToolTip(this.lblCassetteNotScanned, "hotel not scanned ");
            // 
            // lblNotIdle
            // 
            this.lblNotIdle.BackColor = System.Drawing.SystemColors.Control;
            this.lblNotIdle.BorderStyle = System.Windows.Forms.BorderStyle.Fixed3D;
            this.lblNotIdle.Cursor = System.Windows.Forms.Cursors.Default;
            this.lblNotIdle.Font = new System.Drawing.Font("Times New Roman", 7.8F, System.Drawing.FontStyle.Regular, System.Drawing.GraphicsUnit.Point, ((byte)(0)));
            this.lblNotIdle.ForeColor = System.Drawing.SystemColors.ControlText;
            this.lblNotIdle.Location = new System.Drawing.Point(8, 170);
            this.lblNotIdle.Name = "lblNotIdle";
            this.lblNotIdle.RightToLeft = System.Windows.Forms.RightToLeft.No;
            this.lblNotIdle.Size = new System.Drawing.Size(164, 23);
            this.lblNotIdle.TabIndex = 19;
            this.lblNotIdle.TextAlign = System.Drawing.ContentAlignment.MiddleCenter;
            this.toolTip1.SetToolTip(this.lblNotIdle, "idle status");
            // 
            // lblSlideOnStage
            // 
            this.lblSlideOnStage.BackColor = System.Drawing.SystemColors.Control;
            this.lblSlideOnStage.BorderStyle = System.Windows.Forms.BorderStyle.Fixed3D;
            this.lblSlideOnStage.Cursor = System.Windows.Forms.Cursors.Default;
            this.lblSlideOnStage.Font = new System.Drawing.Font("Times New Roman", 7.8F, System.Drawing.FontStyle.Regular, System.Drawing.GraphicsUnit.Point, ((byte)(0)));
            this.lblSlideOnStage.ForeColor = System.Drawing.SystemColors.ControlText;
            this.lblSlideOnStage.Location = new System.Drawing.Point(8, 201);
            this.lblSlideOnStage.Name = "lblSlideOnStage";
            this.lblSlideOnStage.RightToLeft = System.Windows.Forms.RightToLeft.No;
            this.lblSlideOnStage.Size = new System.Drawing.Size(164, 23);
            this.lblSlideOnStage.TabIndex = 16;
            this.lblSlideOnStage.TextAlign = System.Drawing.ContentAlignment.MiddleCenter;
            this.toolTip1.SetToolTip(this.lblSlideOnStage, "slide in stage sensor status");
            // 
            // lblInvalidCassette
            // 
            this.lblInvalidCassette.BackColor = System.Drawing.SystemColors.Control;
            this.lblInvalidCassette.BorderStyle = System.Windows.Forms.BorderStyle.Fixed3D;
            this.lblInvalidCassette.Cursor = System.Windows.Forms.Cursors.Default;
            this.lblInvalidCassette.Font = new System.Drawing.Font("Times New Roman", 7.8F, System.Drawing.FontStyle.Regular, System.Drawing.GraphicsUnit.Point, ((byte)(0)));
            this.lblInvalidCassette.ForeColor = System.Drawing.SystemColors.ControlText;
            this.lblInvalidCassette.Location = new System.Drawing.Point(8, 263);
            this.lblInvalidCassette.Name = "lblInvalidCassette";
            this.lblInvalidCassette.RightToLeft = System.Windows.Forms.RightToLeft.No;
            this.lblInvalidCassette.Size = new System.Drawing.Size(164, 23);
            this.lblInvalidCassette.TabIndex = 15;
            this.lblInvalidCassette.TextAlign = System.Drawing.ContentAlignment.MiddleCenter;
            this.toolTip1.SetToolTip(this.lblInvalidCassette, "invalid hotel id");
            // 
            // lblInvalidSlide
            // 
            this.lblInvalidSlide.BackColor = System.Drawing.SystemColors.Control;
            this.lblInvalidSlide.BorderStyle = System.Windows.Forms.BorderStyle.Fixed3D;
            this.lblInvalidSlide.Cursor = System.Windows.Forms.Cursors.Default;
            this.lblInvalidSlide.Font = new System.Drawing.Font("Times New Roman", 7.8F, System.Drawing.FontStyle.Regular, System.Drawing.GraphicsUnit.Point, ((byte)(0)));
            this.lblInvalidSlide.ForeColor = System.Drawing.SystemColors.ControlText;
            this.lblInvalidSlide.Location = new System.Drawing.Point(8, 232);
            this.lblInvalidSlide.Name = "lblInvalidSlide";
            this.lblInvalidSlide.RightToLeft = System.Windows.Forms.RightToLeft.No;
            this.lblInvalidSlide.Size = new System.Drawing.Size(164, 23);
            this.lblInvalidSlide.TabIndex = 14;
            this.lblInvalidSlide.TextAlign = System.Drawing.ContentAlignment.MiddleCenter;
            this.toolTip1.SetToolTip(this.lblInvalidSlide, "invalid tray id");
            // 
            // lblNotSetup
            // 
            this.lblNotSetup.BackColor = System.Drawing.SystemColors.Control;
            this.lblNotSetup.BorderStyle = System.Windows.Forms.BorderStyle.Fixed3D;
            this.lblNotSetup.Cursor = System.Windows.Forms.Cursors.Default;
            this.lblNotSetup.Font = new System.Drawing.Font("Times New Roman", 7.8F, System.Drawing.FontStyle.Regular, System.Drawing.GraphicsUnit.Point, ((byte)(0)));
            this.lblNotSetup.ForeColor = System.Drawing.SystemColors.ControlText;
            this.lblNotSetup.Location = new System.Drawing.Point(8, 139);
            this.lblNotSetup.Name = "lblNotSetup";
            this.lblNotSetup.RightToLeft = System.Windows.Forms.RightToLeft.No;
            this.lblNotSetup.Size = new System.Drawing.Size(164, 23);
            this.lblNotSetup.TabIndex = 13;
            this.lblNotSetup.TextAlign = System.Drawing.ContentAlignment.MiddleCenter;
            this.toolTip1.SetToolTip(this.lblNotSetup, "calibration status");
            // 
            // lblNotInitialised
            // 
            this.lblNotInitialised.BackColor = System.Drawing.SystemColors.Control;
            this.lblNotInitialised.BorderStyle = System.Windows.Forms.BorderStyle.Fixed3D;
            this.lblNotInitialised.Cursor = System.Windows.Forms.Cursors.Default;
            this.lblNotInitialised.Font = new System.Drawing.Font("Times New Roman", 7.8F, System.Drawing.FontStyle.Regular, System.Drawing.GraphicsUnit.Point, ((byte)(0)));
            this.lblNotInitialised.ForeColor = System.Drawing.SystemColors.ControlText;
            this.lblNotInitialised.Location = new System.Drawing.Point(8, 108);
            this.lblNotInitialised.Name = "lblNotInitialised";
            this.lblNotInitialised.RightToLeft = System.Windows.Forms.RightToLeft.No;
            this.lblNotInitialised.Size = new System.Drawing.Size(164, 23);
            this.lblNotInitialised.TabIndex = 12;
            this.lblNotInitialised.TextAlign = System.Drawing.ContentAlignment.MiddleCenter;
            this.toolTip1.SetToolTip(this.lblNotInitialised, "initalised status");
            // 
            // lblNotConnected
            // 
            this.lblNotConnected.BackColor = System.Drawing.SystemColors.Control;
            this.lblNotConnected.BorderStyle = System.Windows.Forms.BorderStyle.Fixed3D;
            this.lblNotConnected.Cursor = System.Windows.Forms.Cursors.Default;
            this.lblNotConnected.Font = new System.Drawing.Font("Times New Roman", 7.8F, System.Drawing.FontStyle.Regular, System.Drawing.GraphicsUnit.Point, ((byte)(0)));
            this.lblNotConnected.ForeColor = System.Drawing.SystemColors.ControlText;
            this.lblNotConnected.Location = new System.Drawing.Point(8, 77);
            this.lblNotConnected.Name = "lblNotConnected";
            this.lblNotConnected.RightToLeft = System.Windows.Forms.RightToLeft.No;
            this.lblNotConnected.Size = new System.Drawing.Size(164, 23);
            this.lblNotConnected.TabIndex = 11;
            this.lblNotConnected.Text = "NOT CONNECTED";
            this.lblNotConnected.TextAlign = System.Drawing.ContentAlignment.MiddleCenter;
            this.toolTip1.SetToolTip(this.lblNotConnected, "connected status");
            // 
            // lblError
            // 
            this.lblError.BackColor = System.Drawing.SystemColors.Control;
            this.lblError.BorderStyle = System.Windows.Forms.BorderStyle.Fixed3D;
            this.lblError.Cursor = System.Windows.Forms.Cursors.Default;
            this.lblError.Font = new System.Drawing.Font("Times New Roman", 7.8F, System.Drawing.FontStyle.Regular, System.Drawing.GraphicsUnit.Point, ((byte)(0)));
            this.lblError.ForeColor = System.Drawing.SystemColors.ControlText;
            this.lblError.Location = new System.Drawing.Point(8, 46);
            this.lblError.Name = "lblError";
            this.lblError.RightToLeft = System.Windows.Forms.RightToLeft.No;
            this.lblError.Size = new System.Drawing.Size(164, 23);
            this.lblError.TabIndex = 10;
            this.lblError.Text = "ERROR";
            this.lblError.TextAlign = System.Drawing.ContentAlignment.MiddleCenter;
            this.toolTip1.SetToolTip(this.lblError, "Global error Indication");
            // 
            // grpAction
            // 
            this.grpAction.Controls.Add(this.btnPreview);
            this.grpAction.Controls.Add(this.btnLoadHotels);
            this.grpAction.Controls.Add(this.btnEjectHotels);
            this.grpAction.Controls.Add(this.btnToHotel);
            this.grpAction.Controls.Add(this.btnToStage);
            this.grpAction.Enabled = false;
            this.grpAction.Location = new System.Drawing.Point(8, 56);
            this.grpAction.Name = "grpAction";
            this.grpAction.Size = new System.Drawing.Size(128, 355);
            this.grpAction.TabIndex = 816;
            this.grpAction.TabStop = false;
            this.grpAction.Text = "Action";
            // 
            // btnPreview
            // 
            this.btnPreview.Location = new System.Drawing.Point(8, 170);
            this.btnPreview.Name = "btnPreview";
            this.btnPreview.Size = new System.Drawing.Size(110, 30);
            this.btnPreview.TabIndex = 7;
            this.btnPreview.Text = "Preview 1?";
            this.toolTip1.SetToolTip(this.btnPreview, "Acknowlegde a preview point completed.");
            this.btnPreview.UseVisualStyleBackColor = true;
            this.btnPreview.Click += new System.EventHandler(this.btnPreview_Click);
            // 
            // btnLoadHotels
            // 
            this.btnLoadHotels.Location = new System.Drawing.Point(8, 287);
            this.btnLoadHotels.Name = "btnLoadHotels";
            this.btnLoadHotels.Size = new System.Drawing.Size(110, 48);
            this.btnLoadHotels.TabIndex = 10;
            this.btnLoadHotels.Text = "Insert Hotel Shuttle";
            this.toolTip1.SetToolTip(this.btnLoadHotels, "Insert the Hotel Shuttle to the system ready for use.");
            this.btnLoadHotels.UseVisualStyleBackColor = true;
            this.btnLoadHotels.Click += new System.EventHandler(this.btnLoadHotels_Click);
            // 
            // btnEjectHotels
            // 
            this.btnEjectHotels.Location = new System.Drawing.Point(8, 222);
            this.btnEjectHotels.Name = "btnEjectHotels";
            this.btnEjectHotels.Size = new System.Drawing.Size(110, 48);
            this.btnEjectHotels.TabIndex = 9;
            this.btnEjectHotels.Text = "Eject Hotel Shuttle";
            this.toolTip1.SetToolTip(this.btnEjectHotels, "Eject Hotel Shuttle from system so that\r\nhotels can be loaded or unloaded.");
            this.btnEjectHotels.UseVisualStyleBackColor = true;
            this.btnEjectHotels.Click += new System.EventHandler(this.btnEjectHotels_Click);
            // 
            // btnToHotel
            // 
            this.btnToHotel.Location = new System.Drawing.Point(9, 97);
            this.btnToHotel.Name = "btnToHotel";
            this.btnToHotel.Size = new System.Drawing.Size(110, 48);
            this.btnToHotel.TabIndex = 8;
            this.btnToHotel.Text = "Move Tray\r\nTo Hotel";
            this.toolTip1.SetToolTip(this.btnToHotel, "Click here followed by an un-occupied apartment to\r\ntransfer tray on stage to hot" +
        "el");
            this.btnToHotel.UseVisualStyleBackColor = true;
            this.btnToHotel.Click += new System.EventHandler(this.btnToHotel_Click);
            // 
            // btnToStage
            // 
            this.btnToStage.Location = new System.Drawing.Point(9, 37);
            this.btnToStage.Name = "btnToStage";
            this.btnToStage.Size = new System.Drawing.Size(110, 48);
            this.btnToStage.TabIndex = 6;
            this.btnToStage.Text = "Move Tray\r\nTo Stage";
            this.toolTip1.SetToolTip(this.btnToStage, "Click here followed by an occupied apartment to\r\ntransfer that tray to stage.");
            this.btnToStage.UseVisualStyleBackColor = true;
            this.btnToStage.Click += new System.EventHandler(this.btnToStage_Click);
            // 
            // grpHotel1
            // 
            this.grpHotel1.Controls.Add(this.btnScan1);
            this.grpHotel1.Enabled = false;
            this.grpHotel1.Location = new System.Drawing.Point(142, 56);
            this.grpHotel1.Name = "grpHotel1";
            this.grpHotel1.Size = new System.Drawing.Size(100, 547);
            this.grpHotel1.TabIndex = 8;
            this.grpHotel1.TabStop = false;
            this.grpHotel1.Tag = "1";
            this.grpHotel1.Text = "Hotel 1";
            // 
            // btnScan1
            // 
            this.btnScan1.Location = new System.Drawing.Point(9, 511);
            this.btnScan1.Name = "btnScan1";
            this.btnScan1.Size = new System.Drawing.Size(82, 30);
            this.btnScan1.TabIndex = 4;
            this.btnScan1.Text = "Scan";
            this.toolTip1.SetToolTip(this.btnScan1, "determine what apartments have trays");
            this.btnScan1.UseVisualStyleBackColor = true;
            this.btnScan1.Click += new System.EventHandler(this.btnScan1_Click);
            // 
            // btnSingle
            // 
            this.btnSingle.Enabled = false;
            this.btnSingle.Location = new System.Drawing.Point(16, 567);
            this.btnSingle.Name = "btnSingle";
            this.btnSingle.Size = new System.Drawing.Size(110, 30);
            this.btnSingle.TabIndex = 817;
            this.btnSingle.Text = "Single step";
            this.toolTip1.SetToolTip(this.btnSingle, "Perform a single step of the loader when \r\n\'options->singleStep mode\' enabled");
            this.btnSingle.UseVisualStyleBackColor = true;
            this.btnSingle.Click += new System.EventHandler(this.btnSingle_Click);
            // 
            // btnStop
            // 
            this.btnStop.Enabled = false;
            this.btnStop.ForeColor = System.Drawing.Color.Red;
            this.btnStop.Location = new System.Drawing.Point(392, 549);
            this.btnStop.Name = "btnStop";
            this.btnStop.Size = new System.Drawing.Size(110, 48);
            this.btnStop.TabIndex = 818;
            this.btnStop.Text = "Emergency Stop";
            this.toolTip1.SetToolTip(this.btnStop, "Emrgency stop only. NOTE, you will need to \r\nperform an initialisation afterwards" +
        " to \r\nrecover from potentailly compomised tray\r\nposition.");
            this.btnStop.UseVisualStyleBackColor = true;
            this.btnStop.Click += new System.EventHandler(this.btnStop_Click);
            // 
            // grpHotel2
            // 
            this.grpHotel2.Controls.Add(this.btnScan2);
            this.grpHotel2.Enabled = false;
            this.grpHotel2.Location = new System.Drawing.Point(248, 56);
            this.grpHotel2.Name = "grpHotel2";
            this.grpHotel2.Size = new System.Drawing.Size(100, 547);
            this.grpHotel2.TabIndex = 819;
            this.grpHotel2.TabStop = false;
            this.grpHotel2.Tag = "2";
            this.grpHotel2.Text = "Hotel 2";
            // 
            // btnScan2
            // 
            this.btnScan2.Location = new System.Drawing.Point(9, 511);
            this.btnScan2.Name = "btnScan2";
            this.btnScan2.Size = new System.Drawing.Size(82, 30);
            this.btnScan2.TabIndex = 5;
            this.btnScan2.Text = "Scan";
            this.toolTip1.SetToolTip(this.btnScan2, "determine what apartments have trays");
            this.btnScan2.UseVisualStyleBackColor = true;
            this.btnScan2.Click += new System.EventHandler(this.btnScan2_Click);
            // 
            // lblstate
            // 
            this.lblstate.BorderSides = ((System.Windows.Forms.ToolStripStatusLabelBorderSides)((((System.Windows.Forms.ToolStripStatusLabelBorderSides.Left | System.Windows.Forms.ToolStripStatusLabelBorderSides.Top) 
            | System.Windows.Forms.ToolStripStatusLabelBorderSides.Right) 
            | System.Windows.Forms.ToolStripStatusLabelBorderSides.Bottom)));
            this.lblstate.BorderStyle = System.Windows.Forms.Border3DStyle.Sunken;
            this.lblstate.Font = new System.Drawing.Font("Times New Roman", 9F, System.Drawing.FontStyle.Regular, System.Drawing.GraphicsUnit.Point, ((byte)(0)));
            this.lblstate.Name = "lblstate";
            this.lblstate.Size = new System.Drawing.Size(135, 21);
            this.lblstate.Text = "TXF_FROMSTAGE";
            this.lblstate.ToolTipText = "SL160 major state level";
            // 
            // lbltime
            // 
            this.lbltime.BorderSides = ((System.Windows.Forms.ToolStripStatusLabelBorderSides)((((System.Windows.Forms.ToolStripStatusLabelBorderSides.Left | System.Windows.Forms.ToolStripStatusLabelBorderSides.Top) 
            | System.Windows.Forms.ToolStripStatusLabelBorderSides.Right) 
            | System.Windows.Forms.ToolStripStatusLabelBorderSides.Bottom)));
            this.lbltime.BorderStyle = System.Windows.Forms.Border3DStyle.Sunken;
            this.lbltime.Font = new System.Drawing.Font("Times New Roman", 9F, System.Drawing.FontStyle.Regular, System.Drawing.GraphicsUnit.Point, ((byte)(0)));
            this.lbltime.Name = "lbltime";
            this.lbltime.Size = new System.Drawing.Size(32, 21);
            this.lbltime.Text = "12s";
            this.lbltime.ToolTipText = "Time taken to perform last hotel scan or tray transfer";
            // 
            // lblSoakCount
            // 
            this.lblSoakCount.BorderSides = ((System.Windows.Forms.ToolStripStatusLabelBorderSides)((((System.Windows.Forms.ToolStripStatusLabelBorderSides.Left | System.Windows.Forms.ToolStripStatusLabelBorderSides.Top) 
            | System.Windows.Forms.ToolStripStatusLabelBorderSides.Right) 
            | System.Windows.Forms.ToolStripStatusLabelBorderSides.Bottom)));
            this.lblSoakCount.BorderStyle = System.Windows.Forms.Border3DStyle.Sunken;
            this.lblSoakCount.Name = "lblSoakCount";
            this.lblSoakCount.Size = new System.Drawing.Size(4, 21);
            this.lblSoakCount.ToolTipText = "soak cycle counter";
            // 
            // lbllasterror
            // 
            this.lbllasterror.BorderSides = ((System.Windows.Forms.ToolStripStatusLabelBorderSides)((((System.Windows.Forms.ToolStripStatusLabelBorderSides.Left | System.Windows.Forms.ToolStripStatusLabelBorderSides.Top) 
            | System.Windows.Forms.ToolStripStatusLabelBorderSides.Right) 
            | System.Windows.Forms.ToolStripStatusLabelBorderSides.Bottom)));
            this.lbllasterror.BorderStyle = System.Windows.Forms.Border3DStyle.Sunken;
            this.lbllasterror.Font = new System.Drawing.Font("Times New Roman", 9F, System.Drawing.FontStyle.Regular, System.Drawing.GraphicsUnit.Point, ((byte)(0)));
            this.lbllasterror.Name = "lbllasterror";
            this.lbllasterror.Size = new System.Drawing.Size(86, 21);
            this.lbllasterror.Text = "LAST_ERR";
            this.lbllasterror.ToolTipText = "Last reported error. Click to clear.";
            this.lbllasterror.Click += new System.EventHandler(this.lbllasterror_Click);
            // 
            // statusStrip
            // 
            this.statusStrip.Items.AddRange(new System.Windows.Forms.ToolStripItem[] {
            this.lblstate,
            this.lbltime,
            this.lblSoakCount,
            this.lbllasterror});
            this.statusStrip.Location = new System.Drawing.Point(0, 617);
            this.statusStrip.Name = "statusStrip";
            this.statusStrip.ShowItemToolTips = true;
            this.statusStrip.Size = new System.Drawing.Size(549, 26);
            this.statusStrip.TabIndex = 780;
            this.statusStrip.Text = "statusStrip1";
            // 
            // grpNosePiece
            // 
            this.grpNosePiece.Controls.Add(this.MC11_H);
            this.grpNosePiece.Controls.Add(this.MC11_2);
            this.grpNosePiece.Controls.Add(this.MC11_1);
            this.grpNosePiece.Enabled = false;
            this.grpNosePiece.Location = new System.Drawing.Point(570, 281);
            this.grpNosePiece.Margin = new System.Windows.Forms.Padding(4);
            this.grpNosePiece.Name = "grpNosePiece";
            this.grpNosePiece.Padding = new System.Windows.Forms.Padding(4);
            this.grpNosePiece.Size = new System.Drawing.Size(176, 105);
            this.grpNosePiece.TabIndex = 822;
            this.grpNosePiece.TabStop = false;
            this.grpNosePiece.Text = "NosePiece";
            // 
            // MC11_H
            // 
            this.MC11_H.Location = new System.Drawing.Point(12, 23);
            this.MC11_H.Margin = new System.Windows.Forms.Padding(4);
            this.MC11_H.Name = "MC11_H";
            this.MC11_H.Size = new System.Drawing.Size(72, 28);
            this.MC11_H.TabIndex = 55;
            this.MC11_H.Text = "Home";
            this.MC11_H.UseVisualStyleBackColor = true;
            this.MC11_H.Click += new System.EventHandler(this.MC11_H_Click);
            // 
            // MC11_2
            // 
            this.MC11_2.Location = new System.Drawing.Point(60, 59);
            this.MC11_2.Margin = new System.Windows.Forms.Padding(4);
            this.MC11_2.Name = "MC11_2";
            this.MC11_2.Size = new System.Drawing.Size(40, 28);
            this.MC11_2.TabIndex = 54;
            this.MC11_2.Tag = "2";
            this.MC11_2.Text = "2";
            this.MC11_2.UseVisualStyleBackColor = true;
            this.MC11_2.Click += new System.EventHandler(this.MC11_2_Click);
            // 
            // MC11_1
            // 
            this.MC11_1.Location = new System.Drawing.Point(12, 59);
            this.MC11_1.Margin = new System.Windows.Forms.Padding(4);
            this.MC11_1.Name = "MC11_1";
            this.MC11_1.Size = new System.Drawing.Size(40, 28);
            this.MC11_1.TabIndex = 53;
            this.MC11_1.Tag = "1";
            this.MC11_1.Text = "1";
            this.MC11_1.UseVisualStyleBackColor = true;
            this.MC11_1.Click += new System.EventHandler(this.MC11_1_Click);
            // 
            // grpCube
            // 
            this.grpCube.Controls.Add(this.btnCubeShutter);
            this.grpCube.Controls.Add(this.HH313_6);
            this.grpCube.Controls.Add(this.HH313_5);
            this.grpCube.Controls.Add(this.HH313_4);
            this.grpCube.Controls.Add(this.HH313_3);
            this.grpCube.Controls.Add(this.HH313_2);
            this.grpCube.Controls.Add(this.HH313_1);
            this.grpCube.Controls.Add(this.HH313_H);
            this.grpCube.Enabled = false;
            this.grpCube.Location = new System.Drawing.Point(570, 65);
            this.grpCube.Margin = new System.Windows.Forms.Padding(4);
            this.grpCube.Name = "grpCube";
            this.grpCube.Padding = new System.Windows.Forms.Padding(4);
            this.grpCube.Size = new System.Drawing.Size(176, 208);
            this.grpCube.TabIndex = 821;
            this.grpCube.TabStop = false;
            this.grpCube.Text = "Cube";
            // 
            // btnCubeShutter
            // 
            this.btnCubeShutter.Location = new System.Drawing.Point(12, 162);
            this.btnCubeShutter.Margin = new System.Windows.Forms.Padding(4);
            this.btnCubeShutter.Name = "btnCubeShutter";
            this.btnCubeShutter.Size = new System.Drawing.Size(139, 28);
            this.btnCubeShutter.TabIndex = 57;
            this.btnCubeShutter.Tag = "6";
            this.btnCubeShutter.Text = "Shutter Closed";
            this.btnCubeShutter.UseVisualStyleBackColor = true;
            this.btnCubeShutter.Click += new System.EventHandler(this.btnCubeShutter_Click);
            // 
            // HH313_6
            // 
            this.HH313_6.Location = new System.Drawing.Point(111, 108);
            this.HH313_6.Margin = new System.Windows.Forms.Padding(4);
            this.HH313_6.Name = "HH313_6";
            this.HH313_6.Size = new System.Drawing.Size(40, 28);
            this.HH313_6.TabIndex = 56;
            this.HH313_6.Tag = "6";
            this.HH313_6.Text = "6";
            this.HH313_6.UseVisualStyleBackColor = true;
            this.HH313_6.Click += new System.EventHandler(this.HH313_1_Click);
            // 
            // HH313_5
            // 
            this.HH313_5.Location = new System.Drawing.Point(61, 108);
            this.HH313_5.Margin = new System.Windows.Forms.Padding(4);
            this.HH313_5.Name = "HH313_5";
            this.HH313_5.Size = new System.Drawing.Size(40, 28);
            this.HH313_5.TabIndex = 55;
            this.HH313_5.Tag = "5";
            this.HH313_5.Text = "5";
            this.HH313_5.UseVisualStyleBackColor = true;
            this.HH313_5.Click += new System.EventHandler(this.HH313_1_Click);
            // 
            // HH313_4
            // 
            this.HH313_4.Location = new System.Drawing.Point(12, 108);
            this.HH313_4.Margin = new System.Windows.Forms.Padding(4);
            this.HH313_4.Name = "HH313_4";
            this.HH313_4.Size = new System.Drawing.Size(40, 28);
            this.HH313_4.TabIndex = 54;
            this.HH313_4.Tag = "4";
            this.HH313_4.Text = "4";
            this.HH313_4.UseVisualStyleBackColor = true;
            this.HH313_4.Click += new System.EventHandler(this.HH313_1_Click);
            // 
            // HH313_3
            // 
            this.HH313_3.Location = new System.Drawing.Point(111, 63);
            this.HH313_3.Margin = new System.Windows.Forms.Padding(4);
            this.HH313_3.Name = "HH313_3";
            this.HH313_3.Size = new System.Drawing.Size(40, 28);
            this.HH313_3.TabIndex = 53;
            this.HH313_3.Tag = "3";
            this.HH313_3.Text = "3";
            this.HH313_3.UseVisualStyleBackColor = true;
            this.HH313_3.Click += new System.EventHandler(this.HH313_1_Click);
            // 
            // HH313_2
            // 
            this.HH313_2.Location = new System.Drawing.Point(61, 63);
            this.HH313_2.Margin = new System.Windows.Forms.Padding(4);
            this.HH313_2.Name = "HH313_2";
            this.HH313_2.Size = new System.Drawing.Size(40, 28);
            this.HH313_2.TabIndex = 52;
            this.HH313_2.Tag = "2";
            this.HH313_2.Text = "2";
            this.HH313_2.UseVisualStyleBackColor = true;
            this.HH313_2.Click += new System.EventHandler(this.HH313_1_Click);
            // 
            // HH313_1
            // 
            this.HH313_1.Location = new System.Drawing.Point(12, 63);
            this.HH313_1.Margin = new System.Windows.Forms.Padding(4);
            this.HH313_1.Name = "HH313_1";
            this.HH313_1.Size = new System.Drawing.Size(40, 28);
            this.HH313_1.TabIndex = 51;
            this.HH313_1.Tag = "1";
            this.HH313_1.Text = "1";
            this.HH313_1.UseVisualStyleBackColor = true;
            this.HH313_1.Click += new System.EventHandler(this.HH313_1_Click);
            // 
            // HH313_H
            // 
            this.HH313_H.Location = new System.Drawing.Point(12, 28);
            this.HH313_H.Margin = new System.Windows.Forms.Padding(4);
            this.HH313_H.Name = "HH313_H";
            this.HH313_H.Size = new System.Drawing.Size(72, 28);
            this.HH313_H.TabIndex = 50;
            this.HH313_H.Text = "Home";
            this.HH313_H.UseVisualStyleBackColor = true;
            this.HH313_H.Click += new System.EventHandler(this.HH313_H_Click);
            // 
            // grpStage
            // 
            this.grpStage.Controls.Add(this.txtXStep);
            this.grpStage.Controls.Add(this.btnF);
            this.grpStage.Controls.Add(this.btnR);
            this.grpStage.Controls.Add(this.btnH);
            this.grpStage.Controls.Add(this.btnL);
            this.grpStage.Controls.Add(this.btnB);
            this.grpStage.Controls.Add(this.lblY);
            this.grpStage.Controls.Add(this.lblX);
            this.grpStage.Controls.Add(this.label18);
            this.grpStage.Controls.Add(this.label17);
            this.grpStage.Enabled = false;
            this.grpStage.Location = new System.Drawing.Point(570, 399);
            this.grpStage.Margin = new System.Windows.Forms.Padding(4);
            this.grpStage.Name = "grpStage";
            this.grpStage.Padding = new System.Windows.Forms.Padding(4);
            this.grpStage.Size = new System.Drawing.Size(288, 198);
            this.grpStage.TabIndex = 820;
            this.grpStage.TabStop = false;
            this.grpStage.Text = "Stage";
            // 
            // txtXStep
            // 
            this.txtXStep.Location = new System.Drawing.Point(171, 154);
            this.txtXStep.Margin = new System.Windows.Forms.Padding(4);
            this.txtXStep.Name = "txtXStep";
            this.txtXStep.Size = new System.Drawing.Size(71, 22);
            this.txtXStep.TabIndex = 56;
            this.txtXStep.Text = "1000";
            // 
            // btnF
            // 
            this.btnF.Location = new System.Drawing.Point(184, 110);
            this.btnF.Margin = new System.Windows.Forms.Padding(4);
            this.btnF.Name = "btnF";
            this.btnF.Size = new System.Drawing.Size(40, 37);
            this.btnF.TabIndex = 51;
            this.btnF.Text = "F";
            this.btnF.UseVisualStyleBackColor = true;
            this.btnF.Click += new System.EventHandler(this.btnF_Click);
            // 
            // btnR
            // 
            this.btnR.Location = new System.Drawing.Point(232, 66);
            this.btnR.Margin = new System.Windows.Forms.Padding(4);
            this.btnR.Name = "btnR";
            this.btnR.Size = new System.Drawing.Size(40, 37);
            this.btnR.TabIndex = 50;
            this.btnR.Text = "R";
            this.btnR.UseVisualStyleBackColor = true;
            this.btnR.Click += new System.EventHandler(this.btnR_Click);
            // 
            // btnH
            // 
            this.btnH.Location = new System.Drawing.Point(184, 66);
            this.btnH.Margin = new System.Windows.Forms.Padding(4);
            this.btnH.Name = "btnH";
            this.btnH.Size = new System.Drawing.Size(40, 37);
            this.btnH.TabIndex = 49;
            this.btnH.Text = "H";
            this.btnH.UseVisualStyleBackColor = true;
            this.btnH.Click += new System.EventHandler(this.btnH_Click);
            // 
            // btnL
            // 
            this.btnL.Location = new System.Drawing.Point(136, 66);
            this.btnL.Margin = new System.Windows.Forms.Padding(4);
            this.btnL.Name = "btnL";
            this.btnL.Size = new System.Drawing.Size(40, 37);
            this.btnL.TabIndex = 48;
            this.btnL.Text = "L";
            this.btnL.UseVisualStyleBackColor = true;
            this.btnL.Click += new System.EventHandler(this.btnL_Click);
            // 
            // btnB
            // 
            this.btnB.Location = new System.Drawing.Point(184, 22);
            this.btnB.Margin = new System.Windows.Forms.Padding(4);
            this.btnB.Name = "btnB";
            this.btnB.Size = new System.Drawing.Size(40, 37);
            this.btnB.TabIndex = 47;
            this.btnB.Text = "B";
            this.btnB.UseVisualStyleBackColor = true;
            this.btnB.Click += new System.EventHandler(this.btnB_Click);
            // 
            // lblY
            // 
            this.lblY.BorderStyle = System.Windows.Forms.BorderStyle.FixedSingle;
            this.lblY.Location = new System.Drawing.Point(28, 94);
            this.lblY.Margin = new System.Windows.Forms.Padding(4, 0, 4, 0);
            this.lblY.Name = "lblY";
            this.lblY.Size = new System.Drawing.Size(101, 44);
            this.lblY.TabIndex = 4;
            this.lblY.Text = "0";
            this.lblY.TextAlign = System.Drawing.ContentAlignment.MiddleRight;
            // 
            // lblX
            // 
            this.lblX.BorderStyle = System.Windows.Forms.BorderStyle.FixedSingle;
            this.lblX.Location = new System.Drawing.Point(27, 38);
            this.lblX.Margin = new System.Windows.Forms.Padding(4, 0, 4, 0);
            this.lblX.Name = "lblX";
            this.lblX.Size = new System.Drawing.Size(101, 44);
            this.lblX.TabIndex = 3;
            this.lblX.Text = "0";
            this.lblX.TextAlign = System.Drawing.ContentAlignment.MiddleRight;
            // 
            // label18
            // 
            this.label18.AutoSize = true;
            this.label18.Location = new System.Drawing.Point(9, 105);
            this.label18.Margin = new System.Windows.Forms.Padding(4, 0, 4, 0);
            this.label18.Name = "label18";
            this.label18.Size = new System.Drawing.Size(17, 17);
            this.label18.TabIndex = 1;
            this.label18.Text = "Y";
            this.label18.TextAlign = System.Drawing.ContentAlignment.MiddleLeft;
            // 
            // label17
            // 
            this.label17.AutoSize = true;
            this.label17.Location = new System.Drawing.Point(8, 52);
            this.label17.Margin = new System.Windows.Forms.Padding(4, 0, 4, 0);
            this.label17.Name = "label17";
            this.label17.Size = new System.Drawing.Size(17, 17);
            this.label17.TabIndex = 0;
            this.label17.Text = "X";
            this.label17.TextAlign = System.Drawing.ContentAlignment.MiddleLeft;
            // 
            // txtZStep
            // 
            this.txtZStep.Location = new System.Drawing.Point(111, 150);
            this.txtZStep.Margin = new System.Windows.Forms.Padding(4);
            this.txtZStep.Name = "txtZStep";
            this.txtZStep.Size = new System.Drawing.Size(71, 22);
            this.txtZStep.TabIndex = 57;
            this.txtZStep.Text = "10";
            // 
            // btnD
            // 
            this.btnD.Location = new System.Drawing.Point(142, 105);
            this.btnD.Margin = new System.Windows.Forms.Padding(4);
            this.btnD.Name = "btnD";
            this.btnD.Size = new System.Drawing.Size(40, 37);
            this.btnD.TabIndex = 54;
            this.btnD.Text = "D";
            this.btnD.UseVisualStyleBackColor = true;
            this.btnD.Click += new System.EventHandler(this.btnD_Click);
            // 
            // btnZH
            // 
            this.btnZH.Location = new System.Drawing.Point(142, 61);
            this.btnZH.Margin = new System.Windows.Forms.Padding(4);
            this.btnZH.Name = "btnZH";
            this.btnZH.Size = new System.Drawing.Size(40, 37);
            this.btnZH.TabIndex = 53;
            this.btnZH.Text = "H";
            this.btnZH.UseVisualStyleBackColor = true;
            this.btnZH.Click += new System.EventHandler(this.btnZH_Click);
            // 
            // btnU
            // 
            this.btnU.Location = new System.Drawing.Point(142, 21);
            this.btnU.Margin = new System.Windows.Forms.Padding(4);
            this.btnU.Name = "btnU";
            this.btnU.Size = new System.Drawing.Size(40, 37);
            this.btnU.TabIndex = 52;
            this.btnU.Text = "U";
            this.btnU.UseVisualStyleBackColor = true;
            this.btnU.Click += new System.EventHandler(this.btnU_Click);
            // 
            // grpZ
            // 
            this.grpZ.Controls.Add(this.lblZ);
            this.grpZ.Controls.Add(this.txtZStep);
            this.grpZ.Controls.Add(this.label4);
            this.grpZ.Controls.Add(this.btnU);
            this.grpZ.Controls.Add(this.btnD);
            this.grpZ.Controls.Add(this.btnZH);
            this.grpZ.Enabled = false;
            this.grpZ.Location = new System.Drawing.Point(878, 399);
            this.grpZ.Margin = new System.Windows.Forms.Padding(4);
            this.grpZ.Name = "grpZ";
            this.grpZ.Padding = new System.Windows.Forms.Padding(4);
            this.grpZ.Size = new System.Drawing.Size(205, 198);
            this.grpZ.TabIndex = 823;
            this.grpZ.TabStop = false;
            this.grpZ.Text = "Z";
            // 
            // lblZ
            // 
            this.lblZ.BorderStyle = System.Windows.Forms.BorderStyle.FixedSingle;
            this.lblZ.Location = new System.Drawing.Point(33, 54);
            this.lblZ.Margin = new System.Windows.Forms.Padding(4, 0, 4, 0);
            this.lblZ.Name = "lblZ";
            this.lblZ.Size = new System.Drawing.Size(101, 44);
            this.lblZ.TabIndex = 5;
            this.lblZ.Text = "0";
            this.lblZ.TextAlign = System.Drawing.ContentAlignment.MiddleRight;
            // 
            // label4
            // 
            this.label4.AutoSize = true;
            this.label4.Location = new System.Drawing.Point(8, 71);
            this.label4.Margin = new System.Windows.Forms.Padding(4, 0, 4, 0);
            this.label4.Name = "label4";
            this.label4.Size = new System.Drawing.Size(17, 17);
            this.label4.TabIndex = 2;
            this.label4.Text = "Z";
            this.label4.TextAlign = System.Drawing.ContentAlignment.MiddleLeft;
            // 
            // grpLed
            // 
            this.grpLed.Controls.Add(this.lvl4);
            this.grpLed.Controls.Add(this.lvl3);
            this.grpLed.Controls.Add(this.lvl2);
            this.grpLed.Controls.Add(this.lvl1);
            this.grpLed.Controls.Add(this.Label12);
            this.grpLed.Controls.Add(this.Label11);
            this.grpLed.Controls.Add(this.Label10);
            this.grpLed.Controls.Add(this.Label9);
            this.grpLed.Controls.Add(this.lblFluor4);
            this.grpLed.Controls.Add(this.btnLed4);
            this.grpLed.Controls.Add(this.lblFluor3);
            this.grpLed.Controls.Add(this.btnLed3);
            this.grpLed.Controls.Add(this.lblFluor2);
            this.grpLed.Controls.Add(this.btnLed2);
            this.grpLed.Controls.Add(this.lblFluor1);
            this.grpLed.Controls.Add(this.btnLed1);
            this.grpLed.Controls.Add(this.HScrollBar4);
            this.grpLed.Controls.Add(this.HScrollBar3);
            this.grpLed.Controls.Add(this.HScrollBar2);
            this.grpLed.Controls.Add(this.HScrollBar1);
            this.grpLed.Enabled = false;
            this.grpLed.Location = new System.Drawing.Point(766, 65);
            this.grpLed.Margin = new System.Windows.Forms.Padding(4);
            this.grpLed.Name = "grpLed";
            this.grpLed.Padding = new System.Windows.Forms.Padding(4);
            this.grpLed.Size = new System.Drawing.Size(564, 233);
            this.grpLed.TabIndex = 824;
            this.grpLed.TabStop = false;
            this.grpLed.Text = "LED Board 1";
            // 
            // lvl4
            // 
            this.lvl4.BorderStyle = System.Windows.Forms.BorderStyle.FixedSingle;
            this.lvl4.Enabled = false;
            this.lvl4.Location = new System.Drawing.Point(501, 165);
            this.lvl4.Margin = new System.Windows.Forms.Padding(4, 0, 4, 0);
            this.lvl4.Name = "lvl4";
            this.lvl4.Size = new System.Drawing.Size(38, 28);
            this.lvl4.TabIndex = 26;
            this.lvl4.TextAlign = System.Drawing.ContentAlignment.MiddleLeft;
            // 
            // lvl3
            // 
            this.lvl3.BorderStyle = System.Windows.Forms.BorderStyle.FixedSingle;
            this.lvl3.Enabled = false;
            this.lvl3.Location = new System.Drawing.Point(501, 123);
            this.lvl3.Margin = new System.Windows.Forms.Padding(4, 0, 4, 0);
            this.lvl3.Name = "lvl3";
            this.lvl3.Size = new System.Drawing.Size(38, 28);
            this.lvl3.TabIndex = 25;
            this.lvl3.TextAlign = System.Drawing.ContentAlignment.MiddleLeft;
            // 
            // lvl2
            // 
            this.lvl2.BorderStyle = System.Windows.Forms.BorderStyle.FixedSingle;
            this.lvl2.Enabled = false;
            this.lvl2.Location = new System.Drawing.Point(501, 81);
            this.lvl2.Margin = new System.Windows.Forms.Padding(4, 0, 4, 0);
            this.lvl2.Name = "lvl2";
            this.lvl2.Size = new System.Drawing.Size(38, 28);
            this.lvl2.TabIndex = 24;
            this.lvl2.TextAlign = System.Drawing.ContentAlignment.MiddleLeft;
            // 
            // lvl1
            // 
            this.lvl1.BorderStyle = System.Windows.Forms.BorderStyle.FixedSingle;
            this.lvl1.Enabled = false;
            this.lvl1.Location = new System.Drawing.Point(501, 39);
            this.lvl1.Margin = new System.Windows.Forms.Padding(4, 0, 4, 0);
            this.lvl1.Name = "lvl1";
            this.lvl1.Size = new System.Drawing.Size(38, 28);
            this.lvl1.TabIndex = 23;
            this.lvl1.TextAlign = System.Drawing.ContentAlignment.MiddleLeft;
            // 
            // Label12
            // 
            this.Label12.AutoSize = true;
            this.Label12.Location = new System.Drawing.Point(8, 172);
            this.Label12.Margin = new System.Windows.Forms.Padding(4, 0, 4, 0);
            this.Label12.Name = "Label12";
            this.Label12.Size = new System.Drawing.Size(16, 17);
            this.Label12.TabIndex = 22;
            this.Label12.Text = "4";
            // 
            // Label11
            // 
            this.Label11.AutoSize = true;
            this.Label11.Location = new System.Drawing.Point(8, 130);
            this.Label11.Margin = new System.Windows.Forms.Padding(4, 0, 4, 0);
            this.Label11.Name = "Label11";
            this.Label11.Size = new System.Drawing.Size(16, 17);
            this.Label11.TabIndex = 21;
            this.Label11.Text = "3";
            // 
            // Label10
            // 
            this.Label10.AutoSize = true;
            this.Label10.Location = new System.Drawing.Point(8, 87);
            this.Label10.Margin = new System.Windows.Forms.Padding(4, 0, 4, 0);
            this.Label10.Name = "Label10";
            this.Label10.Size = new System.Drawing.Size(16, 17);
            this.Label10.TabIndex = 20;
            this.Label10.Text = "2";
            // 
            // Label9
            // 
            this.Label9.AutoSize = true;
            this.Label9.Location = new System.Drawing.Point(8, 47);
            this.Label9.Margin = new System.Windows.Forms.Padding(4, 0, 4, 0);
            this.Label9.Name = "Label9";
            this.Label9.Size = new System.Drawing.Size(16, 17);
            this.Label9.TabIndex = 19;
            this.Label9.Text = "1";
            // 
            // lblFluor4
            // 
            this.lblFluor4.BorderStyle = System.Windows.Forms.BorderStyle.FixedSingle;
            this.lblFluor4.Enabled = false;
            this.lblFluor4.Location = new System.Drawing.Point(108, 165);
            this.lblFluor4.Margin = new System.Windows.Forms.Padding(4, 0, 4, 0);
            this.lblFluor4.Name = "lblFluor4";
            this.lblFluor4.Size = new System.Drawing.Size(123, 28);
            this.lblFluor4.TabIndex = 16;
            this.lblFluor4.Text = "lblFluor4";
            this.lblFluor4.TextAlign = System.Drawing.ContentAlignment.MiddleLeft;
            // 
            // btnLed4
            // 
            this.btnLed4.Enabled = false;
            this.btnLed4.Location = new System.Drawing.Point(39, 165);
            this.btnLed4.Margin = new System.Windows.Forms.Padding(4);
            this.btnLed4.Name = "btnLed4";
            this.btnLed4.Size = new System.Drawing.Size(61, 28);
            this.btnLed4.TabIndex = 7;
            this.btnLed4.Tag = "4";
            this.btnLed4.UseVisualStyleBackColor = true;
            this.btnLed4.Click += new System.EventHandler(this.btnLed1_Click);
            // 
            // lblFluor3
            // 
            this.lblFluor3.BorderStyle = System.Windows.Forms.BorderStyle.FixedSingle;
            this.lblFluor3.Enabled = false;
            this.lblFluor3.Location = new System.Drawing.Point(108, 123);
            this.lblFluor3.Margin = new System.Windows.Forms.Padding(4, 0, 4, 0);
            this.lblFluor3.Name = "lblFluor3";
            this.lblFluor3.Size = new System.Drawing.Size(123, 28);
            this.lblFluor3.TabIndex = 14;
            this.lblFluor3.Text = "lblFluor3";
            this.lblFluor3.TextAlign = System.Drawing.ContentAlignment.MiddleLeft;
            // 
            // btnLed3
            // 
            this.btnLed3.Enabled = false;
            this.btnLed3.Location = new System.Drawing.Point(39, 123);
            this.btnLed3.Margin = new System.Windows.Forms.Padding(4);
            this.btnLed3.Name = "btnLed3";
            this.btnLed3.Size = new System.Drawing.Size(61, 28);
            this.btnLed3.TabIndex = 5;
            this.btnLed3.Tag = "3";
            this.btnLed3.UseVisualStyleBackColor = true;
            this.btnLed3.Click += new System.EventHandler(this.btnLed1_Click);
            // 
            // lblFluor2
            // 
            this.lblFluor2.BorderStyle = System.Windows.Forms.BorderStyle.FixedSingle;
            this.lblFluor2.Enabled = false;
            this.lblFluor2.Location = new System.Drawing.Point(108, 81);
            this.lblFluor2.Margin = new System.Windows.Forms.Padding(4, 0, 4, 0);
            this.lblFluor2.Name = "lblFluor2";
            this.lblFluor2.Size = new System.Drawing.Size(123, 28);
            this.lblFluor2.TabIndex = 12;
            this.lblFluor2.Text = "lblFluor2";
            this.lblFluor2.TextAlign = System.Drawing.ContentAlignment.MiddleLeft;
            // 
            // btnLed2
            // 
            this.btnLed2.Enabled = false;
            this.btnLed2.Location = new System.Drawing.Point(39, 81);
            this.btnLed2.Margin = new System.Windows.Forms.Padding(4);
            this.btnLed2.Name = "btnLed2";
            this.btnLed2.Size = new System.Drawing.Size(61, 28);
            this.btnLed2.TabIndex = 3;
            this.btnLed2.Tag = "2";
            this.btnLed2.UseVisualStyleBackColor = true;
            this.btnLed2.Click += new System.EventHandler(this.btnLed1_Click);
            // 
            // lblFluor1
            // 
            this.lblFluor1.BorderStyle = System.Windows.Forms.BorderStyle.FixedSingle;
            this.lblFluor1.Enabled = false;
            this.lblFluor1.Location = new System.Drawing.Point(108, 39);
            this.lblFluor1.Margin = new System.Windows.Forms.Padding(4, 0, 4, 0);
            this.lblFluor1.Name = "lblFluor1";
            this.lblFluor1.Size = new System.Drawing.Size(123, 28);
            this.lblFluor1.TabIndex = 10;
            this.lblFluor1.Text = "lblFluor1";
            this.lblFluor1.TextAlign = System.Drawing.ContentAlignment.MiddleLeft;
            // 
            // btnLed1
            // 
            this.btnLed1.Enabled = false;
            this.btnLed1.Location = new System.Drawing.Point(39, 39);
            this.btnLed1.Margin = new System.Windows.Forms.Padding(4);
            this.btnLed1.Name = "btnLed1";
            this.btnLed1.Size = new System.Drawing.Size(61, 28);
            this.btnLed1.TabIndex = 1;
            this.btnLed1.Tag = "1";
            this.btnLed1.UseVisualStyleBackColor = true;
            this.btnLed1.Click += new System.EventHandler(this.btnLed1_Click);
            // 
            // HScrollBar4
            // 
            this.HScrollBar4.Enabled = false;
            this.HScrollBar4.Location = new System.Drawing.Point(255, 165);
            this.HScrollBar4.Maximum = 109;
            this.HScrollBar4.Name = "HScrollBar4";
            this.HScrollBar4.Size = new System.Drawing.Size(229, 23);
            this.HScrollBar4.TabIndex = 8;
            this.HScrollBar4.Tag = "4";
            this.HScrollBar4.ValueChanged += new System.EventHandler(this.HScrollBar1_ValueChanged);
            // 
            // HScrollBar3
            // 
            this.HScrollBar3.Enabled = false;
            this.HScrollBar3.Location = new System.Drawing.Point(255, 123);
            this.HScrollBar3.Maximum = 109;
            this.HScrollBar3.Name = "HScrollBar3";
            this.HScrollBar3.Size = new System.Drawing.Size(229, 23);
            this.HScrollBar3.TabIndex = 6;
            this.HScrollBar3.Tag = "3";
            this.HScrollBar3.ValueChanged += new System.EventHandler(this.HScrollBar1_ValueChanged);
            // 
            // HScrollBar2
            // 
            this.HScrollBar2.Enabled = false;
            this.HScrollBar2.Location = new System.Drawing.Point(255, 81);
            this.HScrollBar2.Maximum = 109;
            this.HScrollBar2.Name = "HScrollBar2";
            this.HScrollBar2.Size = new System.Drawing.Size(229, 23);
            this.HScrollBar2.TabIndex = 4;
            this.HScrollBar2.Tag = "2";
            this.HScrollBar2.ValueChanged += new System.EventHandler(this.HScrollBar1_ValueChanged);
            // 
            // HScrollBar1
            // 
            this.HScrollBar1.Enabled = false;
            this.HScrollBar1.Location = new System.Drawing.Point(255, 39);
            this.HScrollBar1.Maximum = 109;
            this.HScrollBar1.Name = "HScrollBar1";
            this.HScrollBar1.Size = new System.Drawing.Size(229, 21);
            this.HScrollBar1.TabIndex = 2;
            this.HScrollBar1.Tag = "1";
            this.HScrollBar1.ValueChanged += new System.EventHandler(this.HScrollBar1_ValueChanged);
            // 
            // btnShutter4
            // 
            this.btnShutter4.Enabled = false;
            this.btnShutter4.Location = new System.Drawing.Point(766, 340);
            this.btnShutter4.Margin = new System.Windows.Forms.Padding(4);
            this.btnShutter4.Name = "btnShutter4";
            this.btnShutter4.Size = new System.Drawing.Size(139, 28);
            this.btnShutter4.TabIndex = 825;
            this.btnShutter4.Tag = "6";
            this.btnShutter4.Text = "Shutter 4 Closed";
            this.btnShutter4.UseVisualStyleBackColor = true;
            this.btnShutter4.Click += new System.EventHandler(this.btnShutter4_Click);
            // 
            // Form1
            // 
            this.AutoScaleDimensions = new System.Drawing.SizeF(8F, 16F);
            this.AutoScaleMode = System.Windows.Forms.AutoScaleMode.Font;
            this.ClientSize = new System.Drawing.Size(549, 643);
            this.Controls.Add(this.btnShutter4);
            this.Controls.Add(this.grpLed);
            this.Controls.Add(this.grpZ);
            this.Controls.Add(this.grpNosePiece);
            this.Controls.Add(this.grpCube);
            this.Controls.Add(this.grpStage);
            this.Controls.Add(this.grpHotel2);
            this.Controls.Add(this.btnStop);
            this.Controls.Add(this.btnSingle);
            this.Controls.Add(this.grpHotel1);
            this.Controls.Add(this.grpAction);
            this.Controls.Add(this.statusStrip);
            this.Controls.Add(this.grpStatus);
            this.Controls.Add(this.menuStrip1);
            this.FormBorderStyle = System.Windows.Forms.FormBorderStyle.FixedDialog;
            this.Icon = ((System.Drawing.Icon)(resources.GetObject("$this.Icon")));
            this.Location = new System.Drawing.Point(100, 100);
            this.MainMenuStrip = this.menuStrip1;
            this.MaximizeBox = false;
            this.MinimizeBox = false;
            this.Name = "Form1";
            this.StartPosition = System.Windows.Forms.FormStartPosition.Manual;
            this.Text = "SL160_Demo";
            this.FormClosing += new System.Windows.Forms.FormClosingEventHandler(this.Form1_FormClosing);
            this.Load += new System.EventHandler(this.Form1_Load);
            this.menuStrip1.ResumeLayout(false);
            this.menuStrip1.PerformLayout();
            this.grpStatus.ResumeLayout(false);
            this.grpAction.ResumeLayout(false);
            this.grpHotel1.ResumeLayout(false);
            this.grpHotel2.ResumeLayout(false);
            this.statusStrip.ResumeLayout(false);
            this.statusStrip.PerformLayout();
            this.grpNosePiece.ResumeLayout(false);
            this.grpCube.ResumeLayout(false);
            this.grpStage.ResumeLayout(false);
            this.grpStage.PerformLayout();
            this.grpZ.ResumeLayout(false);
            this.grpZ.PerformLayout();
            this.grpLed.ResumeLayout(false);
            this.grpLed.PerformLayout();
            this.ResumeLayout(false);
            this.PerformLayout();

        }

        #endregion

        private System.Windows.Forms.MenuStrip menuStrip1;
        private System.Windows.Forms.ToolStripMenuItem connectToolStripMenuItem;
        private System.Windows.Forms.ToolStripMenuItem editINIToolStripMenuItem;
        public System.Windows.Forms.GroupBox grpStatus;
        public System.Windows.Forms.Label lblStallError;
        public System.Windows.Forms.Label lblSlideSensorError;
        public System.Windows.Forms.Label lblCommsError;
        public System.Windows.Forms.Label lblCassetteNotScanned;
        public System.Windows.Forms.Label lblNotIdle;
        public System.Windows.Forms.Label lblSlideOnStage;
        public System.Windows.Forms.Label lblInvalidCassette;
        public System.Windows.Forms.Label lblInvalidSlide;
        public System.Windows.Forms.Label lblNotSetup;
        public System.Windows.Forms.Label lblNotInitialised;
        public System.Windows.Forms.Label lblNotConnected;
        public System.Windows.Forms.Label lblError;
        private System.Windows.Forms.ToolStripMenuItem optionsToolStripMenuItem;
        private System.Windows.Forms.ToolStripMenuItem singleStepModeToolStripMenuItem;
        private System.Windows.Forms.GroupBox grpAction;
        private System.Windows.Forms.Button btnToHotel;
        private System.Windows.Forms.Button btnToStage;
        private System.Windows.Forms.GroupBox grpHotel1;
        private System.Windows.Forms.ToolStripMenuItem helpToolStripMenuItem;
        private System.Windows.Forms.ToolStripMenuItem doSoakToolStripMenuItem;
        private System.Windows.Forms.Button btnSingle;
        private System.Windows.Forms.Button btnStop;
        private System.Windows.Forms.ToolStripMenuItem loaderINIToolStripMenuItem;
        private System.Windows.Forms.GroupBox grpHotel2;
        private System.Windows.Forms.Button btnLoadHotels;
        private System.Windows.Forms.Button btnEjectHotels;
        private System.Windows.Forms.Button btnPreview;
        private System.Windows.Forms.Button btnScan1;
        private System.Windows.Forms.Button btnScan2;
        private System.Windows.Forms.ToolStripMenuItem loggingToolStripMenuItem;
        private System.Windows.Forms.ToolStripMenuItem enabledToolStripMenuItem;
        private System.Windows.Forms.ToolStripMenuItem scanOnlySoakToolStripMenuItem;
        public System.Windows.Forms.Label lblEject;
        private System.Windows.Forms.ToolStripMenuItem stageRasterEnabledToolStripMenuItem;
        private System.Windows.Forms.ToolStripStatusLabel lblstate;
        private System.Windows.Forms.ToolStripStatusLabel lbltime;
        private System.Windows.Forms.ToolStripStatusLabel lblSoakCount;
        private System.Windows.Forms.ToolStripStatusLabel lbllasterror;
        private System.Windows.Forms.StatusStrip statusStrip;
        private System.Windows.Forms.ToolStripMenuItem redoCalibrationToolStripMenuItem;
        private System.Windows.Forms.ToolStripMenuItem checkCalibrationToolStripMenuItem;
        private System.Windows.Forms.ToolStripMenuItem joystickToolStripMenuItem;
        private System.Windows.Forms.ToolTip toolTip1;
        private System.Windows.Forms.ToolStripMenuItem previewOnToolStripMenuItem;
        private System.Windows.Forms.GroupBox grpNosePiece;
        private System.Windows.Forms.Button MC11_H;
        private System.Windows.Forms.Button MC11_2;
        private System.Windows.Forms.Button MC11_1;
        private System.Windows.Forms.GroupBox grpCube;
        private System.Windows.Forms.Button HH313_6;
        private System.Windows.Forms.Button HH313_5;
        private System.Windows.Forms.Button HH313_4;
        private System.Windows.Forms.Button HH313_3;
        private System.Windows.Forms.Button HH313_2;
        private System.Windows.Forms.Button HH313_1;
        private System.Windows.Forms.Button HH313_H;
        private System.Windows.Forms.GroupBox grpStage;
        private System.Windows.Forms.TextBox txtZStep;
        private System.Windows.Forms.TextBox txtXStep;
        private System.Windows.Forms.Button btnD;
        private System.Windows.Forms.Button btnZH;
        private System.Windows.Forms.Button btnU;
        private System.Windows.Forms.Button btnF;
        private System.Windows.Forms.Button btnR;
        private System.Windows.Forms.Button btnH;
        private System.Windows.Forms.Button btnL;
        private System.Windows.Forms.Button btnB;
        private System.Windows.Forms.Label lblY;
        private System.Windows.Forms.Label lblX;
        private System.Windows.Forms.Label label18;
        private System.Windows.Forms.Label label17;
        private System.Windows.Forms.GroupBox grpZ;
        private System.Windows.Forms.Label lblZ;
        private System.Windows.Forms.Label label4;
        internal System.Windows.Forms.GroupBox grpLed;
        internal System.Windows.Forms.Label lvl4;
        internal System.Windows.Forms.Label lvl3;
        internal System.Windows.Forms.Label lvl2;
        internal System.Windows.Forms.Label lvl1;
        internal System.Windows.Forms.Label Label12;
        internal System.Windows.Forms.Label Label11;
        internal System.Windows.Forms.Label Label10;
        internal System.Windows.Forms.Label Label9;
        internal System.Windows.Forms.Label lblFluor4;
        internal System.Windows.Forms.Button btnLed4;
        internal System.Windows.Forms.Label lblFluor3;
        internal System.Windows.Forms.Button btnLed3;
        internal System.Windows.Forms.Label lblFluor2;
        internal System.Windows.Forms.Button btnLed2;
        internal System.Windows.Forms.Label lblFluor1;
        internal System.Windows.Forms.Button btnLed1;
        internal System.Windows.Forms.HScrollBar HScrollBar4;
        internal System.Windows.Forms.HScrollBar HScrollBar3;
        internal System.Windows.Forms.HScrollBar HScrollBar2;
        internal System.Windows.Forms.HScrollBar HScrollBar1;
        private System.Windows.Forms.Button btnCubeShutter;
        private System.Windows.Forms.Button btnShutter4;
        private System.Windows.Forms.ToolStripMenuItem ReInitialiseToolStripMenuItem;
        private System.Windows.Forms.ToolStripMenuItem ManualoolStripMenuItem;
    }
}

