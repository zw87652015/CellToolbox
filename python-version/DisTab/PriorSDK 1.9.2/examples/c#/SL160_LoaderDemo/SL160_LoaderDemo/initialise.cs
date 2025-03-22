using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Data;
using System.Drawing;
using System.Linq;
using System.Text;
using System.Threading;
using System.Windows.Forms;
using System.Reflection;

namespace SL160_LoaderDemo
{
    public partial class initialise : Form
    {
        SL160 _sl160;

        enum InitState
        {
            InitStart,
            InitLoader,
            InitStage,
            End,
        };

        InitState state = InitState.InitStart;


        public initialise(SL160 sl160)
        {
            InitializeComponent();
            _sl160 = sl160;

            state = InitState.InitStart;
        }

        private void initialise_Load(object sender, EventArgs e)
        {
            DoState();
        }

        private void DoState()
        {
            int err;

            switch (state)
            {
                case InitState.InitStart:
                {
                    btnNext.Enabled = true;

                    this.Text = "Initialise System - " + state.ToString(); 
                    lbInfo.Items.Add("Press 'Next' to start the SL160 initialisation");

                    break;
                }

                case InitState.InitLoader:
                {

                    btnNext.Enabled = false;
                    this.Text = "Initialise System - " + state.ToString(); 
                    lbInfo.Items.Add("Initialising Loader...");
                    this.Refresh();

                    if ((err = _sl160.InitLoader()) != Prior.PRIOR_OK)
                    {
                        MessageBox.Show("Error (" + err.ToString() + ") occured, please contact Prior");
                        DialogResult = DialogResult.Cancel;
                    } 
                    else
                        lbInfo.Items.Add("Done.");

                    state++;
                    goto case InitState.InitStage;   
                }

                case InitState.InitStage:
                {
                    this.Text = "Initialise System - " + state.ToString(); 
                    lbInfo.Items.Add("Initialising Stage...");
                    this.Refresh();

                    if ((err = _sl160.InitStage()) != Prior.PRIOR_OK)
                    {
                        MessageBox.Show("Error (" + err.ToString() + ") occured, please contact Prior");
                        DialogResult = DialogResult.Cancel;
                    }
                    else
                    {
                        btnNext.Enabled = true;
                        lbInfo.Items.Add("Done.");
                        lbInfo.Items.Add("Press 'Next' to end initialisation.");
                    }

                    break;
                }

                case InitState.End:
                {
                    DialogResult = DialogResult.OK;
                    break;
                }
            }
        }

        private void btQuit_Click(object sender, EventArgs e)
        {
            DialogResult = DialogResult.Cancel;
        }

        private void btnNext_Click(object sender, EventArgs e)
        {
            state++;
            DoState();
        }
    }
}
