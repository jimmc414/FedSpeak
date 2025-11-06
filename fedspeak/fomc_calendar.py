"""
FOMC Meeting Calendar
Actual Federal Reserve FOMC meeting dates for accurate document downloads.

Source: Federal Reserve official calendar
https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm

Note: Dates represent FOMC policy statement release dates (typically 2pm EST).
Format: YYYYMMDD as used in Fed URLs
"""

# FOMC meeting dates by year
# Each year typically has 8 scheduled meetings
FOMC_MEETINGS = {
    # 2025 (scheduled)
    2025: [
        '20250129',  # Jan 28-29
        '20250319',  # Mar 18-19
        '20250507',  # May 6-7
        '20250618',  # Jun 17-18
        '20250730',  # Jul 29-30
        '20250917',  # Sep 16-17
        '20251105',  # Nov 4-5
        '20251217',  # Dec 16-17
    ],

    # 2024
    2024: [
        '20240131',  # Jan 30-31
        '20240320',  # Mar 19-20
        '20240501',  # Apr 30 - May 1
        '20240612',  # Jun 11-12
        '20240731',  # Jul 30-31
        '20240918',  # Sep 17-18
        '20241107',  # Nov 6-7
        '20241218',  # Dec 17-18
    ],

    # 2023
    2023: [
        '20230201',  # Jan 31 - Feb 1
        '20230322',  # Mar 21-22
        '20230503',  # May 2-3
        '20230614',  # Jun 13-14
        '20230726',  # Jul 25-26
        '20230920',  # Sep 19-20
        '20231101',  # Oct 31 - Nov 1
        '20231213',  # Dec 12-13
    ],

    # 2022
    2022: [
        '20220126',  # Jan 25-26
        '20220316',  # Mar 15-16
        '20220504',  # May 3-4
        '20220615',  # Jun 14-15
        '20220727',  # Jul 26-27
        '20220921',  # Sep 20-21
        '20221102',  # Nov 1-2
        '20221214',  # Dec 13-14
    ],

    # 2021
    2021: [
        '20210127',  # Jan 26-27
        '20210317',  # Mar 16-17
        '20210428',  # Apr 27-28
        '20210616',  # Jun 15-16
        '20210728',  # Jul 27-28
        '20210922',  # Sep 21-22
        '20211103',  # Nov 2-3
        '20211215',  # Dec 14-15
    ],

    # 2020
    2020: [
        '20200129',  # Jan 28-29
        '20200303',  # Mar 3 (unscheduled)
        '20200315',  # Mar 15 (unscheduled - COVID)
        '20200323',  # Mar 23 (unscheduled - COVID)
        '20200429',  # Apr 28-29
        '20200610',  # Jun 9-10
        '20200729',  # Jul 28-29
        '20200916',  # Sep 15-16
        '20201105',  # Nov 4-5
        '20201216',  # Dec 15-16
    ],

    # 2019
    2019: [
        '20190130',  # Jan 29-30
        '20190320',  # Mar 19-20
        '20190501',  # Apr 30 - May 1
        '20190619',  # Jun 18-19
        '20190731',  # Jul 30-31
        '20190918',  # Sep 17-18
        '20191030',  # Oct 29-30
        '20191211',  # Dec 10-11
    ],

    # 2018
    2018: [
        '20180131',  # Jan 30-31
        '20180321',  # Mar 20-21
        '20180502',  # May 1-2
        '20180613',  # Jun 12-13
        '20180801',  # Jul 31 - Aug 1
        '20180926',  # Sep 25-26
        '20181108',  # Nov 7-8
        '20181219',  # Dec 18-19
    ],

    # 2017
    2017: [
        '20170201',  # Jan 31 - Feb 1
        '20170315',  # Mar 14-15
        '20170503',  # May 2-3
        '20170614',  # Jun 13-14
        '20170726',  # Jul 25-26
        '20170920',  # Sep 19-20
        '20171101',  # Oct 31 - Nov 1
        '20171213',  # Dec 12-13
    ],

    # 2016
    2016: [
        '20160127',  # Jan 26-27
        '20160316',  # Mar 15-16
        '20160427',  # Apr 26-27
        '20160615',  # Jun 14-15
        '20160727',  # Jul 26-27
        '20160921',  # Sep 20-21
        '20161102',  # Nov 1-2
        '20161214',  # Dec 13-14
    ],

    # 2015
    2015: [
        '20150128',  # Jan 27-28
        '20150318',  # Mar 17-18
        '20150429',  # Apr 28-29
        '20150617',  # Jun 16-17
        '20150729',  # Jul 28-29
        '20150917',  # Sep 16-17
        '20151028',  # Oct 27-28
        '20151216',  # Dec 15-16
    ],

    # 2014
    2014: [
        '20140129',  # Jan 28-29
        '20140319',  # Mar 18-19
        '20140430',  # Apr 29-30
        '20140618',  # Jun 17-18
        '20140730',  # Jul 29-30
        '20140917',  # Sep 16-17
        '20141029',  # Oct 28-29
        '20141217',  # Dec 16-17
    ],

    # 2013
    2013: [
        '20130130',  # Jan 29-30
        '20130320',  # Mar 19-20
        '20130501',  # Apr 30 - May 1
        '20130619',  # Jun 18-19
        '20130731',  # Jul 30-31
        '20130918',  # Sep 17-18
        '20131030',  # Oct 29-30
        '20131218',  # Dec 17-18
    ],

    # 2012
    2012: [
        '20120125',  # Jan 24-25
        '20120313',  # Mar 13
        '20120425',  # Apr 24-25
        '20120620',  # Jun 19-20
        '20120801',  # Jul 31 - Aug 1
        '20120913',  # Sep 12-13
        '20121024',  # Oct 23-24
        '20121212',  # Dec 11-12
    ],

    # 2011
    2011: [
        '20110126',  # Jan 25-26
        '20110315',  # Mar 15
        '20110427',  # Apr 26-27
        '20110622',  # Jun 21-22
        '20110809',  # Aug 9
        '20110921',  # Sep 20-21
        '20111102',  # Nov 1-2
        '20111213',  # Dec 13
    ],

    # 2010
    2010: [
        '20100127',  # Jan 26-27
        '20100316',  # Mar 16
        '20100428',  # Apr 27-28
        '20100623',  # Jun 22-23
        '20100810',  # Aug 10
        '20100921',  # Sep 21
        '20101103',  # Nov 2-3
        '20101214',  # Dec 14
    ],

    # 2009
    2009: [
        '20090128',  # Jan 27-28
        '20090318',  # Mar 18
        '20090429',  # Apr 28-29
        '20090624',  # Jun 23-24
        '20090812',  # Aug 12
        '20090923',  # Sep 23
        '20091104',  # Nov 3-4
        '20091216',  # Dec 16
    ],

    # 2008
    2008: [
        '20080130',  # Jan 29-30
        '20080318',  # Mar 18
        '20080430',  # Apr 29-30
        '20080625',  # Jun 24-25
        '20080805',  # Aug 5
        '20080916',  # Sep 16
        '20081029',  # Oct 28-29
        '20081216',  # Dec 15-16
    ],
}


def get_fomc_dates(start_year: int, end_year: int) -> list:
    """
    Get FOMC meeting dates for a range of years.

    Args:
        start_year: Starting year (inclusive)
        end_year: Ending year (inclusive)

    Returns:
        List of date strings in YYYYMMDD format, sorted
    """
    dates = []
    for year in range(start_year, end_year + 1):
        if year in FOMC_MEETINGS:
            dates.extend(FOMC_MEETINGS[year])
        else:
            # Year not in calendar - return empty for that year
            # This is expected for years < 2008 or far future
            pass

    return sorted(dates)


def get_meetings_in_date_range(start_date: str, end_date: str) -> list:
    """
    Get FOMC meetings within a specific date range.

    Args:
        start_date: Start date in YYYYMMDD format
        end_date: End date in YYYYMMDD format

    Returns:
        List of meeting dates in YYYYMMDD format
    """
    all_dates = []
    for dates in FOMC_MEETINGS.values():
        all_dates.extend(dates)

    # Filter to date range
    filtered = [d for d in all_dates if start_date <= d <= end_date]

    return sorted(filtered)


if __name__ == '__main__':
    # Quick verification
    print("FOMC Calendar Summary:")
    print(f"Years covered: {min(FOMC_MEETINGS.keys())} - {max(FOMC_MEETINGS.keys())}")
    print(f"Total meetings: {sum(len(dates) for dates in FOMC_MEETINGS.values())}")
    print(f"\nMeetings per year:")
    for year in sorted(FOMC_MEETINGS.keys(), reverse=True):
        print(f"  {year}: {len(FOMC_MEETINGS[year])} meetings")
