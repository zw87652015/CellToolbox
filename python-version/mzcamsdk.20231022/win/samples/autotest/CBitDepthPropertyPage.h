#pragma once

class CBitDepthPropertyPage : public CPropertyPage
{
	int m_bitDepth;
public:
	CBitDepthPropertyPage();

#ifdef AFX_DESIGN_TIME
	enum { IDD = IDD_PROPERTY_BITDEPTH };
#endif

protected:
	virtual void DoDataExchange(CDataExchange* pDX);
	virtual BOOL OnInitDialog();
	afx_msg void OnBnClickedRadio8Bit();
	afx_msg void OnBnClickedRadioHighBit();
	DECLARE_MESSAGE_MAP()
};
