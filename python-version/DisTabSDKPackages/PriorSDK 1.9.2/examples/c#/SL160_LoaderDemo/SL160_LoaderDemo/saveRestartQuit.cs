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
    public partial class saveRestartQuit : Form
    {
        SL160 _data;

        public saveRestartQuit(SL160 data)
        {
            InitializeComponent();
            _data = data;
        }
       

        private void saveRestartQuit_Load(object sender, EventArgs e)
        {

        }
    }
}
