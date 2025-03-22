namespace SL160_LoaderDemo
{
    partial class ConfigStage
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
            System.ComponentModel.ComponentResourceManager resources = new System.ComponentModel.ComponentResourceManager(typeof(ConfigStage));
            this.btnQuit = new System.Windows.Forms.Button();
            this.pbImage = new System.Windows.Forms.PictureBox();
            this.btnNext = new System.Windows.Forms.Button();
            this.btnPrev = new System.Windows.Forms.Button();
            this.grpLift = new System.Windows.Forms.GroupBox();
            this.label2 = new System.Windows.Forms.Label();
            this.rbLift01 = new System.Windows.Forms.RadioButton();
            this.rbLift1 = new System.Windows.Forms.RadioButton();
            this.btnLift = new System.Windows.Forms.Button();
            this.btnLower = new System.Windows.Forms.Button();
            this.grpShuttle = new System.Windows.Forms.GroupBox();
            this.label3 = new System.Windows.Forms.Label();
            this.rbShuttle5 = new System.Windows.Forms.RadioButton();
            this.rbShuttle01 = new System.Windows.Forms.RadioButton();
            this.rbShuttle1 = new System.Windows.Forms.RadioButton();
            this.btnExtend = new System.Windows.Forms.Button();
            this.btnRetract = new System.Windows.Forms.Button();
            this.lbInfo = new System.Windows.Forms.ListBox();
            ((System.ComponentModel.ISupportInitialize)(this.pbImage)).BeginInit();
            this.grpLift.SuspendLayout();
            this.grpShuttle.SuspendLayout();
            this.SuspendLayout();
            // 
            // btnQuit
            // 
            this.btnQuit.Location = new System.Drawing.Point(531, 642);
            this.btnQuit.Name = "btnQuit";
            this.btnQuit.Size = new System.Drawing.Size(84, 32);
            this.btnQuit.TabIndex = 14;
            this.btnQuit.Text = "Quit";
            this.btnQuit.UseVisualStyleBackColor = true;
            this.btnQuit.Click += new System.EventHandler(this.btnQuit_Click);
            // 
            // pbImage
            // 
            this.pbImage.BorderStyle = System.Windows.Forms.BorderStyle.Fixed3D;
            this.pbImage.Location = new System.Drawing.Point(12, 12);
            this.pbImage.Name = "pbImage";
            this.pbImage.Size = new System.Drawing.Size(603, 383);
            this.pbImage.SizeMode = System.Windows.Forms.PictureBoxSizeMode.Zoom;
            this.pbImage.TabIndex = 12;
            this.pbImage.TabStop = false;
            // 
            // btnNext
            // 
            this.btnNext.Location = new System.Drawing.Point(123, 642);
            this.btnNext.Name = "btnNext";
            this.btnNext.Size = new System.Drawing.Size(84, 32);
            this.btnNext.TabIndex = 11;
            this.btnNext.Text = "Next";
            this.btnNext.UseVisualStyleBackColor = true;
            this.btnNext.Click += new System.EventHandler(this.btnNext_Click);
            // 
            // btnPrev
            // 
            this.btnPrev.Location = new System.Drawing.Point(12, 642);
            this.btnPrev.Name = "btnPrev";
            this.btnPrev.Size = new System.Drawing.Size(84, 32);
            this.btnPrev.TabIndex = 10;
            this.btnPrev.Text = "Previous";
            this.btnPrev.UseVisualStyleBackColor = true;
            this.btnPrev.Click += new System.EventHandler(this.btnPrev_Click);
            // 
            // grpLift
            // 
            this.grpLift.Controls.Add(this.label2);
            this.grpLift.Controls.Add(this.rbLift01);
            this.grpLift.Controls.Add(this.rbLift1);
            this.grpLift.Controls.Add(this.btnLift);
            this.grpLift.Controls.Add(this.btnLower);
            this.grpLift.Location = new System.Drawing.Point(666, 12);
            this.grpLift.Name = "grpLift";
            this.grpLift.Size = new System.Drawing.Size(255, 255);
            this.grpLift.TabIndex = 16;
            this.grpLift.TabStop = false;
            this.grpLift.Text = "Hotel Lift Position Adjust";
            // 
            // label2
            // 
            this.label2.BorderStyle = System.Windows.Forms.BorderStyle.FixedSingle;
            this.label2.Font = new System.Drawing.Font("Microsoft Sans Serif", 10.2F, System.Drawing.FontStyle.Regular, System.Drawing.GraphicsUnit.Point, ((byte)(0)));
            this.label2.Location = new System.Drawing.Point(13, 39);
            this.label2.Name = "label2";
            this.label2.Size = new System.Drawing.Size(220, 74);
            this.label2.TabIndex = 18;
            this.label2.Text = "click to fine adjust hotel position with respect to tray.";
            // 
            // rbLift01
            // 
            this.rbLift01.AutoSize = true;
            this.rbLift01.Location = new System.Drawing.Point(18, 165);
            this.rbLift01.Name = "rbLift01";
            this.rbLift01.Size = new System.Drawing.Size(98, 21);
            this.rbLift01.TabIndex = 11;
            this.rbLift01.Text = "0.1mm Jog";
            this.rbLift01.UseVisualStyleBackColor = true;
            // 
            // rbLift1
            // 
            this.rbLift1.AutoSize = true;
            this.rbLift1.Checked = true;
            this.rbLift1.Location = new System.Drawing.Point(18, 126);
            this.rbLift1.Name = "rbLift1";
            this.rbLift1.Size = new System.Drawing.Size(86, 21);
            this.rbLift1.TabIndex = 10;
            this.rbLift1.TabStop = true;
            this.rbLift1.Text = "1mm Jog";
            this.rbLift1.UseVisualStyleBackColor = true;
            // 
            // btnLift
            // 
            this.btnLift.Location = new System.Drawing.Point(18, 207);
            this.btnLift.Name = "btnLift";
            this.btnLift.Size = new System.Drawing.Size(103, 32);
            this.btnLift.TabIndex = 3;
            this.btnLift.Text = "Lift Hotel";
            this.btnLift.UseVisualStyleBackColor = true;
            this.btnLift.Click += new System.EventHandler(this.btnLift_Click);
            // 
            // btnLower
            // 
            this.btnLower.Location = new System.Drawing.Point(135, 207);
            this.btnLower.Name = "btnLower";
            this.btnLower.Size = new System.Drawing.Size(104, 32);
            this.btnLower.TabIndex = 4;
            this.btnLower.Text = "Lower Hotel";
            this.btnLower.UseVisualStyleBackColor = true;
            this.btnLower.Click += new System.EventHandler(this.btnLower_Click);
            // 
            // grpShuttle
            // 
            this.grpShuttle.Controls.Add(this.label3);
            this.grpShuttle.Controls.Add(this.rbShuttle5);
            this.grpShuttle.Controls.Add(this.rbShuttle01);
            this.grpShuttle.Controls.Add(this.rbShuttle1);
            this.grpShuttle.Controls.Add(this.btnExtend);
            this.grpShuttle.Controls.Add(this.btnRetract);
            this.grpShuttle.Location = new System.Drawing.Point(666, 295);
            this.grpShuttle.Name = "grpShuttle";
            this.grpShuttle.Size = new System.Drawing.Size(255, 261);
            this.grpShuttle.TabIndex = 17;
            this.grpShuttle.TabStop = false;
            this.grpShuttle.Text = "Stage Shuttle Position Adjust";
            // 
            // label3
            // 
            this.label3.BorderStyle = System.Windows.Forms.BorderStyle.FixedSingle;
            this.label3.Font = new System.Drawing.Font("Microsoft Sans Serif", 10.2F, System.Drawing.FontStyle.Regular, System.Drawing.GraphicsUnit.Point, ((byte)(0)));
            this.label3.Location = new System.Drawing.Point(13, 28);
            this.label3.Name = "label3";
            this.label3.Size = new System.Drawing.Size(220, 74);
            this.label3.TabIndex = 13;
            this.label3.Text = "Press and hold button to drive shuttle at selected speed. Release to stop.";
            // 
            // rbShuttle5
            // 
            this.rbShuttle5.AutoSize = true;
            this.rbShuttle5.Checked = true;
            this.rbShuttle5.Location = new System.Drawing.Point(18, 110);
            this.rbShuttle5.Name = "rbShuttle5";
            this.rbShuttle5.Size = new System.Drawing.Size(70, 21);
            this.rbShuttle5.TabIndex = 12;
            this.rbShuttle5.TabStop = true;
            this.rbShuttle5.Text = "5mm/s";
            this.rbShuttle5.UseVisualStyleBackColor = true;
            // 
            // rbShuttle01
            // 
            this.rbShuttle01.AutoSize = true;
            this.rbShuttle01.Location = new System.Drawing.Point(18, 164);
            this.rbShuttle01.Name = "rbShuttle01";
            this.rbShuttle01.Size = new System.Drawing.Size(82, 21);
            this.rbShuttle01.TabIndex = 11;
            this.rbShuttle01.Text = "0.1mm/s";
            this.rbShuttle01.UseVisualStyleBackColor = true;
            // 
            // rbShuttle1
            // 
            this.rbShuttle1.AutoSize = true;
            this.rbShuttle1.Location = new System.Drawing.Point(18, 137);
            this.rbShuttle1.Name = "rbShuttle1";
            this.rbShuttle1.Size = new System.Drawing.Size(70, 21);
            this.rbShuttle1.TabIndex = 10;
            this.rbShuttle1.Text = "1mm/s";
            this.rbShuttle1.UseVisualStyleBackColor = true;
            // 
            // btnExtend
            // 
            this.btnExtend.Location = new System.Drawing.Point(13, 205);
            this.btnExtend.Name = "btnExtend";
            this.btnExtend.Size = new System.Drawing.Size(103, 44);
            this.btnExtend.TabIndex = 3;
            this.btnExtend.Text = "Shuttle Extend";
            this.btnExtend.UseVisualStyleBackColor = true;
            this.btnExtend.MouseDown += new System.Windows.Forms.MouseEventHandler(this.btnExtend_MouseDown);
            this.btnExtend.MouseLeave += new System.EventHandler(this.btnExtend_MouseLeave);
            this.btnExtend.MouseUp += new System.Windows.Forms.MouseEventHandler(this.btnExtend_MouseUp);
            // 
            // btnRetract
            // 
            this.btnRetract.Location = new System.Drawing.Point(135, 205);
            this.btnRetract.Name = "btnRetract";
            this.btnRetract.Size = new System.Drawing.Size(104, 44);
            this.btnRetract.TabIndex = 4;
            this.btnRetract.Text = "Shuttle Retract";
            this.btnRetract.UseVisualStyleBackColor = true;
            this.btnRetract.MouseDown += new System.Windows.Forms.MouseEventHandler(this.btnRetract_MouseDown);
            this.btnRetract.MouseLeave += new System.EventHandler(this.btnRetract_MouseLeave);
            this.btnRetract.MouseUp += new System.Windows.Forms.MouseEventHandler(this.btnRetract_MouseUp);
            // 
            // lbInfo
            // 
            this.lbInfo.Font = new System.Drawing.Font("Microsoft Sans Serif", 10.2F, System.Drawing.FontStyle.Regular, System.Drawing.GraphicsUnit.Point, ((byte)(0)));
            this.lbInfo.FormattingEnabled = true;
            this.lbInfo.ItemHeight = 20;
            this.lbInfo.Items.AddRange(new object[] {
            "MICROSCOPE VARIABLE STAGE HEIGHT SYSTEM:",
            "\"It should be used for a variable height stage controlled by users.",
            " microscope. User is responsible for establishing this height position",
            " and faithfully moving to it before loading/unloading trays.",
            "It should be used for a fixed height stage such as when using an OpenStand."});
            this.lbInfo.Location = new System.Drawing.Point(12, 417);
            this.lbInfo.Name = "lbInfo";
            this.lbInfo.Size = new System.Drawing.Size(603, 204);
            this.lbInfo.TabIndex = 18;
            // 
            // ConfigStage
            // 
            this.AutoScaleDimensions = new System.Drawing.SizeF(8F, 16F);
            this.AutoScaleMode = System.Windows.Forms.AutoScaleMode.Font;
            this.ClientSize = new System.Drawing.Size(953, 695);
            this.Controls.Add(this.lbInfo);
            this.Controls.Add(this.grpShuttle);
            this.Controls.Add(this.grpLift);
            this.Controls.Add(this.btnQuit);
            this.Controls.Add(this.pbImage);
            this.Controls.Add(this.btnNext);
            this.Controls.Add(this.btnPrev);
            this.FormBorderStyle = System.Windows.Forms.FormBorderStyle.FixedDialog;
            this.Icon = ((System.Drawing.Icon)(resources.GetObject("$this.Icon")));
            this.Location = new System.Drawing.Point(100, 100);
            this.MaximizeBox = false;
            this.MinimizeBox = false;
            this.Name = "ConfigStage";
            this.ShowInTaskbar = false;
            this.StartPosition = System.Windows.Forms.FormStartPosition.Manual;
            this.Text = "Calibrate Stage Step n";
            this.Load += new System.EventHandler(this.ConfigStage_Load);
            ((System.ComponentModel.ISupportInitialize)(this.pbImage)).EndInit();
            this.grpLift.ResumeLayout(false);
            this.grpLift.PerformLayout();
            this.grpShuttle.ResumeLayout(false);
            this.grpShuttle.PerformLayout();
            this.ResumeLayout(false);

        }

        #endregion

        private System.Windows.Forms.Button btnQuit;
        private System.Windows.Forms.PictureBox pbImage;
        private System.Windows.Forms.Button btnNext;
        private System.Windows.Forms.Button btnPrev;
        private System.Windows.Forms.GroupBox grpLift;
        private System.Windows.Forms.RadioButton rbLift01;
        private System.Windows.Forms.RadioButton rbLift1;
        private System.Windows.Forms.Button btnLift;
        private System.Windows.Forms.Button btnLower;
        private System.Windows.Forms.GroupBox grpShuttle;
        private System.Windows.Forms.RadioButton rbShuttle01;
        private System.Windows.Forms.RadioButton rbShuttle1;
        private System.Windows.Forms.Button btnExtend;
        private System.Windows.Forms.Button btnRetract;
        private System.Windows.Forms.RadioButton rbShuttle5;
        private System.Windows.Forms.Label label2;
        private System.Windows.Forms.Label label3;
        private System.Windows.Forms.ListBox lbInfo;
    }
}