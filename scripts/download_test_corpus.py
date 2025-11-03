#!/usr/bin/env python3
"""
Download additional Fed documents for Document 03 test cases.
Focuses on periods around identified language shifts.
"""

import sys
sys.path.append('scripts')
from download_fed_docs import FedDocDownloader

def get_test_case_documents():
    """
    Define documents needed for Document 03 test cases.

    Test Case 1: "Transitory" shift (Apr 2021 - Dec 2021)
    - Window: Jan 2020 - Jun 2022

    Test Case 2: "Accommodative" removal (Sep 2018)
    - Window: Jan 2017 - Dec 2019
    """
    documents = []

    # TEST CASE 1: TRANSITORY SHIFT
    # Baseline period (2020)
    documents.extend([
        {'doc_type': 'policy_statement', 'date': '20200129', 'title': 'Jan 2020 Statement (Pre-COVID baseline)'},
        {'doc_type': 'policy_statement', 'date': '20200318', 'title': 'Mar 2020 Statement (COVID emergency)'},
        {'doc_type': 'policy_statement', 'date': '20200610', 'title': 'Jun 2020 Statement'},
        {'doc_type': 'policy_statement', 'date': '20200916', 'title': 'Sep 2020 Statement'},
        {'doc_type': 'policy_statement', 'date': '20201105', 'title': 'Nov 2020 Statement'},
        {'doc_type': 'policy_statement', 'date': '20201216', 'title': 'Dec 2020 Statement'},
    ])

    # Pre-transitory period (early 2021)
    documents.extend([
        {'doc_type': 'policy_statement', 'date': '20210127', 'title': 'Jan 2021 Statement'},
        {'doc_type': 'policy_statement', 'date': '20210317', 'title': 'Mar 2021 Statement'},
    ])

    # Transitory emergence and peak (mid-late 2021)
    documents.extend([
        {'doc_type': 'policy_statement', 'date': '20210428', 'title': 'Apr 2021 Statement (Transitory FIRST appears)'},
        # June 2021 already have
        # July 2021 minutes already have
        {'doc_type': 'policy_statement', 'date': '20210922', 'title': 'Sep 2021 Statement'},
        {'doc_type': 'policy_statement', 'date': '20211103', 'title': 'Nov 2021 Statement'},
        {'doc_type': 'policy_statement', 'date': '20211215', 'title': 'Dec 2021 Statement (Transitory REMOVED)'},
    ])

    # Post-transitory period (2022)
    documents.extend([
        {'doc_type': 'policy_statement', 'date': '20220126', 'title': 'Jan 2022 Statement'},
        {'doc_type': 'policy_statement', 'date': '20220316', 'title': 'Mar 2022 Statement (First rate hike)'},
        {'doc_type': 'policy_statement', 'date': '20220504', 'title': 'May 2022 Statement'},
        {'doc_type': 'policy_statement', 'date': '20220615', 'title': 'Jun 2022 Statement'},
    ])

    # TEST CASE 2: ACCOMMODATIVE REMOVAL
    # Baseline with "accommodative" (2017)
    documents.extend([
        {'doc_type': 'policy_statement', 'date': '20170201', 'title': 'Feb 2017 Statement (Accommodative baseline)'},
        {'doc_type': 'policy_statement', 'date': '20170614', 'title': 'Jun 2017 Statement'},
        {'doc_type': 'policy_statement', 'date': '20170920', 'title': 'Sep 2017 Statement'},
        {'doc_type': 'policy_statement', 'date': '20171213', 'title': 'Dec 2017 Statement'},
    ])

    # Pre-removal period (2018)
    documents.extend([
        {'doc_type': 'policy_statement', 'date': '20180131', 'title': 'Jan 2018 Statement'},
        {'doc_type': 'policy_statement', 'date': '20180321', 'title': 'Mar 2018 Statement'},
        {'doc_type': 'policy_statement', 'date': '20180613', 'title': 'Jun 2018 Statement'},
        {'doc_type': 'policy_statement', 'date': '20180926', 'title': 'Sep 2018 Statement (Accommodative REMOVED)'},
        # Dec 2018 already have
    ])

    # Post-removal period (2019)
    documents.extend([
        {'doc_type': 'policy_statement', 'date': '20190130', 'title': 'Jan 2019 Statement'},
        {'doc_type': 'policy_statement', 'date': '20190320', 'title': 'Mar 2019 Statement'},
        {'doc_type': 'policy_statement', 'date': '20190619', 'title': 'Jun 2019 Statement'},
        {'doc_type': 'policy_statement', 'date': '20190918', 'title': 'Sep 2019 Statement'},
        {'doc_type': 'policy_statement', 'date': '20191211', 'title': 'Dec 2019 Statement'},
    ])

    # Add corresponding FOMC minutes for key dates
    # (Minutes are 3 weeks after meeting, use same date code)
    minutes_dates = [
        # Transitory case - key meetings
        '20200129', '20200429', '20200610', '20200916', '20201216',
        '20210127', '20210317', '20210428', '20210616', '20210922', '20211103', '20211215',
        '20220126', '20220316',
        # Accommodative case - key meetings
        '20170614', '20171213', '20180321', '20180613', '20180926', '20181219',
        '20190130', '20190619', '20191211'
    ]

    for date in minutes_dates:
        documents.append({
            'doc_type': 'fomc_minutes',
            'date': date,
            'title': f'FOMC Minutes {date}'
        })

    return documents


def main():
    print("Document 03: Downloading Test Case Corpus")
    print("=" * 60)

    downloader = FedDocDownloader(output_dir="data/raw")
    documents = get_test_case_documents()

    print(f"\nPreparing to download {len(documents)} documents for test cases:")
    print(f"  - Test Case 1 (Transitory): ~30 documents (2020-2022)")
    print(f"  - Test Case 2 (Accommodative): ~20 documents (2017-2019)")
    print(f"  - Total: {len(documents)} documents\n")

    downloader.download_batch(documents)
    downloader.save_metadata(filepath="data/raw/test_corpus_metadata.json")

    print("\n✓ Test corpus download complete!")
    print("\nNext steps:")
    print("1. Run extraction script on new documents")
    print("2. Verify ground truth (check for 'transitory' and 'accommodative')")
    print("3. Begin implementing detection approaches")


if __name__ == "__main__":
    main()
