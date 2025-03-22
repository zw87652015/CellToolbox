namespace SL160_LoaderDemo
{
    partial class ManualMove
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
            System.ComponentModel.ComponentResourceManager resources = new System.ComponentModel.ComponentResourceManager(typeof(ManualMove));
            this.label1 = new System.Windows.Forms.Label();
            this.groupBox1 = new System.Windows.Forms.GroupBox();
            this.grpSTM = new System.Windows.Forms.GroupBox();
            this.label3 = new System.Windows.Forms.Label();
            this.txtSTM = new System.Windows.Forms.TextBox();
            this.btnSTMRETRACT = new System.Windows.Forms.Button();
            this.btnSTMEXTEND = new System.Windows.Forms.Button();
            this.grpHLM = new System.Windows.Forms.GroupBox();
            this.label2 = new System.Windows.Forms.Label();
            this.txtHLM = new System.Windows.Forms.TextBox();
            this.btnHLMUP = new System.Windows.Forms.Button();
            this.btnHLMDOWN = new System.Windows.Forms.Button();
            this.grpHSM = new System.Windows.Forms.GroupBox();
            this.label5 = new System.Windows.Forms.Label();
            this.txtHSM = new System.Windows.Forms.TextBox();
            this.btnHSMIN = new System.Windows.Forms.Button();
            this.btnHSMOUT = new System.Windows.Forms.Button();
            this.groupBox2 = new System.Windows.Forms.GroupBox();
            this.grpZ = new System.Windows.Forms.GroupBox();
            this.label6 = new System.Windows.Forms.Label();
            this.txtZ = new System.Windows.Forms.TextBox();
            this.btnZUp = new System.Windows.Forms.Button();
            this.btnZDown = new System.Windows.Forms.Button();
            this.grpXY = new System.Windows.Forms.GroupBox();
            this.label4 = new System.Windows.Forms.Label();
            this.txtStage = new System.Windows.Forms.TextBox();
            this.btnRight = new System.Windows.Forms.Button();
            this.btnLeft = new System.Windows.Forms.Button();
            this.btnForward = new System.Windows.Forms.Button();
            this.btnBack = new System.Windows.Forms.Button();
            this.toolTip1 = new System.Windows.Forms.ToolTip(this.components);
            this.groupBox1.SuspendLayout();
            this.grpSTM.SuspendLayout();
            this.grpHLM.SuspendLayout();
            this.grpHSM.SuspendLayout();
            this.groupBox2.SuspendLayout();
            this.grpZ.SuspendLayout();
            this.grpXY.SuspendLayout();
            this.SuspendLayout();
            // 
            // label1
            // 
            this.label1.BorderStyle = System.Windows.Forms.BorderStyle.FixedSingle;
            this.label1.Font = new System.Drawing.Font("Microsoft Sans Serif", 12F, System.Drawing.FontStyle.Regular, System.Drawing.GraphicsUnit.Point, ((byte)(0)));
            this.label1.ForeColor = System.Drawing.Color.Red;
            this.label1.Location = new System.Drawing.Point(46, 30);
            this.label1.Name = "label1";
            this.label1.Size = new System.Drawing.Size(766, 155);
            this.label1.TabIndex = 1;
            this.label1.Text = resources.GetString("label1.Text");
            // 
            // groupBox1
            // 
            this.groupBox1.Controls.Add(this.grpSTM);
            this.groupBox1.Controls.Add(this.grpHLM);
            this.groupBox1.Controls.Add(this.grpHSM);
            this.groupBox1.Location = new System.Drawing.Point(46, 225);
            this.groupBox1.Name = "groupBox1";
            this.groupBox1.Size = new System.Drawing.Size(386, 437);
            this.groupBox1.TabIndex = 2;
            this.groupBox1.TabStop = false;
            this.groupBox1.Text = "SL160 Loader Axes";
            // 
            // grpSTM
            // 
            this.grpSTM.Controls.Add(this.label3);
            this.grpSTM.Controls.Add(this.txtSTM);
            this.grpSTM.Controls.Add(this.btnSTMRETRACT);
            this.grpSTM.Controls.Add(this.btnSTMEXTEND);
            this.grpSTM.Location = new System.Drawing.Point(23, 287);
            this.grpSTM.Name = "grpSTM";
            this.grpSTM.Size = new System.Drawing.Size(334, 101);
            this.grpSTM.TabIndex = 8;
            this.grpSTM.TabStop = false;
            this.grpSTM.Text = "STM";
            // 
            // label3
            // 
            this.label3.AutoSize = true;
            this.label3.Location = new System.Drawing.Point(236, 26);
            this.label3.Name = "label3";
            this.label3.Size = new System.Drawing.Size(92, 17);
            this.label3.TabIndex = 7;
            this.label3.Text = "Speed(mm/s)";
            // 
            // txtSTM
            // 
            this.txtSTM.Location = new System.Drawing.Point(252, 52);
            this.txtSTM.Name = "txtSTM";
            this.txtSTM.Size = new System.Drawing.Size(53, 22);
            this.txtSTM.TabIndex = 6;
            this.txtSTM.Text = "1";
            this.toolTip1.SetToolTip(this.txtSTM, "STM speed mm/s");
            this.txtSTM.Validating += new System.ComponentModel.CancelEventHandler(this.posInt_Validating);
            // 
            // btnSTMRETRACT
            // 
            this.btnSTMRETRACT.Location = new System.Drawing.Point(17, 41);
            this.btnSTMRETRACT.Name = "btnSTMRETRACT";
            this.btnSTMRETRACT.Size = new System.Drawing.Size(90, 40);
            this.btnSTMRETRACT.TabIndex = 4;
            this.btnSTMRETRACT.Text = "Retract";
            this.toolTip1.SetToolTip(this.btnSTMRETRACT, "hold down to move STM in or out of stage");
            this.btnSTMRETRACT.UseVisualStyleBackColor = true;
            this.btnSTMRETRACT.MouseDown += new System.Windows.Forms.MouseEventHandler(this.btnSTMRETRACT_MouseDown);
            this.btnSTMRETRACT.MouseUp += new System.Windows.Forms.MouseEventHandler(this.btnSTMRETRACT_MouseUp);
            // 
            // btnSTMEXTEND
            // 
            this.btnSTMEXTEND.Location = new System.Drawing.Point(120, 41);
            this.btnSTMEXTEND.Name = "btnSTMEXTEND";
            this.btnSTMEXTEND.Size = new System.Drawing.Size(90, 40);
            this.btnSTMEXTEND.TabIndex = 5;
            this.btnSTMEXTEND.Text = "Extend";
            this.toolTip1.SetToolTip(this.btnSTMEXTEND, "hold down to move STM in or out of stage");
            this.btnSTMEXTEND.UseVisualStyleBackColor = true;
            this.btnSTMEXTEND.MouseDown += new System.Windows.Forms.MouseEventHandler(this.btnSTMEXTEND_MouseDown);
            this.btnSTMEXTEND.MouseUp += new System.Windows.Forms.MouseEventHandler(this.btnSTMEXTEND_MouseUp);
            // 
            // grpHLM
            // 
            this.grpHLM.Controls.Add(this.label2);
            this.grpHLM.Controls.Add(this.txtHLM);
            this.grpHLM.Controls.Add(this.btnHLMUP);
            this.grpHLM.Controls.Add(this.btnHLMDOWN);
            this.grpHLM.Location = new System.Drawing.Point(23, 163);
            this.grpHLM.Name = "grpHLM";
            this.grpHLM.Size = new System.Drawing.Size(334, 101);
            this.grpHLM.TabIndex = 7;
            this.grpHLM.TabStop = false;
            this.grpHLM.Text = "HLM";
            // 
            // label2
            // 
            this.label2.AutoSize = true;
            this.label2.Location = new System.Drawing.Point(236, 26);
            this.label2.Name = "label2";
            this.label2.Size = new System.Drawing.Size(92, 17);
            this.label2.TabIndex = 7;
            this.label2.Text = "Speed(mm/s)";
            // 
            // txtHLM
            // 
            this.txtHLM.Location = new System.Drawing.Point(252, 52);
            this.txtHLM.Name = "txtHLM";
            this.txtHLM.Size = new System.Drawing.Size(53, 22);
            this.txtHLM.TabIndex = 6;
            this.txtHLM.Text = "1";
            this.toolTip1.SetToolTip(this.txtHLM, "HLM speed mm/s");
            this.txtHLM.Validating += new System.ComponentModel.CancelEventHandler(this.posInt_Validating);
            // 
            // btnHLMUP
            // 
            this.btnHLMUP.Location = new System.Drawing.Point(17, 41);
            this.btnHLMUP.Name = "btnHLMUP";
            this.btnHLMUP.Size = new System.Drawing.Size(90, 40);
            this.btnHLMUP.TabIndex = 4;
            this.btnHLMUP.Text = "Up";
            this.toolTip1.SetToolTip(this.btnHLMUP, "hold down to lift HLM up or down");
            this.btnHLMUP.UseVisualStyleBackColor = true;
            this.btnHLMUP.MouseDown += new System.Windows.Forms.MouseEventHandler(this.btnHLMUP_MouseDown);
            this.btnHLMUP.MouseUp += new System.Windows.Forms.MouseEventHandler(this.btnHLMUP_MouseUp);
            // 
            // btnHLMDOWN
            // 
            this.btnHLMDOWN.Location = new System.Drawing.Point(120, 41);
            this.btnHLMDOWN.Name = "btnHLMDOWN";
            this.btnHLMDOWN.Size = new System.Drawing.Size(90, 40);
            this.btnHLMDOWN.TabIndex = 5;
            this.btnHLMDOWN.Text = "Down";
            this.toolTip1.SetToolTip(this.btnHLMDOWN, "hold down to lift HLM up or down");
            this.btnHLMDOWN.UseVisualStyleBackColor = true;
            this.btnHLMDOWN.MouseDown += new System.Windows.Forms.MouseEventHandler(this.btnHLMDOWN_MouseDown);
            this.btnHLMDOWN.MouseUp += new System.Windows.Forms.MouseEventHandler(this.btnHLMDOWN_MouseUp);
            // 
            // grpHSM
            // 
            this.grpHSM.Controls.Add(this.label5);
            this.grpHSM.Controls.Add(this.txtHSM);
            this.grpHSM.Controls.Add(this.btnHSMIN);
            this.grpHSM.Controls.Add(this.btnHSMOUT);
            this.grpHSM.Location = new System.Drawing.Point(23, 47);
            this.grpHSM.Name = "grpHSM";
            this.grpHSM.Size = new System.Drawing.Size(334, 101);
            this.grpHSM.TabIndex = 6;
            this.grpHSM.TabStop = false;
            this.grpHSM.Text = "HSM";
            // 
            // label5
            // 
            this.label5.AutoSize = true;
            this.label5.Location = new System.Drawing.Point(236, 26);
            this.label5.Name = "label5";
            this.label5.Size = new System.Drawing.Size(92, 17);
            this.label5.TabIndex = 7;
            this.label5.Text = "Speed(mm/s)";
            // 
            // txtHSM
            // 
            this.txtHSM.Location = new System.Drawing.Point(252, 52);
            this.txtHSM.Name = "txtHSM";
            this.txtHSM.Size = new System.Drawing.Size(53, 22);
            this.txtHSM.TabIndex = 6;
            this.txtHSM.Text = "1";
            this.toolTip1.SetToolTip(this.txtHSM, "HSM speed mm/s");
            this.txtHSM.Validating += new System.ComponentModel.CancelEventHandler(this.posInt_Validating);
            // 
            // btnHSMIN
            // 
            this.btnHSMIN.Location = new System.Drawing.Point(17, 41);
            this.btnHSMIN.Name = "btnHSMIN";
            this.btnHSMIN.Size = new System.Drawing.Size(90, 40);
            this.btnHSMIN.TabIndex = 4;
            this.btnHSMIN.Text = "Insert";
            this.toolTip1.SetToolTip(this.btnHSMIN, "hold down to move HSM in or out of loader");
            this.btnHSMIN.UseVisualStyleBackColor = true;
            this.btnHSMIN.MouseDown += new System.Windows.Forms.MouseEventHandler(this.btnHSMIN_MouseDown);
            this.btnHSMIN.MouseUp += new System.Windows.Forms.MouseEventHandler(this.btnHSMIN_MouseUp);
            // 
            // btnHSMOUT
            // 
            this.btnHSMOUT.Location = new System.Drawing.Point(120, 41);
            this.btnHSMOUT.Name = "btnHSMOUT";
            this.btnHSMOUT.Size = new System.Drawing.Size(90, 40);
            this.btnHSMOUT.TabIndex = 5;
            this.btnHSMOUT.Text = "Eject";
            this.toolTip1.SetToolTip(this.btnHSMOUT, "hold down to move HSM in or out of loader");
            this.btnHSMOUT.UseVisualStyleBackColor = true;
            this.btnHSMOUT.MouseDown += new System.Windows.Forms.MouseEventHandler(this.btnHSMOUT_MouseDown);
            this.btnHSMOUT.MouseUp += new System.Windows.Forms.MouseEventHandler(this.btnHSMOUT_MouseUp);
            // 
            // groupBox2
            // 
            this.groupBox2.Controls.Add(this.grpZ);
            this.groupBox2.Controls.Add(this.grpXY);
            this.groupBox2.Location = new System.Drawing.Point(450, 225);
            this.groupBox2.Name = "groupBox2";
            this.groupBox2.Size = new System.Drawing.Size(362, 437);
            this.groupBox2.TabIndex = 3;
            this.groupBox2.TabStop = false;
            this.groupBox2.Text = "Stage Axes";
            // 
            // grpZ
            // 
            this.grpZ.Controls.Add(this.label6);
            this.grpZ.Controls.Add(this.txtZ);
            this.grpZ.Controls.Add(this.btnZUp);
            this.grpZ.Controls.Add(this.btnZDown);
            this.grpZ.Location = new System.Drawing.Point(18, 268);
            this.grpZ.Name = "grpZ";
            this.grpZ.Size = new System.Drawing.Size(326, 152);
            this.grpZ.TabIndex = 12;
            this.grpZ.TabStop = false;
            this.grpZ.Text = "Stage Z";
            // 
            // label6
            // 
            this.label6.AutoSize = true;
            this.label6.Location = new System.Drawing.Point(219, 52);
            this.label6.Name = "label6";
            this.label6.Size = new System.Drawing.Size(78, 17);
            this.label6.TabIndex = 12;
            this.label6.Text = "Speed(u/s)";
            // 
            // txtZ
            // 
            this.txtZ.Location = new System.Drawing.Point(235, 78);
            this.txtZ.Name = "txtZ";
            this.txtZ.Size = new System.Drawing.Size(53, 22);
            this.txtZ.TabIndex = 11;
            this.txtZ.Text = "10";
            this.toolTip1.SetToolTip(this.txtZ, "focus speed microns/s");
            this.txtZ.Validating += new System.ComponentModel.CancelEventHandler(this.posInt_Validating);
            // 
            // btnZUp
            // 
            this.btnZUp.Location = new System.Drawing.Point(65, 33);
            this.btnZUp.Name = "btnZUp";
            this.btnZUp.Size = new System.Drawing.Size(90, 40);
            this.btnZUp.TabIndex = 9;
            this.btnZUp.Text = "Up";
            this.toolTip1.SetToolTip(this.btnZUp, "hold down to move focus");
            this.btnZUp.UseVisualStyleBackColor = true;
            this.btnZUp.MouseDown += new System.Windows.Forms.MouseEventHandler(this.btnZUp_MouseDown);
            this.btnZUp.MouseUp += new System.Windows.Forms.MouseEventHandler(this.btnZUp_MouseUp);
            // 
            // btnZDown
            // 
            this.btnZDown.Location = new System.Drawing.Point(65, 93);
            this.btnZDown.Name = "btnZDown";
            this.btnZDown.Size = new System.Drawing.Size(90, 40);
            this.btnZDown.TabIndex = 10;
            this.btnZDown.Text = "Down";
            this.toolTip1.SetToolTip(this.btnZDown, "hold down to move focus");
            this.btnZDown.UseVisualStyleBackColor = true;
            this.btnZDown.MouseDown += new System.Windows.Forms.MouseEventHandler(this.btnZDown_MouseDown);
            this.btnZDown.MouseUp += new System.Windows.Forms.MouseEventHandler(this.btnZDown_MouseUp);
            // 
            // grpXY
            // 
            this.grpXY.Controls.Add(this.label4);
            this.grpXY.Controls.Add(this.txtStage);
            this.grpXY.Controls.Add(this.btnRight);
            this.grpXY.Controls.Add(this.btnLeft);
            this.grpXY.Controls.Add(this.btnForward);
            this.grpXY.Controls.Add(this.btnBack);
            this.grpXY.Location = new System.Drawing.Point(18, 48);
            this.grpXY.Name = "grpXY";
            this.grpXY.Size = new System.Drawing.Size(326, 196);
            this.grpXY.TabIndex = 11;
            this.grpXY.TabStop = false;
            this.grpXY.Text = "Stage XY";
            // 
            // label4
            // 
            this.label4.AutoSize = true;
            this.label4.Location = new System.Drawing.Point(219, 68);
            this.label4.Name = "label4";
            this.label4.Size = new System.Drawing.Size(78, 17);
            this.label4.TabIndex = 10;
            this.label4.Text = "Speed(u/s)";
            // 
            // txtStage
            // 
            this.txtStage.Location = new System.Drawing.Point(235, 94);
            this.txtStage.Name = "txtStage";
            this.txtStage.Size = new System.Drawing.Size(53, 22);
            this.txtStage.TabIndex = 9;
            this.txtStage.Text = "1000";
            this.toolTip1.SetToolTip(this.txtStage, "stage speed microns/s");
            this.txtStage.Validating += new System.ComponentModel.CancelEventHandler(this.posInt_Validating);
            // 
            // btnRight
            // 
            this.btnRight.Location = new System.Drawing.Point(110, 76);
            this.btnRight.Name = "btnRight";
            this.btnRight.Size = new System.Drawing.Size(90, 40);
            this.btnRight.TabIndex = 8;
            this.btnRight.Text = "Right";
            this.toolTip1.SetToolTip(this.btnRight, "hold down to move stage");
            this.btnRight.UseVisualStyleBackColor = true;
            this.btnRight.MouseDown += new System.Windows.Forms.MouseEventHandler(this.btnRight_MouseDown);
            this.btnRight.MouseUp += new System.Windows.Forms.MouseEventHandler(this.btnRight_MouseUp);
            // 
            // btnLeft
            // 
            this.btnLeft.Location = new System.Drawing.Point(15, 76);
            this.btnLeft.Name = "btnLeft";
            this.btnLeft.Size = new System.Drawing.Size(90, 40);
            this.btnLeft.TabIndex = 5;
            this.btnLeft.Text = "Left";
            this.toolTip1.SetToolTip(this.btnLeft, "hold down to move stage");
            this.btnLeft.UseVisualStyleBackColor = true;
            this.btnLeft.MouseDown += new System.Windows.Forms.MouseEventHandler(this.btnLeft_MouseDown);
            this.btnLeft.MouseUp += new System.Windows.Forms.MouseEventHandler(this.btnLeft_MouseUp);
            // 
            // btnForward
            // 
            this.btnForward.Location = new System.Drawing.Point(65, 129);
            this.btnForward.Name = "btnForward";
            this.btnForward.Size = new System.Drawing.Size(90, 40);
            this.btnForward.TabIndex = 6;
            this.btnForward.Text = "Forward";
            this.toolTip1.SetToolTip(this.btnForward, "hold down to move stage");
            this.btnForward.UseVisualStyleBackColor = true;
            this.btnForward.MouseDown += new System.Windows.Forms.MouseEventHandler(this.btnForward_MouseDown);
            this.btnForward.MouseUp += new System.Windows.Forms.MouseEventHandler(this.btnForward_MouseUp);
            // 
            // btnBack
            // 
            this.btnBack.Location = new System.Drawing.Point(65, 25);
            this.btnBack.Name = "btnBack";
            this.btnBack.Size = new System.Drawing.Size(90, 40);
            this.btnBack.TabIndex = 7;
            this.btnBack.Text = "Back";
            this.toolTip1.SetToolTip(this.btnBack, "hold down to move stage");
            this.btnBack.UseVisualStyleBackColor = true;
            this.btnBack.MouseDown += new System.Windows.Forms.MouseEventHandler(this.btnBack_MouseDown);
            this.btnBack.MouseUp += new System.Windows.Forms.MouseEventHandler(this.btnBack_MouseUp);
            // 
            // ManualMove
            // 
            this.AutoScaleDimensions = new System.Drawing.SizeF(8F, 16F);
            this.AutoScaleMode = System.Windows.Forms.AutoScaleMode.Font;
            this.ClientSize = new System.Drawing.Size(830, 679);
            this.Controls.Add(this.groupBox2);
            this.Controls.Add(this.groupBox1);
            this.Controls.Add(this.label1);
            this.FormBorderStyle = System.Windows.Forms.FormBorderStyle.FixedDialog;
            this.Icon = ((System.Drawing.Icon)(resources.GetObject("$this.Icon")));
            this.MaximizeBox = false;
            this.MinimizeBox = false;
            this.Name = "ManualMove";
            this.ShowInTaskbar = false;
            this.StartPosition = System.Windows.Forms.FormStartPosition.CenterScreen;
            this.Text = "ManualMove";
            this.Load += new System.EventHandler(this.ManualMove_Load);
            this.groupBox1.ResumeLayout(false);
            this.grpSTM.ResumeLayout(false);
            this.grpSTM.PerformLayout();
            this.grpHLM.ResumeLayout(false);
            this.grpHLM.PerformLayout();
            this.grpHSM.ResumeLayout(false);
            this.grpHSM.PerformLayout();
            this.groupBox2.ResumeLayout(false);
            this.grpZ.ResumeLayout(false);
            this.grpZ.PerformLayout();
            this.grpXY.ResumeLayout(false);
            this.grpXY.PerformLayout();
            this.ResumeLayout(false);

        }

        #endregion

        private System.Windows.Forms.Label label1;
        private System.Windows.Forms.GroupBox groupBox1;
        private System.Windows.Forms.GroupBox groupBox2;
        private System.Windows.Forms.GroupBox grpHSM;
        private System.Windows.Forms.Button btnHSMOUT;
        private System.Windows.Forms.Button btnHSMIN;
        private System.Windows.Forms.GroupBox grpSTM;
        private System.Windows.Forms.Label label3;
        private System.Windows.Forms.TextBox txtSTM;
        private System.Windows.Forms.Button btnSTMRETRACT;
        private System.Windows.Forms.Button btnSTMEXTEND;
        private System.Windows.Forms.GroupBox grpHLM;
        private System.Windows.Forms.Label label2;
        private System.Windows.Forms.TextBox txtHLM;
        private System.Windows.Forms.Button btnHLMUP;
        private System.Windows.Forms.Button btnHLMDOWN;
        private System.Windows.Forms.Label label5;
        private System.Windows.Forms.TextBox txtHSM;
        private System.Windows.Forms.ToolTip toolTip1;
        private System.Windows.Forms.GroupBox grpZ;
        private System.Windows.Forms.Label label6;
        private System.Windows.Forms.TextBox txtZ;
        private System.Windows.Forms.Button btnZUp;
        private System.Windows.Forms.Button btnZDown;
        private System.Windows.Forms.GroupBox grpXY;
        private System.Windows.Forms.Label label4;
        private System.Windows.Forms.TextBox txtStage;
        private System.Windows.Forms.Button btnRight;
        private System.Windows.Forms.Button btnLeft;
        private System.Windows.Forms.Button btnForward;
        private System.Windows.Forms.Button btnBack;

    }
}