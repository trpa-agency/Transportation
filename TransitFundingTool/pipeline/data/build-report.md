# Data build 20261030a

Built 2026-10-30T19:55:15.

## Workbooks

- Example Transit Financial Scenario Workbook.xlsx, saved 2026-10-28T02:17:15, sha256 fccb9a121a47afb6
- Financial PlanG.xlsx, saved 2026-10-28T02:17:15, sha256 8e0aa78245720af0

## Warnings (0)

None.

## Workbook values that differ from the seed (0)

These came from the workbooks and replace the values stored in etl/seed. Copy them into the seed when you agree with them, so the seed stays a true record.

None.

## Seed values held over the workbook (21)

- Service 30: `dataYear` = '26-27 estimate' (workbook '26-27'). Data year label marks the estimate
- Service TART-WS: `stateCond` = 'California route' (workbook 'Califorrnia route'). Spelling fixed; the workbook reads 'Califorrnia route'
- Source ttd-5310: `matchText` = '20% non-federal' (workbook '50% non-federal'). 20 percent non-federal match per TRPA (Oct. 23, 2026); Revenue %s lists 50 percent
- Source ttd-5310: `fedShare` = 0.8 (workbook 0.5). 80 percent federal share per TRPA (Oct. 23, 2026); Revenue %s lists 50 percent. Confirm with FTA
- Source ttd-5310co: `matchText` = '20% non-federal' (workbook '50% non-federal'). 20 percent non-federal match per TRPA (Oct. 23, 2026); Revenue %s lists 50 percent
- Source ttd-5310co: `fedShare` = 0.8 (workbook 0.5). 80 percent federal share per TRPA (Oct. 23, 2026); Revenue %s lists 50 percent. Confirm with FTA
- Source ttd-lctop: shares held in the seed. Revenue %s row 15 divides by TTD hours including Route 30 but gives Route 30 nothing (data note 3)
- Source ttd-interest: shares held in the seed. Revenue %s row 20 divides by TTD hours including Route 30 but gives Route 30 nothing (data note 3)
- Source ll-slttid: `amount` = 25,000 (workbook 0). Carried steady at the FY 25-26 amount per TRPA (Oct. 23, 2026); the plan shows $0 for FY 26-27
- Source ll-heavenly: `amount` = 15,000 (workbook 0). Carried steady at the FY 25-26 amount per TRPA (Oct. 23, 2026); the plan shows $0 for FY 26-27
- Source ll-caesars: `amount` = 65,000 (workbook 0). Carried steady at the FY 25-26 amount per TRPA (Oct. 23, 2026); the plan shows $0 for FY 26-27
- Source ll-roundhill: `amount` = 85,000 (workbook 0). Carried steady at the FY 25-26 amount per TRPA (Oct. 23, 2026); the plan shows $0 for FY 26-27
- Source ll-advlearn: `amount` = 25,000 (workbook 0). Carried steady at the FY 25-26 amount per TRPA (Oct. 23, 2026); the plan shows $0 for FY 26-27
- Source ll-ltva: `amount` = 62,100 (workbook 0). Carried steady at the FY 25-26 amount per TRPA (Oct. 23, 2026); the plan shows $0 for FY 26-27
- Source ll-ltcc: `amount` = 25,000 (workbook 0). Carried steady at the FY 25-26 amount per TRPA (Oct. 23, 2026); the plan shows $0 for FY 26-27
- Source tart-5307: shares held in the seed. Revenue %s row 3 TART shares sum to 72 percent because TART total VSH counts Main Line twice (data note 3)
- Source tart-5310: `matchText` = '20% non-federal' (workbook '50% non-federal'). 20 percent non-federal match per TRPA (Oct. 23, 2026); Revenue %s lists 50 percent
- Source tart-5310: `fedShare` = 0.8 (workbook 0.5). 80 percent federal share per TRPA (Oct. 23, 2026); Revenue %s lists 50 percent. Confirm with FTA
- Source tart-washoe: shares held in the seed. Revenue %s row 25 puts shares on Main Line and NLTE; Washoe RTC funds only TART Nevada (route restriction)
- Source tart-martis: `amount` = 50,000 (workbook 0). Carried steady at the FY 25-26 amount per TRPA (Oct. 23, 2026); the plan shows $0 for FY 26-27
- Source tnt-ntca: `amount` = 487,173 (workbook 0). Carried steady at the FY 25-26 amount per TRPA (Oct. 23, 2026); the plan shows $0 for FY 26-27
