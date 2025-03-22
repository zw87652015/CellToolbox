namespace SL160_LoaderDemo
{
    partial class Joystick
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
            System.ComponentModel.ComponentResourceManager resources = new System.ComponentModel.ComponentResourceManager(typeof(Joystick));
            this.chkX = new System.Windows.Forms.CheckBox();
            this.chkY = new System.Windows.Forms.CheckBox();
            this.grpJoyState = new System.Windows.Forms.GroupBox();
            this.rbZ = new System.Windows.Forms.RadioButton();
            this.rbXY = new System.Windows.Forms.RadioButton();
            this.rbOff = new System.Windows.Forms.RadioButton();
            this.rbXYZ = new System.Windows.Forms.RadioButton();
            this.grpJoyState.SuspendLayout();
            this.SuspendLayout();
            // 
            // chkX
            // 
            this.chkX.AutoSize = true;
            this.chkX.Font = new System.Drawing.Font("Microsoft Sans Serif", 12F, System.Drawing.FontStyle.Regular, System.Drawing.GraphicsUnit.Point, ((byte)(0)));
            this.chkX.Location = new System.Drawing.Point(23, 255);
            this.chkX.Name = "chkX";
            this.chkX.Size = new System.Drawing.Size(101, 29);
            this.chkX.TabIndex = 0;
            this.chkX.Text = "Invert X";
            this.chkX.UseVisualStyleBackColor = true;
            this.chkX.CheckedChanged += new System.EventHandler(this.chkX_CheckedChanged);
            // 
            // chkY
            // 
            this.chkY.AutoSize = true;
            this.chkY.Font = new System.Drawing.Font("Microsoft Sans Serif", 12F, System.Drawing.FontStyle.Regular, System.Drawing.GraphicsUnit.Point, ((byte)(0)));
            this.chkY.Location = new System.Drawing.Point(23, 309);
            this.chkY.Name = "chkY";
            this.chkY.Size = new System.Drawing.Size(100, 29);
            this.chkY.TabIndex = 1;
            this.chkY.Text = "Invert Y";
            this.chkY.UseVisualStyleBackColor = true;
            this.chkY.CheckedChanged += new System.EventHandler(this.chkY_CheckedChanged);
            // 
            // grpJoyState
            // 
            this.grpJoyState.Controls.Add(this.rbZ);
            this.grpJoyState.Controls.Add(this.rbXY);
            this.grpJoyState.Controls.Add(this.rbOff);
            this.grpJoyState.Controls.Add(this.rbXYZ);
            this.grpJoyState.Location = new System.Drawing.Point(23, 28);
            this.grpJoyState.Name = "grpJoyState";
            this.grpJoyState.Size = new System.Drawing.Size(155, 206);
            this.grpJoyState.TabIndex = 2;
            this.grpJoyState.TabStop = false;
            this.grpJoyState.Text = "JoyStickState";
            // 
            // rbZ
            // 
            this.rbZ.AutoSize = true;
            this.rbZ.Location = new System.Drawing.Point(20, 123);
            this.rbZ.Name = "rbZ";
            this.rbZ.Size = new System.Drawing.Size(94, 21);
            this.rbZ.TabIndex = 3;
            this.rbZ.TabStop = true;
            this.rbZ.Text = "Z Enabled";
            this.rbZ.UseVisualStyleBackColor = true;
            this.rbZ.CheckedChanged += new System.EventHandler(this.rbZ_CheckedChanged);
            // 
            // rbXY
            // 
            this.rbXY.AutoSize = true;
            this.rbXY.Location = new System.Drawing.Point(20, 161);
            this.rbXY.Name = "rbXY";
            this.rbXY.Size = new System.Drawing.Size(103, 21);
            this.rbXY.TabIndex = 2;
            this.rbXY.TabStop = true;
            this.rbXY.Text = "XY Enabled";
            this.rbXY.UseVisualStyleBackColor = true;
            this.rbXY.CheckedChanged += new System.EventHandler(this.rbXY_CheckedChanged);
            // 
            // rbOff
            // 
            this.rbOff.AutoSize = true;
            this.rbOff.Location = new System.Drawing.Point(20, 84);
            this.rbOff.Name = "rbOff";
            this.rbOff.Size = new System.Drawing.Size(115, 21);
            this.rbOff.TabIndex = 1;
            this.rbOff.TabStop = true;
            this.rbOff.Text = "XYZ Disabled";
            this.rbOff.UseVisualStyleBackColor = true;
            this.rbOff.CheckedChanged += new System.EventHandler(this.rbOff_CheckedChanged);
            // 
            // rbXYZ
            // 
            this.rbXYZ.AutoSize = true;
            this.rbXYZ.Location = new System.Drawing.Point(20, 44);
            this.rbXYZ.Name = "rbXYZ";
            this.rbXYZ.Size = new System.Drawing.Size(112, 21);
            this.rbXYZ.TabIndex = 0;
            this.rbXYZ.TabStop = true;
            this.rbXYZ.Text = "XYZ Enabled";
            this.rbXYZ.UseVisualStyleBackColor = true;
            this.rbXYZ.CheckedChanged += new System.EventHandler(this.rbXYZ_CheckedChanged);
            // 
            // Joystick
            // 
            this.AutoScaleDimensions = new System.Drawing.SizeF(8F, 16F);
            this.AutoScaleMode = System.Windows.Forms.AutoScaleMode.Font;
            this.ClientSize = new System.Drawing.Size(202, 352);
            this.Controls.Add(this.grpJoyState);
            this.Controls.Add(this.chkY);
            this.Controls.Add(this.chkX);
            this.FormBorderStyle = System.Windows.Forms.FormBorderStyle.FixedDialog;
            this.Icon = ((System.Drawing.Icon)(resources.GetObject("$this.Icon")));
            this.MaximizeBox = false;
            this.MinimizeBox = false;
            this.Name = "Joystick";
            this.ShowInTaskbar = false;
            this.StartPosition = System.Windows.Forms.FormStartPosition.CenterParent;
            this.Text = "Joystick Direction";
            this.Load += new System.EventHandler(this.Joystick_Load);
            this.grpJoyState.ResumeLayout(false);
            this.grpJoyState.PerformLayout();
            this.ResumeLayout(false);
            this.PerformLayout();

        }

        #endregion

        private System.Windows.Forms.CheckBox chkX;
        private System.Windows.Forms.CheckBox chkY;
        private System.Windows.Forms.GroupBox grpJoyState;
        private System.Windows.Forms.RadioButton rbZ;
        private System.Windows.Forms.RadioButton rbXY;
        private System.Windows.Forms.RadioButton rbOff;
        private System.Windows.Forms.RadioButton rbXYZ;
    }
}