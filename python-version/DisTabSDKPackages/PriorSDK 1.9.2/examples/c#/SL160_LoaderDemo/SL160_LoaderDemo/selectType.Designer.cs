namespace SL160_LoaderDemo
{
    partial class selectType
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
            System.ComponentModel.ComponentResourceManager resources = new System.ComponentModel.ComponentResourceManager(typeof(selectType));
            this.btnFHS = new System.Windows.Forms.Button();
            this.btnCCVHS = new System.Windows.Forms.Button();
            this.btnPCVHS = new System.Windows.Forms.Button();
            this.label1 = new System.Windows.Forms.Label();
            this.SuspendLayout();
            // 
            // btnFHS
            // 
            this.btnFHS.Font = new System.Drawing.Font("Microsoft Sans Serif", 13.8F, System.Drawing.FontStyle.Regular, System.Drawing.GraphicsUnit.Point, ((byte)(0)));
            this.btnFHS.Location = new System.Drawing.Point(24, 34);
            this.btnFHS.Name = "btnFHS";
            this.btnFHS.Size = new System.Drawing.Size(511, 87);
            this.btnFHS.TabIndex = 0;
            this.btnFHS.Text = "Fixed Height Stage";
            this.btnFHS.UseVisualStyleBackColor = true;
            this.btnFHS.Click += new System.EventHandler(this.btnFHS_Click);
            // 
            // btnCCVHS
            // 
            this.btnCCVHS.Font = new System.Drawing.Font("Microsoft Sans Serif", 13.8F, System.Drawing.FontStyle.Regular, System.Drawing.GraphicsUnit.Point, ((byte)(0)));
            this.btnCCVHS.Location = new System.Drawing.Point(24, 139);
            this.btnCCVHS.Name = "btnCCVHS";
            this.btnCCVHS.Size = new System.Drawing.Size(511, 87);
            this.btnCCVHS.TabIndex = 1;
            this.btnCCVHS.Text = "Customer Controlled Variable Height Stage";
            this.btnCCVHS.UseVisualStyleBackColor = true;
            this.btnCCVHS.Click += new System.EventHandler(this.btnCCVHS_Click);
            // 
            // btnPCVHS
            // 
            this.btnPCVHS.Font = new System.Drawing.Font("Microsoft Sans Serif", 13.8F, System.Drawing.FontStyle.Regular, System.Drawing.GraphicsUnit.Point, ((byte)(0)));
            this.btnPCVHS.Location = new System.Drawing.Point(24, 244);
            this.btnPCVHS.Name = "btnPCVHS";
            this.btnPCVHS.Size = new System.Drawing.Size(511, 87);
            this.btnPCVHS.TabIndex = 2;
            this.btnPCVHS.Text = "ProScan Controlled Variable Height Stage";
            this.btnPCVHS.UseVisualStyleBackColor = true;
            this.btnPCVHS.Click += new System.EventHandler(this.btnPCVHS_Click);
            // 
            // label1
            // 
            this.label1.Font = new System.Drawing.Font("Microsoft Sans Serif", 10.2F, System.Drawing.FontStyle.Regular, System.Drawing.GraphicsUnit.Point, ((byte)(0)));
            this.label1.ForeColor = System.Drawing.Color.Red;
            this.label1.Location = new System.Drawing.Point(34, 370);
            this.label1.Name = "label1";
            this.label1.Size = new System.Drawing.Size(501, 51);
            this.label1.TabIndex = 3;
            this.label1.Text = "Select option that best represents the final customer configuration";
            // 
            // selectType
            // 
            this.AutoScaleDimensions = new System.Drawing.SizeF(8F, 16F);
            this.AutoScaleMode = System.Windows.Forms.AutoScaleMode.Font;
            this.ClientSize = new System.Drawing.Size(567, 447);
            this.Controls.Add(this.label1);
            this.Controls.Add(this.btnPCVHS);
            this.Controls.Add(this.btnCCVHS);
            this.Controls.Add(this.btnFHS);
            this.FormBorderStyle = System.Windows.Forms.FormBorderStyle.FixedDialog;
            this.Icon = ((System.Drawing.Icon)(resources.GetObject("$this.Icon")));
            this.Location = new System.Drawing.Point(100, 100);
            this.MaximizeBox = false;
            this.MinimizeBox = false;
            this.Name = "selectType";
            this.ShowInTaskbar = false;
            this.StartPosition = System.Windows.Forms.FormStartPosition.Manual;
            this.Text = "System Type";
            this.Load += new System.EventHandler(this.selectType_Load);
            this.ResumeLayout(false);

        }

        #endregion

        private System.Windows.Forms.Button btnFHS;
        private System.Windows.Forms.Button btnCCVHS;
        private System.Windows.Forms.Button btnPCVHS;
        private System.Windows.Forms.Label label1;
    }
}