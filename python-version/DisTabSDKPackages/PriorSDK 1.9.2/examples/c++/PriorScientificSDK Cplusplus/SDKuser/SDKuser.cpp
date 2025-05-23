// SDKuser.cpp : Defines the entry point for the console application.
//

/**
 * @file    sdkUser
 * @date    5/5/2020
 * @brief   This project contains example source for using PriorSDK
 * @copyright   Copyright (c) 2020- Prior Scientific Instruments Ltd. All rights reserved
 *
 * This software is provided 'as is' without warranty of any kind, either express or implied,
 * including, but not limited to, the implied warranties of fitness for a purpose, or the
 * warranty of non-infringement. Without limiting the foregoing, Prior Scientific
 * makes no warranty that:
 * 
 *    1. the software will meet your requirements
 *    2. the software will be uninterrupted, timely, secure or error-free
 *    3. the results that may be obtained from the use of the software will be effective,
 *       accurate or reliable
 *    4. the quality of the software will meet your expectations
 *    5. any errors in the software obtained will be corrected.
 * 
 * Software and its documentation made available from Prior:
 * 
 *    6. could include technical or other mistakes, inaccuracies or typographical errors.
 *       Prior may make changes to the software or documentation made available.
 *    7. may be out of date, and Prior makes no commitment to update such materials.
 * 
 * Prior assumes no responsibility for errors or ommissions in the software or documentation
 * available from its web site. In no event shall Prior be liable to you or any third
 * parties for any special, punitive, incidental, indirect or consequential damages of any
 * kind, or any damages whatsoever, including, without limitation, those resulting from loss
 * of use, data or profits, whether or not Prior has been advised of the possibility of such
 * damages, and on any theory of liability, arising out of or in connection with the use of
 * this software.
 * The use of this software is at your own discretion
 * and risk and with agreement that you will be solely responsible for any damage to your
 * computer system or loss of data that results from such activities. No advice or information,
 * whether oral or written, obtained by you from Prior shall create
 * any warranty for the software.
 * */

#include "stdafx.h"
#include "PriorScientificSDK.h"
#include <iostream> 
using namespace std; 

/* PriorScientificSDK.dll implicitly linked through PriorScientificSDK.lib. See solution properties */

/*  use c++ interface from PriorScientificSDK.h */
PriorScientificSDK priorSDK;

/* uncomment when real hw available */
//#define realhw

char rx[1000];
int ret;
int sessionID = 0;

int  Cmd(char *tx)
{
	cout <<  tx << endl;
	if (!(ret = priorSDK.Cmd(sessionID,tx,rx)))
		cout <<  "OK " << rx << endl;
	else
		cout << "Api error " << ret << endl;

	system("pause");

	return 0;
}

int _tmain(int argc, _TCHAR* argv[])
{
	int focusFitted = 0;
	int stageFitted = 0;
	int stageBusy = 0;
	int zBusy = 0;

	rx[0] = 0;

	/* always call Initialise first */
	ret = priorSDK.Initialise();

	if (ret != PRIOR_OK)
	{
		cout << "Error initialising " << ret << endl;
		return -1;
	}
	else
		cout << "Ok initialising " << ret << endl;
	
	/* get version number, check ret = 0, and rx contains correct version information */
	ret = priorSDK.Version((char *const)rx);

	cout << "dll version api ret=" << ret << ", version=" << rx << endl;

	/* create the session, can be up to 10 */
	sessionID = priorSDK.OpenSession();

	if (sessionID < 0)
	{
		cout << "Error getting sessionId " << ret << endl;
		return -1;
	}
	else
		cout << "sessionId " << sessionID << endl;
	

#ifndef realhw	
	/* the following two commands use a built in API test command 
	* which returns the first parameter as the API return code and
	* the second parameter string is copied back to the user via rx buffer
	*/
	ret = priorSDK.Cmd(sessionID,"dll.apitest 33 goodresponse",rx);
	cout << "api response " << ret << ", rx = " << rx << endl;
	system("pause");

	ret = priorSDK.Cmd(sessionID,"dll.apitest -300 stillgoodresponse",rx);
	cout << "api response " << ret << ", rx = " << rx << endl;
	system("pause");
#else
	cout << "connecting ..." << endl;

	/* substitute with your com port Id */
	Cmd ("controller.connect 5");

	/* get model, ie H31, ES11 etc */
	Cmd ("controller.model.get");

	/* see if Z fitted */
	Cmd ("controller.z.fitted.get");
	focusFitted = atoi(rx); 
	Cmd ("controller.z.name.get");

	/* see if stage fitted */
	Cmd ("controller.stage.fitted.get");
	stageFitted = atoi(rx);
	Cmd ("controller.stage.name.get");

	/* test an illegal command */
	Cmd("controller.stage.position.getx");



	if (stageFitted)
	{
		/* get current XY position in default units of microns */
		Cmd("controller.stage.position.get");

		/* re-define this current position as 1234,5678 */
		Cmd("controller.stage.position.set 1234 5678");

		/* check it worked */
		Cmd("controller.stage.position.get");

		/* set it back to 0,0 */
		Cmd("controller.stage.position.set 0 0");
		Cmd("controller.stage.position.get");

		/* start a move to a new position */
		Cmd("controller.stage.goto-position 1234 5678");

		/*  normally you would poll 'controller.stage.busy.get' until response = 0 */
		do
		{
			priorSDK.Cmd(sessionID,"controller.stage.busy.get",rx);

			stageBusy = atoi(rx);
		} while (stageBusy != 0);

		Cmd("controller.stage.position.get");

		/* example velocity move of 10u/s in both x and y */
		Cmd("controller.stage.move-at-velocity 10 10");

		/* see busy status */
		Cmd("controller.stage.busy.get");

		/* stop velocity move */
		Cmd("controller.stage.move-at-velocity 0 0");

		/* see busy status */
		Cmd("controller.stage.busy.get");

		/* see new position */
		Cmd("controller.stage.position.get");
	}
	else
	{
		cout << "no stage!" << endl;
	}

	if (focusFitted)
	{
		/* get current z position in default units of 100nm */
		Cmd("controller.z.position.get");

		/* re-define this current position as 1234 */
		Cmd("controller.z.position.set 1234");

		/* check it worked */
		Cmd("controller.z.position.get");

		/* set it back to 0 */
		Cmd("controller.z.position.set 0");
		Cmd("controller.z.position.get");

		/* start a move to a new position */
		Cmd("controller.z.goto-position 1234");

		/*  normally you would poll 'controller.z.busy.get' until response = 0 */
		do
		{
			priorSDK.Cmd(sessionID,"controller.z.busy.get",rx);

			zBusy = atoi(rx);
		} while (zBusy != 0);

		Cmd("controller.z.position.get");

		/* example velocity move of 5u/s in  z */
		Cmd("controller.z.move-at-velocity 5");

		/* see busy status */
		Cmd("controller.z.busy.get");

		/* stop velocity move */
		Cmd("controller.z.move-at-velocity 0");

		/* see busy status */
		Cmd("controller.z.busy.get");

		/* see new position */
		Cmd("controller.z.position.get");
	}
	else
	{
		cout << "no focus!" << endl;
	}


	/* disconnect cleanly from controller */
	Cmd ("controller.disconnect");

#endif

	ret = priorSDK.CloseSession(sessionID);
	cout << "CloseSession " << ret << endl;

	system("pause");

	return 0;
}

