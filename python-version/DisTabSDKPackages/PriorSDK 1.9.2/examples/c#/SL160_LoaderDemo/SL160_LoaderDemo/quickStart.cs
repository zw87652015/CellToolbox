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
    public partial class quickStart : Form
    {
        SL160 _data;

        public quickStart(SL160 data)
        {
            InitializeComponent();
            _data = data;
        }

        private void quickStart_Load(object sender, EventArgs e)
        {

        }
    }
}
