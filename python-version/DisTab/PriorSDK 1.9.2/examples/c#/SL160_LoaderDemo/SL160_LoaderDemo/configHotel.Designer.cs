namespace SL160_LoaderDemo
{
    partial class ConfigHotel
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
            System.ComponentModel.ComponentResourceManager resources = new System.ComponentModel.ComponentResourceManager(typeof(ConfigHotel));
            this.btnPrev = new System.Windows.Forms.Button();
            this.btnNext = new System.Windows.Forms.Button();
            this.pbImage = new System.Windows.Forms.PictureBox();
            this.btnHotelIn = new System.Windows.Forms.Button();
            this.btnHotelOut = new System.Windows.Forms.Button();
            this.grpAlign = new System.Windows.Forms.GroupBox();
            this.rb01mm = new System.Windows.Forms.RadioButton();
            this.rb1mm = new System.Windows.Forms.RadioButton();
            this.label3 = new System.Windows.Forms.Label();
            this.grpLift = new System.Windows.Forms.GroupBox();
            this.label2 = new System.Windows.Forms.Label();
            this.btnLift = new System.Windows.Forms.Button();
            this.btnLower = new System.Windows.Forms.Button();
            this.btnQuit = new System.Windows.Forms.Button();
            this.lbInfo = new System.Windows.Forms.ListBox();
            ((System.ComponentModel.ISupportInitialize)(this.pbImage)).BeginInit();
            this.grpAlign.SuspendLayout();
            this.grpLift.SuspendLayout();
            this.SuspendLayout();
            // 
            // btnPrev
            // 
            this.btnPrev.Location = new System.Drawing.Point(12, 633);
            this.btnPrev.Name = "btnPrev";
            this.btnPrev.Size = new System.Drawing.Size(84, 32);
            this.btnPrev.TabIndex = 0;
            this.btnPrev.Text = "Previous";
            this.btnPrev.UseVisualStyleBackColor = true;
            this.btnPrev.Click += new System.EventHandler(this.btnPrev_Click);
            // 
            // btnNext
            // 
            this.btnNext.Location = new System.Drawing.Point(126, 633);
            this.btnNext.Name = "btnNext";
            this.btnNext.Size = new System.Drawing.Size(84, 32);
            this.btnNext.TabIndex = 1;
            this.btnNext.Text = "Next";
            this.btnNext.UseVisualStyleBackColor = true;
            this.btnNext.Click += new System.EventHandler(this.btnNext_Click);
            // 
            // pbImage
            // 
            this.pbImage.BorderStyle = System.Windows.Forms.BorderStyle.Fixed3D;
            this.pbImage.Location = new System.Drawing.Point(12, 12);
            this.pbImage.Name = "pbImage";
            this.pbImage.Size = new System.Drawing.Size(551, 383);
            this.pbImage.SizeMode = System.Windows.Forms.PictureBoxSizeMode.Zoom;
            this.pbImage.TabIndex = 2;
            this.pbImage.TabStop = false;
            // 
            // btnHotelIn
            // 
            this.btnHotelIn.Location = new System.Drawing.Point(18, 200);
            this.btnHotelIn.Name = "btnHotelIn";
            this.btnHotelIn.Size = new System.Drawing.Size(103, 32);
            this.btnHotelIn.TabIndex = 3;
            this.btnHotelIn.Text = "Hotel In";
            this.btnHotelIn.UseVisualStyleBackColor = true;
            this.btnHotelIn.Click += new System.EventHandler(this.btnHotelIn_Click);
            // 
            // btnHotelOut
            // 
            this.btnHotelOut.Location = new System.Drawing.Point(134, 200);
            this.btnHotelOut.Name = "btnHotelOut";
            this.btnHotelOut.Size = new System.Drawing.Size(104, 32);
            this.btnHotelOut.TabIndex = 4;
            this.btnHotelOut.Text = "Hotel Out";
            this.btnHotelOut.UseVisualStyleBackColor = true;
            this.btnHotelOut.Click += new System.EventHandler(this.btnHotelOut_Click);
            // 
            // grpAlign
            // 
            this.grpAlign.Controls.Add(this.rb01mm);
            this.grpAlign.Controls.Add(this.rb1mm);
            this.grpAlign.Controls.Add(this.label3);
            this.grpAlign.Controls.Add(this.btnHotelIn);
            this.grpAlign.Controls.Add(this.btnHotelOut);
            this.grpAlign.Location = new System.Drawing.Point(586, 295);
            this.grpAlign.Name = "grpAlign";
            this.grpAlign.Size = new System.Drawing.Size(254, 255);
            this.grpAlign.TabIndex = 5;
            this.grpAlign.TabStop = false;
            this.grpAlign.Text = "Hotel Alignment";
            // 
            // rb01mm
            // 
            this.rb01mm.AutoSize = true;
            this.rb01mm.Location = new System.Drawing.Point(18, 156);
            this.rb01mm.Name = "rb01mm";
            this.rb01mm.Size = new System.Drawing.Size(98, 21);
            this.rb01mm.TabIndex = 11;
            this.rb01mm.Text = "0.1mm Jog";
            this.rb01mm.UseVisualStyleBackColor = true;
            // 
            // rb1mm
            // 
            this.rb1mm.AutoSize = true;
            this.rb1mm.Checked = true;
            this.rb1mm.Location = new System.Drawing.Point(18, 122);
            this.rb1mm.Name = "rb1mm";
            this.rb1mm.Size = new System.Drawing.Size(86, 21);
            this.rb1mm.TabIndex = 10;
            this.rb1mm.TabStop = true;
            this.rb1mm.Text = "1mm Jog";
            this.rb1mm.UseVisualStyleBackColor = true;
            // 
            // label3
            // 
            this.label3.BorderStyle = System.Windows.Forms.BorderStyle.FixedSingle;
            this.label3.Font = new System.Drawing.Font("Microsoft Sans Serif", 10.2F, System.Drawing.FontStyle.Regular, System.Drawing.GraphicsUnit.Point, ((byte)(0)));
            this.label3.Location = new System.Drawing.Point(18, 32);
            this.label3.Name = "label3";
            this.label3.Size = new System.Drawing.Size(220, 74);
            this.label3.TabIndex = 9;
            this.label3.Text = "jog hotel in and out until aligned with hotel lifting lifting mechanism";
            // 
            // grpLift
            // 
            this.grpLift.Controls.Add(this.label2);
            this.grpLift.Controls.Add(this.btnLift);
            this.grpLift.Controls.Add(this.btnLower);
            this.grpLift.Location = new System.Drawing.Point(586, 36);
            this.grpLift.Name = "grpLift";
            this.grpLift.Size = new System.Drawing.Size(254, 205);
            this.grpLift.TabIndex = 6;
            this.grpLift.TabStop = false;
            this.grpLift.Text = "Hotel Lifting";
            // 
            // label2
            // 
            this.label2.BorderStyle = System.Windows.Forms.BorderStyle.FixedSingle;
            this.label2.Font = new System.Drawing.Font("Microsoft Sans Serif", 10.2F, System.Drawing.FontStyle.Regular, System.Drawing.GraphicsUnit.Point, ((byte)(0)));
            this.label2.Location = new System.Drawing.Point(18, 27);
            this.label2.Name = "label2";
            this.label2.Size = new System.Drawing.Size(220, 74);
            this.label2.TabIndex = 8;
            this.label2.Text = "lift hotel up and down to check alignment";
            // 
            // btnLift
            // 
            this.btnLift.Location = new System.Drawing.Point(20, 136);
            this.btnLift.Name = "btnLift";
            this.btnLift.Size = new System.Drawing.Size(103, 32);
            this.btnLift.TabIndex = 3;
            this.btnLift.Text = "Lift Hotel";
            this.btnLift.UseVisualStyleBackColor = true;
            this.btnLift.Click += new System.EventHandler(this.btnLift_Click);
            // 
            // btnLower
            // 
            this.btnLower.Location = new System.Drawing.Point(134, 136);
            this.btnLower.Name = "btnLower";
            this.btnLower.Size = new System.Drawing.Size(104, 32);
            this.btnLower.TabIndex = 4;
            this.btnLower.Text = "Lower Hotel";
            this.btnLower.UseVisualStyleBackColor = true;
            this.btnLower.Click += new System.EventHandler(this.btnLower_Click);
            // 
            // btnQuit
            // 
            this.btnQuit.Location = new System.Drawing.Point(479, 633);
            this.btnQuit.Name = "btnQuit";
            this.btnQuit.Size = new System.Drawing.Size(84, 32);
            this.btnQuit.TabIndex = 8;
            this.btnQuit.Text = "Quit";
            this.btnQuit.UseVisualStyleBackColor = true;
            this.btnQuit.Click += new System.EventHandler(this.btnQuit_Click);
            // 
            // lbInfo
            // 
            this.lbInfo.Font = new System.Drawing.Font("Microsoft Sans Serif", 10.2F, System.Drawing.FontStyle.Regular, System.Drawing.GraphicsUnit.Point, ((byte)(0)));
            this.lbInfo.FormattingEnabled = true;
            this.lbInfo.ItemHeight = 20;
            this.lbInfo.Items.AddRange(new object[] {
            "1",
            "2",
            "3",
            "4",
            "5",
            "6",
            "7",
            "Use controls opposite to position the shuttle and test the lift."});
            this.lbInfo.Location = new System.Drawing.Point(12, 417);
            this.lbInfo.Name = "lbInfo";
            this.lbInfo.Size = new System.Drawing.Size(551, 204);
            this.lbInfo.TabIndex = 16;
            // 
            // ConfigHotel
            // 
            this.AutoScaleDimensions = new System.Drawing.SizeF(8F, 16F);
            this.AutoScaleMode = System.Windows.Forms.AutoScaleMode.Font;
            this.ClientSize = new System.Drawing.Size(852, 673);
            this.Controls.Add(this.lbInfo);
            this.Controls.Add(this.btnQuit);
            this.Controls.Add(this.grpLift);
            this.Controls.Add(this.grpAlign);
            this.Controls.Add(this.pbImage);
            this.Controls.Add(this.btnNext);
            this.Controls.Add(this.btnPrev);
            this.Icon = ((System.Drawing.Icon)(resources.GetObject("$this.Icon")));
            this.Location = new System.Drawing.Point(100, 100);
            this.MaximizeBox = false;
            this.MinimizeBox = false;
            this.Name = "ConfigHotel";
            this.ShowInTaskbar = false;
            this.Text = "Calibrate Hotel Step 6";
            this.Load += new System.EventHandler(this.ConfigHotel_Load);
            ((System.ComponentModel.ISupportInitialize)(this.pbImage)).EndInit();
            this.grpAlign.ResumeLayout(false);
            this.grpAlign.PerformLayout();
            this.grpLift.ResumeLayout(false);
            this.ResumeLayout(false);

        }

        #endregion

        private System.Windows.Forms.Button btnPrev;
        private System.Windows.Forms.Button btnNext;
        private System.Windows.Forms.PictureBox pbImage;
        private System.Windows.Forms.Button btnHotelIn;
        private System.Windows.Forms.Button btnHotelOut;
        private System.Windows.Forms.GroupBox grpAlign;
        private System.Windows.Forms.GroupBox grpLift;
        private System.Windows.Forms.Button btnLift;
        private System.Windows.Forms.Button btnLower;
        private System.Windows.Forms.Label label3;
        private System.Windows.Forms.Label label2;
        private System.Windows.Forms.Button btnQuit;
        private System.Windows.Forms.RadioButton rb01mm;
        private System.Windows.Forms.RadioButton rb1mm;
        private System.Windows.Forms.ListBox lbInfo;
    }
}