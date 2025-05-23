namespace SL160_LoaderDemo
{
    partial class redoCalibration
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
            System.ComponentModel.ComponentResourceManager resources = new System.ComponentModel.ComponentResourceManager(typeof(redoCalibration));
            this.btnRedoAll = new System.Windows.Forms.Button();
            this.btnRedoHotel = new System.Windows.Forms.Button();
            this.btnRedoStage = new System.Windows.Forms.Button();
            this.btnCancel = new System.Windows.Forms.Button();
            this.SuspendLayout();
            // 
            // btnRedoAll
            // 
            this.btnRedoAll.Font = new System.Drawing.Font("Microsoft Sans Serif", 12F, System.Drawing.FontStyle.Regular, System.Drawing.GraphicsUnit.Point, ((byte)(0)));
            this.btnRedoAll.Location = new System.Drawing.Point(24, 23);
            this.btnRedoAll.Name = "btnRedoAll";
            this.btnRedoAll.Size = new System.Drawing.Size(451, 65);
            this.btnRedoAll.TabIndex = 0;
            this.btnRedoAll.Text = "Redo ALL calibration";
            this.btnRedoAll.UseVisualStyleBackColor = true;
            this.btnRedoAll.Click += new System.EventHandler(this.btnRedoAll_Click);
            // 
            // btnRedoHotel
            // 
            this.btnRedoHotel.Font = new System.Drawing.Font("Microsoft Sans Serif", 12F, System.Drawing.FontStyle.Regular, System.Drawing.GraphicsUnit.Point, ((byte)(0)));
            this.btnRedoHotel.Location = new System.Drawing.Point(24, 109);
            this.btnRedoHotel.Name = "btnRedoHotel";
            this.btnRedoHotel.Size = new System.Drawing.Size(451, 65);
            this.btnRedoHotel.TabIndex = 1;
            this.btnRedoHotel.Text = "Redo Hotel Calibration ONLY";
            this.btnRedoHotel.UseVisualStyleBackColor = true;
            this.btnRedoHotel.Click += new System.EventHandler(this.btnRedoHotel_Click);
            // 
            // btnRedoStage
            // 
            this.btnRedoStage.Font = new System.Drawing.Font("Microsoft Sans Serif", 12F, System.Drawing.FontStyle.Regular, System.Drawing.GraphicsUnit.Point, ((byte)(0)));
            this.btnRedoStage.Location = new System.Drawing.Point(24, 194);
            this.btnRedoStage.Name = "btnRedoStage";
            this.btnRedoStage.Size = new System.Drawing.Size(451, 65);
            this.btnRedoStage.TabIndex = 2;
            this.btnRedoStage.Text = "Redo Stage Calibration ONLY";
            this.btnRedoStage.UseVisualStyleBackColor = true;
            this.btnRedoStage.Click += new System.EventHandler(this.btnRedoStage_Click);
            // 
            // btnCancel
            // 
            this.btnCancel.Font = new System.Drawing.Font("Microsoft Sans Serif", 12F, System.Drawing.FontStyle.Regular, System.Drawing.GraphicsUnit.Point, ((byte)(0)));
            this.btnCancel.Location = new System.Drawing.Point(24, 285);
            this.btnCancel.Name = "btnCancel";
            this.btnCancel.Size = new System.Drawing.Size(451, 65);
            this.btnCancel.TabIndex = 3;
            this.btnCancel.Text = "Cancel - DO NOTHING";
            this.btnCancel.UseVisualStyleBackColor = true;
            this.btnCancel.Click += new System.EventHandler(this.btnCancel_Click);
            // 
            // redoCalibration
            // 
            this.AutoScaleDimensions = new System.Drawing.SizeF(8F, 16F);
            this.AutoScaleMode = System.Windows.Forms.AutoScaleMode.Font;
            this.ClientSize = new System.Drawing.Size(506, 376);
            this.Controls.Add(this.btnCancel);
            this.Controls.Add(this.btnRedoStage);
            this.Controls.Add(this.btnRedoHotel);
            this.Controls.Add(this.btnRedoAll);
            this.FormBorderStyle = System.Windows.Forms.FormBorderStyle.FixedDialog;
            this.Icon = ((System.Drawing.Icon)(resources.GetObject("$this.Icon")));
            this.Location = new System.Drawing.Point(100, 100);
            this.MaximizeBox = false;
            this.MinimizeBox = false;
            this.Name = "redoCalibration";
            this.ShowInTaskbar = false;
            this.StartPosition = System.Windows.Forms.FormStartPosition.Manual;
            this.Text = "Redo Calibration Options";
            this.Load += new System.EventHandler(this.redoCalibration_Load);
            this.ResumeLayout(false);

        }

        #endregion

        private System.Windows.Forms.Button btnRedoAll;
        private System.Windows.Forms.Button btnRedoHotel;
        private System.Windows.Forms.Button btnRedoStage;
        private System.Windows.Forms.Button btnCancel;
    }
}