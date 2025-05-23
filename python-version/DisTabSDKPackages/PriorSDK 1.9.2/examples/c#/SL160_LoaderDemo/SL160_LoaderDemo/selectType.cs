using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Data;
using System.Drawing;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using System.Windows.Forms;

namespace SL160_LoaderDemo
{
    public partial class selectType : Form
    {
        SL160 _sl160;

        public selectType(SL160 sl160)
        {
            InitializeComponent();
            _sl160 = sl160;
        }

        private void selectType_Load(object sender, EventArgs e)
        {
         
        }

        private void btnFHS_Click(object sender, EventArgs e)
        {
            if (MessageBox.Show("Confirm Fixed Height Stage","Confirm", MessageBoxButtons.YesNo, MessageBoxIcon.Question) == System.Windows.Forms.DialogResult.Yes)
            {
                if (_sl160.SetCalibrationTypeFixed())
                    DialogResult = System.Windows.Forms.DialogResult.OK;
                else
                    DialogResult = System.Windows.Forms.DialogResult.Cancel;
            }
        }

        private void btnCCVHS_Click(object sender, EventArgs e)
        {
            if (MessageBox.Show("Confirm Customer Controlled Height Stage", "Confirm", MessageBoxButtons.YesNo, MessageBoxIcon.Question) == System.Windows.Forms.DialogResult.Yes)
            {
                if (_sl160.SetCalibrationTypeUser())
                    DialogResult = System.Windows.Forms.DialogResult.OK;
                else
                    DialogResult = System.Windows.Forms.DialogResult.Cancel;
            }
        }

        private void btnPCVHS_Click(object sender, EventArgs e)
        {
            if (MessageBox.Show("Confirm Prior Height Controlled Stage", "Confirm", MessageBoxButtons.YesNo, MessageBoxIcon.Question) == System.Windows.Forms.DialogResult.Yes)
            {
                if (_sl160.SetCalibrationTypePrior())
                    DialogResult = System.Windows.Forms.DialogResult.OK;
                else
                    DialogResult = System.Windows.Forms.DialogResult.Cancel;
            }
        }
    }
}
