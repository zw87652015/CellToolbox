#ifndef __mzcam_labview_h__
#define __mzcam_labview_h__

#include "extcode.h"

#ifdef MZCAM_LABVIEW_EXPORTS
#define MZCAM_LABVIEW_API(x) __declspec(dllexport)    x   __cdecl
#else
#define MZCAM_LABVIEW_API(x) __declspec(dllimport)    x   __cdecl
#include "mzcam.h"
#endif

#ifdef __cplusplus
extern "C" {
#endif

MZCAM_LABVIEW_API(HRESULT) Start(HMzcam h, LVUserEventRef* rwer);

#ifdef __cplusplus
}
#endif

#endif