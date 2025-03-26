#include "stdafx.h"
#include "global.h"
#include "AutoTest.h"
#include "CWhiteBalancePropertyPage.h"

CWhiteBalancePropertyPage::CWhiteBalancePropertyPage()
	: CPropertyPage(IDD_PROPERTY_WHITE_BALANCE)
{
}

void CWhiteBalancePropertyPage::OnWhiteBalance()
{
	if (GetSafeHwnd())
	{
		int temp = 0, tint = 0;
		Mzcam_get_TempTint(g_hcam, &temp, &tint);
		SetTempValue(temp);
		SetTintValue(tint);
	}
}

void CWhiteBalancePropertyPage::SetTempValue(int value)
{
	((CSliderCtrl*)GetDlgItem(IDC_SLIDER_TEMP))->SetPos(value);
	SetDlgItemInt(IDC_STATIC_TEMP, value);
}

void CWhiteBalancePropertyPage::SetTintValue(int value)
{
	((CSliderCtrl*)GetDlgItem(IDC_SLIDER_TINT))->SetPos(value);
	SetDlgItemInt(IDC_STATIC_TINT, value);
}

BEGIN_MESSAGE_MAP(CWhiteBalancePropertyPage, CPropertyPage)
	ON_WM_HSCROLL()
	ON_BN_CLICKED(IDC_BUTTON_WHITE_BALANCE, &CWhiteBalancePropertyPage::OnBnClickedButtonWhiteBalance)
END_MESSAGE_MAP()

BOOL CWhiteBalancePropertyPage::OnInitDialog()
{
	CPropertyPage::OnInitDialog();

	((CSliderCtrl*)GetDlgItem(IDC_SLIDER_TEMP))->SetRange(MZCAM_TEMP_MIN, MZCAM_TEMP_MAX);
	SetTempValue(MZCAM_TEMP_DEF);
	((CSliderCtrl*)GetDlgItem(IDC_SLIDER_TINT))->SetRange(MZCAM_TINT_MIN, MZCAM_TINT_MAX);
	SetTintValue(MZCAM_TINT_DEF);

	return TRUE;
}

void CWhiteBalancePropertyPage::OnHScroll(UINT nSBCode, UINT nPos, CScrollBar* pScrollBar)
{
	int curTemp = 0, curTint = 0;
	if (pScrollBar == GetDlgItem(IDC_SLIDER_TEMP))
	{
		Mzcam_get_TempTint(g_hcam, &curTemp, &curTint);
		int temp = ((CSliderCtrl*)GetDlgItem(IDC_SLIDER_TEMP))->GetPos();
		if (temp != curTemp)
		{
			Mzcam_put_TempTint(g_hcam, temp, curTint);
			SetDlgItemInt(IDC_STATIC_TEMP, temp);
		}
	}
	else if (pScrollBar == GetDlgItem(IDC_SLIDER_TINT))
	{
		Mzcam_get_TempTint(g_hcam, &curTemp, &curTint);
		int tint = ((CSliderCtrl*)GetDlgItem(IDC_SLIDER_TINT))->GetPos();
		if (tint != curTint)
		{
			Mzcam_put_TempTint(g_hcam, curTemp, tint);
			SetDlgItemInt(IDC_STATIC_TINT, tint);
		}
	}

	CPropertyPage::OnHScroll(nSBCode, nPos, pScrollBar);
}

void CWhiteBalancePropertyPage::OnBnClickedButtonWhiteBalance()
{
	Mzcam_AwbOnce(g_hcam, nullptr, nullptr);
}
