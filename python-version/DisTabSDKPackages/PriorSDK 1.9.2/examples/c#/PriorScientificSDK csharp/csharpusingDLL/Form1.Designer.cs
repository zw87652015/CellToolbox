namespace csharpusingDLL
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
            this.lblVers = new System.Windows.Forms.Label();
            this.label2 = new System.Windows.Forms.Label();
            this.label3 = new System.Windows.Forms.Label();
            this.lblStage = new System.Windows.Forms.Label();
            this.label5 = new System.Windows.Forms.Label();
            this.lblZ = new System.Windows.Forms.Label();
            this.label1 = new System.Windows.Forms.Label();
            this.lblStagepos = new System.Windows.Forms.Label();
            this.label4 = new System.Windows.Forms.Label();
            this.lblZpos = new System.Windows.Forms.Label();
            this.button1 = new System.Windows.Forms.Button();
            this.btnRaster = new System.Windows.Forms.Button();
            this.timer1 = new System.Windows.Forms.Timer(this.components);
            this.SuspendLayout();
            // 
            // lblVers
            // 
            this.lblVers.AutoSize = true;
            this.lblVers.BorderStyle = System.Windows.Forms.BorderStyle.Fixed3D;
            this.lblVers.Location = new System.Drawing.Point(171, 38);
            this.lblVers.Name = "lblVers";
            this.lblVers.Size = new System.Drawing.Size(53, 19);
            this.lblVers.TabIndex = 0;
            this.lblVers.Text = "lblVers";
            // 
            // label2
            // 
            this.label2.AutoSize = true;
            this.label2.Location = new System.Drawing.Point(79, 38);
            this.label2.Name = "label2";
            this.label2.Size = new System.Drawing.Size(86, 17);
            this.label2.TabIndex = 1;
            this.label2.Text = "DLL Version";
            // 
            // label3
            // 
            this.label3.AutoSize = true;
            this.label3.Location = new System.Drawing.Point(79, 74);
            this.label3.Name = "label3";
            this.label3.Size = new System.Drawing.Size(45, 17);
            this.label3.TabIndex = 3;
            this.label3.Text = "Stage";
            // 
            // lblStage
            // 
            this.lblStage.AutoSize = true;
            this.lblStage.BorderStyle = System.Windows.Forms.BorderStyle.Fixed3D;
            this.lblStage.Location = new System.Drawing.Point(171, 74);
            this.lblStage.Name = "lblStage";
            this.lblStage.Size = new System.Drawing.Size(48, 19);
            this.lblStage.TabIndex = 2;
            this.lblStage.Text = "label4";
            // 
            // label5
            // 
            this.label5.AutoSize = true;
            this.label5.Location = new System.Drawing.Point(79, 108);
            this.label5.Name = "label5";
            this.label5.Size = new System.Drawing.Size(46, 17);
            this.label5.TabIndex = 5;
            this.label5.Text = "Focus";
            // 
            // lblZ
            // 
            this.lblZ.AutoSize = true;
            this.lblZ.BorderStyle = System.Windows.Forms.BorderStyle.Fixed3D;
            this.lblZ.Location = new System.Drawing.Point(171, 108);
            this.lblZ.Name = "lblZ";
            this.lblZ.Size = new System.Drawing.Size(48, 19);
            this.lblZ.TabIndex = 4;
            this.lblZ.Text = "label6";
            // 
            // label1
            // 
            this.label1.AutoSize = true;
            this.label1.Location = new System.Drawing.Point(79, 165);
            this.label1.Name = "label1";
            this.label1.Size = new System.Drawing.Size(53, 17);
            this.label1.TabIndex = 7;
            this.label1.Text = "XY pos";
            // 
            // lblStagepos
            // 
            this.lblStagepos.AutoSize = true;
            this.lblStagepos.BorderStyle = System.Windows.Forms.BorderStyle.Fixed3D;
            this.lblStagepos.Location = new System.Drawing.Point(171, 165);
            this.lblStagepos.Name = "lblStagepos";
            this.lblStagepos.Size = new System.Drawing.Size(48, 19);
            this.lblStagepos.TabIndex = 6;
            this.lblStagepos.Text = "label6";
            // 
            // label4
            // 
            this.label4.AutoSize = true;
            this.label4.Location = new System.Drawing.Point(79, 207);
            this.label4.Name = "label4";
            this.label4.Size = new System.Drawing.Size(44, 17);
            this.label4.TabIndex = 9;
            this.label4.Text = "Z pos";
            // 
            // lblZpos
            // 
            this.lblZpos.AutoSize = true;
            this.lblZpos.BorderStyle = System.Windows.Forms.BorderStyle.Fixed3D;
            this.lblZpos.Location = new System.Drawing.Point(171, 207);
            this.lblZpos.Name = "lblZpos";
            this.lblZpos.Size = new System.Drawing.Size(48, 19);
            this.lblZpos.TabIndex = 8;
            this.lblZpos.Text = "label6";
            // 
            // button1
            // 
            this.button1.Location = new System.Drawing.Point(70, 310);
            this.button1.Name = "button1";
            this.button1.Size = new System.Drawing.Size(228, 36);
            this.button1.TabIndex = 10;
            this.button1.Text = "initialise Init stage and focus";
            this.button1.UseVisualStyleBackColor = true;
            this.button1.Click += new System.EventHandler(this.button1_Click);
            // 
            // btnRaster
            // 
            this.btnRaster.Location = new System.Drawing.Point(70, 370);
            this.btnRaster.Name = "btnRaster";
            this.btnRaster.Size = new System.Drawing.Size(228, 36);
            this.btnRaster.TabIndex = 13;
            this.btnRaster.Text = "stage raster";
            this.btnRaster.UseVisualStyleBackColor = true;
            this.btnRaster.Click += new System.EventHandler(this.btnRaster_Click);
            // 
            // timer1
            // 
            this.timer1.Tick += new System.EventHandler(this.timer1_Tick);
            // 
            // Form1
            // 
            this.AutoScaleDimensions = new System.Drawing.SizeF(8F, 16F);
            this.AutoScaleMode = System.Windows.Forms.AutoScaleMode.Font;
            this.ClientSize = new System.Drawing.Size(723, 458);
            this.Controls.Add(this.btnRaster);
            this.Controls.Add(this.button1);
            this.Controls.Add(this.label4);
            this.Controls.Add(this.lblZpos);
            this.Controls.Add(this.label1);
            this.Controls.Add(this.lblStagepos);
            this.Controls.Add(this.label5);
            this.Controls.Add(this.lblZ);
            this.Controls.Add(this.label3);
            this.Controls.Add(this.lblStage);
            this.Controls.Add(this.label2);
            this.Controls.Add(this.lblVers);
            this.Margin = new System.Windows.Forms.Padding(4);
            this.Name = "Form1";
            this.Text = "priorSDK example";
            this.FormClosing += new System.Windows.Forms.FormClosingEventHandler(this.Form1_FormClosing);
            this.Load += new System.EventHandler(this.Form1_Load);
            this.ResumeLayout(false);
            this.PerformLayout();

        }

        #endregion

        private System.Windows.Forms.Label lblVers;
        private System.Windows.Forms.Label label2;
        private System.Windows.Forms.Label label3;
        private System.Windows.Forms.Label lblStage;
        private System.Windows.Forms.Label label5;
        private System.Windows.Forms.Label lblZ;
        private System.Windows.Forms.Label label1;
        private System.Windows.Forms.Label lblStagepos;
        private System.Windows.Forms.Label label4;
        private System.Windows.Forms.Label lblZpos;
        private System.Windows.Forms.Button button1;
        private System.Windows.Forms.Button btnRaster;
        private System.Windows.Forms.Timer timer1;
    }
}

