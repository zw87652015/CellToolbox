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
    public partial class help : Form
    {
        StringBuilder _version;

        public help(StringBuilder ver)
        {
            InitializeComponent();

            _version = ver;
        }

        private void btnClose_Click(object sender, EventArgs e)
        {
            this.Close();
        }

        private void help_Load(object sender, EventArgs e)
        {
            listBox1.Items.Add(Application.ProductName + " " + Application.ProductVersion);
            listBox1.Items.Add("PriorScientificSDK " + _version.ToString());
            listBox1.Items.Add("");
            listBox1.Items.Add("SL160 Loader Calibration and soak test application");
            listBox1.Items.Add("");
            listBox1.Items.Add("Connect to PS3 and SL160 Loader using 'Connect' menu entry");
            listBox1.Items.Add("");
            listBox1.Items.Add("Follow instructions to Initialise the robot.");
            listBox1.Items.Add("");
            listBox1.Items.Add("Follow instructions to perform calibration during production.");
            listBox1.Items.Add("Calibration data for loader is stored in stage eeprom and used to create");
            listBox1.Items.Add("a user customizeable configuration file C:/ProgramData/Prior/SL160_LOADER_DATA-x.INI");
            listBox1.Items.Add("NOTE: user application must use the same stage co-ordinate system and stage units as this program.");
            listBox1.Items.Add("The exact stage initialisation sequence can be seen in the source for this program");
            listBox1.Items.Add("Stage (0,0) point is stage back-right,increasing XY position counts when moving front-left.");
            listBox1.Items.Add("If a different stage co-ordinate system is required, the user must recode this demo");
            listBox1.Items.Add("and recalibrate fully the system.");
            listBox1.Items.Add("");
            listBox1.Items.Add("Three types of system are catered for within the calibration:");
            listBox1.Items.Add("+ Fixed height stage - such as an OpenStand system.");
            listBox1.Items.Add("+ Variable height stage - stage mounted to a Prior controlled focus ie FB20x block.");
            listBox1.Items.Add("+ Variable height stage - stage mounted to a Microscope controlled focus mechanism.");
            listBox1.Items.Add("");
            listBox1.Items.Add("The stage will be automatically moved to the correct position to perform a scan/load/unload function.");
            listBox1.Items.Add("It is up to the users application to escape objectives safetly before any of these function.");
            listBox1.Items.Add("If the user has a microscope with its own focusing controls, then it is the user's");
            listBox1.Items.Add("responsibility to position Z to known calibrated position.");
            listBox1.Items.Add("A calibrated Z position *must* be lower than the in-focus Z position.");
            listBox1.Items.Add("");

            listBox1.Items.Add("'Eject Hotels'");
            listBox1.Items.Add("presents both hotels to user for removal.");
            listBox1.Items.Add("");

            listBox1.Items.Add("'Insert Hotels'");
            listBox1.Items.Add("detects hotels fitted and inserts them into unit");
            listBox1.Items.Add("");

            listBox1.Items.Add("'Scan'");
            listBox1.Items.Add("performs an auto detect of trays in apartment. Detected trays are marked in green");
            listBox1.Items.Add("");

            listBox1.Items.Add("'Load Tray To Stage'");
            listBox1.Items.Add("followed by green apartment click will transfer that tray to the stage.");
            listBox1.Items.Add("the tray will pause at preview 1/2/3/4 positions, click preview button to continue from each point.");
            listBox1.Items.Add("The preview is handled automatically during the automated soak routine.");
            listBox1.Items.Add("");

            listBox1.Items.Add("'Unload Tray From Stage' ");
            listBox1.Items.Add("'followed by empty apartment click will transfer tray on stage to the empty apartment.");
            listBox1.Items.Add("");

            listBox1.Items.Add("'options->single step mode' ");
            listBox1.Items.Add("is a debug facility that allows the robot to be 'single stepped' through its operation.");
            listBox1.Items.Add("Useful during initial installation.");
            listBox1.Items.Add("");

            listBox1.Items.Add("'options->start/stop soak'");
            listBox1.Items.Add("start/stop an automated soak routine that will continuously cycle");
            listBox1.Items.Add("through all trays that have been detected during the scan.");
            listBox1.Items.Add("");

            listBox1.Items.Add("'options->Check Calibration' ");
            listBox1.Items.Add("will guide you through a check sequence, although this can just as easily");
            listBox1.Items.Add("be done from the GUI with manual load/unloads.");
            listBox1.Items.Add("");

            listBox1.Items.Add("'options->Joystick'");
            listBox1.Items.Add("change direction and on/off states as required for XY stage and Z focus.");
            listBox1.Items.Add("");

            listBox1.Items.Add("'options->ReInitialise'");
            listBox1.Items.Add("after an emergency stop it is recommended to re-initialise in case the");
            listBox1.Items.Add("'robot has ben stopped in a compromised position (ie tray half in/out of hotel");
            listBox1.Items.Add("");

            listBox1.Items.Add("'options->PreviewOn'");
            listBox1.Items.Add("determines whether the slides are presented to the preview station during a load.");
            listBox1.Items.Add("");

            listBox1.Items.Add("'ManualMove'");
            listBox1.Items.Add("Allows for loader and stage axes to be driven manually.");
            listBox1.Items.Add("Extreme care is advised when manually moving stage or loader.");
            listBox1.Items.Add("");

            listBox1.Items.Add("HSM = Hotel Shuttle Mechanism");
            listBox1.Items.Add("HLM = Hotel Lifting Mechanism");
            listBox1.Items.Add("STM = Stage Transfer Mechanism");
            listBox1.Items.Add("");
            listBox1.Items.Add("");
            listBox1.Items.Add("Contact Prior Scientific for additional help. (www.prior.com/contact)");
        }
    }
}
