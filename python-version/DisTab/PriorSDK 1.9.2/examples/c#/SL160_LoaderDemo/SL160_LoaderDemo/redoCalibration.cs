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
    public partial class redoCalibration : Form
    {
        SL160 _sl160;

        public redoCalibration(SL160 sl160)
        {
            InitializeComponent();
            _sl160 = sl160;
        }

        private void redoCalibration_Load(object sender, EventArgs e)
        {

        }

        private void btnRedoAll_Click(object sender, EventArgs e)
        {
            if (MessageBox.Show("Are you sure you want to clear ALL calibration?", "Query",
                                       MessageBoxButtons.YesNo, MessageBoxIcon.Question) == System.Windows.Forms.DialogResult.Yes)
            {
                _sl160.ClearAllCalibrationFlags();
                _sl160.SaveCalibrationFlagsToController();
                DialogResult = System.Windows.Forms.DialogResult.OK;
            }

        }

        private void btnRedoHotel_Click(object sender, EventArgs e)
        {
            if (MessageBox.Show("Are you sure you want to clear hotel calibration?", "Query",
                                        MessageBoxButtons.YesNo, MessageBoxIcon.Question) == System.Windows.Forms.DialogResult.Yes)
            {
                _sl160.ClearHotelCalibrationFlag();
                _sl160.SaveCalibrationFlagsToController();
                DialogResult = System.Windows.Forms.DialogResult.OK;
            }
        }

        private void btnRedoStage_Click(object sender, EventArgs e)
        {
            if (MessageBox.Show("Are you sure you want to clear stage calibration?", "Query",
                                       MessageBoxButtons.YesNo, MessageBoxIcon.Question) == System.Windows.Forms.DialogResult.Yes)
            {
                _sl160.ClearStageCalibrationFlag();
                _sl160.SaveCalibrationFlagsToController();
                DialogResult = System.Windows.Forms.DialogResult.OK;
            }
        }

        private void btnCancel_Click(object sender, EventArgs e)
        {
            DialogResult = System.Windows.Forms.DialogResult.Cancel;
        }

    }
}
