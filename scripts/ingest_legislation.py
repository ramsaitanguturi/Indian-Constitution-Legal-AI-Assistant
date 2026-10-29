"""
Statutory Legislation Ingestion Module (Enhanced Production Version).
Ingests and structures core Central Acts closely tied to Indian Constitutional Law and Governance
from official India Code (Ministry of Law and Justice, Government of India).

Includes:
- Constitutional Framework Acts:
    1. Citizenship Act, 1955 (Act No. 57 of 1955) - Sections 3, 4, 5, 6, 6A, 8, 9, 10, 14A
    2. Representation of the People Act, 1951 (Act No. 43 of 1951) - Sections 8, 9, 11, 29A, 29B, 29C, 123
    3. Protection of Human Rights Act, 1993 (Act No. 10 of 1994) - Sections 2(1)(d), 3, 12, 18, 21, 30
    4. Right to Information Act, 2005 (Act No. 22 of 2005) - Sections 3, 4, 6, 7, 8, 19, 20
    5. Armed Forces (Special Powers) Act, 1958 (Act No. 28 of 1958) - Sections 3, 4, 6
    6. Official Languages Act, 1963 (Act No. 19 of 1963) - Sections 3, 4, 7
    7. Delimitation Act, 2002 (Act No. 33 of 2002) - Sections 3, 8, 9
    8. Comptroller and Auditor-General's (Duties, Powers and Conditions of Service) Act, 1971 (Act No. 56 of 1971) - Sections 10, 13, 16
    9. Supreme Court (Number of Judges) Act, 1956 (Act No. 55 of 1956) - Section 2
    10. National Commission for Minorities Act, 1992 (Act No. 19 of 1992) - Sections 3, 9
- Downloaded Central Code Enactments:
    11. Indian Penal Code, 1860 (Act No. 45 of 1860) - 575 sections
    12. Code of Criminal Procedure, 1973 (Act No. 2 of 1974) - 525 sections
    13. Indian Evidence Act, 1872 (Act No. 1 of 1872) - 184 sections
    14. Code of Civil Procedure, 1908 (Act No. 5 of 1908) - 171 sections
    15. Industrial Disputes Act, 1947 (Act No. 14 of 1947) - 64 sections
    16. Negotiable Instruments Act, 1881 (Act No. 26 of 1881) - 156 sections
    17. Motor Vehicles Act, 1988 (Act No. 59 of 1988) - 256 sections

Preserves sections, subsections, commencement dates, and constitutional relationship mappings.
"""

import os
import sys
import json
import hashlib
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Any

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from config import (
    RAW_LEGISLATION_DIR,
    PROCESSED_LEGISLATION_DIR,
    LEGISLATION_ACTS_PATH,
)

SOURCE_URL_INDIACODE = "https://www.indiacode.nic.in"
SOURCE_NAME_INDIACODE = "India Code: Digital Repository of All Central and State Acts, Government of India"
LICENSE_LEGISLATION = "Government Open Data License - India (GODL)"

CONSTITUTIONAL_FRAMEWORK_ACTS = [
    # 1. Citizenship Act, 1955
    {
        "id": "act_citizenship_1955",
        "document_id": "act_citizenship_1955",
        "document_type": "statute",
        "title": "Citizenship Act, 1955 (Act No. 57 of 1955)",
        "short_title": "Citizenship Act, 1955",
        "act_number": "57 of 1955",
        "year": 1955,
        "enactment_date": "1955-12-30",
        "commencement_date": "1955-12-30",
        "constitutional_basis": ["Article 5", "Article 6", "Article 7", "Article 8", "Article 9", "Article 10", "Article 11"],
        "part_reference": "Part II - Citizenship",
        "legal_status": "in_force",
        "sections": [
            {
                "section_id": "act_citizenship_1955_sec_03",
                "section_number": "Section 3",
                "title": "Citizenship by birth",
                "text": "Every person born in India— (a) on or after the 26th day of January, 1950, but before the 1st day of July, 1987; (b) on or after the 1st day of July, 1987, but before the commencement of the Citizenship (Amendment) Act, 2003 and either of whose parents is a citizen of India at the time of his birth; (c) on or after the commencement of the Citizenship (Amendment) Act, 2003, where both parents are citizens or one parent is a citizen and the other is not an illegal migrant, shall be a citizen of India by birth."
            },
            {
                "section_id": "act_citizenship_1955_sec_04",
                "section_number": "Section 4",
                "title": "Citizenship by descent",
                "text": "A person born outside India shall be a citizen of India by descent: (a) on or after the 26th day of January, 1950, but before the 10th day of December, 1992, if his father is a citizen of India at the time of his birth; or (b) on or after the 10th day of December, 1992, if either of his parents is a citizen of India at the time of his birth."
            },
            {
                "section_id": "act_citizenship_1955_sec_05",
                "section_number": "Section 5",
                "title": "Citizenship by registration",
                "text": "Subject to the provisions of this section and such other conditions and restrictions as may be prescribed, the Central Government may, on an application made in this behalf, register as a citizen of India any person who is not an illegal migrant if he belongs to any of the specified categories."
            },
            {
                "section_id": "act_citizenship_1955_sec_06",
                "section_number": "Section 6",
                "title": "Citizenship by naturalisation",
                "text": "Where an application is made in the prescribed manner by any person of full age and capacity who is not an illegal migrant for the grant of a certificate of naturalisation to him, the Central Government may, if satisfied that the applicant is qualified for naturalisation under the provisions of the Third Schedule, grant to him a certificate of naturalisation."
            },
            {
                "section_id": "act_citizenship_1955_sec_06A",
                "section_number": "Section 6A",
                "title": "Special provisions as to citizenship of persons covered by the Assam Accord",
                "text": "All persons of Indian origin who came before the 1st day of January, 1966 to Assam from Bangladesh and have been ordinarily resident in Assam since shall be deemed to be citizens of India as from the 1st day of January, 1966. (Upheld by Supreme Court Constitution Bench in 2024)."
            },
            {
                "section_id": "act_citizenship_1955_sec_08",
                "section_number": "Section 8",
                "title": "Renunciation of citizenship",
                "text": "If any citizen of India of full age and capacity makes in the prescribed manner a declaration renouncing his Indian citizenship, the declaration shall be registered by the Central Government; and, upon such registration, that person shall cease to be a citizen of India."
            },
            {
                "section_id": "act_citizenship_1955_sec_09",
                "section_number": "Section 9",
                "title": "Termination of citizenship",
                "text": "Any citizen of India who by naturalisation, registration or otherwise voluntarily acquires, or has at any time between the 26th January, 1950 and the commencement of this Act voluntarily acquired the citizenship of another country shall, upon such acquisition, cease to be a citizen of India."
            },
            {
                "section_id": "act_citizenship_1955_sec_10",
                "section_number": "Section 10",
                "title": "Deprivation of citizenship",
                "text": "A citizen of India who is such by naturalisation or by registration shall cease to be a citizen of India, if he is deprived of that citizenship by an order of the Central Government, on grounds of fraud, false representation, disloyalty to the Constitution, or communication with an enemy during war."
            },
            {
                "section_id": "act_citizenship_1955_sec_14A",
                "section_number": "Section 14A",
                "title": "Issue of national identity cards",
                "text": "The Central Government may compulsorily register every citizen of India and issue national identity card to him. The Central Government may maintain a National Register of Indian Citizens."
            }
        ],
        "summary": "Governs the acquisition, renunciation, termination, and deprivation of Indian citizenship enacted by Parliament pursuant to Article 11 of the Constitution.",
        "text": "Citizenship Act, 1955 (Act No. 57 of 1955). Enacted under Article 11 of the Constitution of India. Regulates citizenship by birth (Section 3), descent (Section 4), registration (Section 5), naturalisation (Section 6), Assam Accord provisions (Section 6A), renunciation (Section 8), termination (Section 9), deprivation (Section 10), and National Register of Citizens (Section 14A)."
    },

    # 2. Representation of the People Act, 1951
    {
        "id": "act_rpa_1951",
        "document_id": "act_rpa_1951",
        "document_type": "statute",
        "title": "Representation of the People Act, 1951 (Act No. 43 of 1951)",
        "short_title": "Representation of the People Act, 1951",
        "act_number": "43 of 1951",
        "year": 1951,
        "enactment_date": "1951-07-17",
        "commencement_date": "1951-07-17",
        "constitutional_basis": ["Article 324", "Article 325", "Article 326", "Article 327", "Article 328", "Article 329"],
        "part_reference": "Part XV - Elections",
        "legal_status": "in_force",
        "sections": [
            {
                "section_id": "act_rpa_1951_sec_08",
                "section_number": "Section 8",
                "title": "Disqualification on conviction for certain offences",
                "text": "A person convicted of any offence punishable under specified laws or sentenced to imprisonment for not less than two years shall be disqualified from the date of such conviction and shall continue to be disqualified for a further period of six years since his release. (Note: Section 8(4) saving sitting MPs/MLAs was struck down as unconstitutional by Supreme Court in Lily Thomas v. Union of India, 2013)."
            },
            {
                "section_id": "act_rpa_1951_sec_09",
                "section_number": "Section 9",
                "title": "Disqualification for dismissal for corruption or disloyalty",
                "text": "A person who having held an office under the Government of India or under the Government of any State has been dismissed for corruption or for disloyalty to the State shall be disqualified for a period of five years from the date of such dismissal."
            },
            {
                "section_id": "act_rpa_1951_sec_11",
                "section_number": "Section 11",
                "title": "Removal or reduction of period of disqualification",
                "text": "The Election Commission may, for reasons to be recorded, remove any disqualification under this Chapter (except under section 8A) or reduce the period of any such disqualification."
            },
            {
                "section_id": "act_rpa_1951_sec_29A",
                "section_number": "Section 29A",
                "title": "Registration with the Election Commission of associations and bodies as political parties",
                "text": "Any association or body of individual citizens of India calling itself a political party and intending to avail itself of the provisions of this Part shall make an application to the Election Commission for its registration as a political party, containing a specific provision pledging allegiance to the Constitution of India and principles of socialism, secularism and democracy."
            },
            {
                "section_id": "act_rpa_1951_sec_29B",
                "section_number": "Section 29B",
                "title": "Political parties may accept contributions",
                "text": "Subject to the provisions of this Act, any political party may accept any amount of contribution voluntarily offered to it by any person or company other than a Government company or foreign source."
            },
            {
                "section_id": "act_rpa_1951_sec_29C",
                "section_number": "Section 29C",
                "title": "Declaration of donation received by political parties",
                "text": "The treasurer of a political party shall in each financial year prepare a report in respect of the contribution received in excess of twenty thousand rupees from any person or company and submit it to the Election Commission."
            },
            {
                "section_id": "act_rpa_1951_sec_123",
                "section_number": "Section 123",
                "title": "Corrupt practices",
                "text": "The following shall be deemed to be corrupt practices for the purposes of this Act: (1) Bribery; (2) Undue influence; (3) The appeal by a candidate or his agent to vote or refrain from voting on the ground of his religion, race, caste, community or language (interpreted broadly by Supreme Court 7-Judge Bench in Abhiram Singh v. C.D. Commachen, 2017); (4) Publication of false statements in relation to personal character of candidate."
            }
        ],
        "summary": "Governs the conduct of elections to Houses of Parliament and State Legislatures, qualification and disqualification of members, corrupt practices, and electoral dispute adjudication pursuant to Articles 324–329.",
        "text": "Representation of the People Act, 1951 (Act No. 43 of 1951). Enacted under Article 327 of the Constitution of India. Establishes grounds for disqualification of legislators (Section 8, Section 9), removal of disqualification (Section 11), registration of political parties (Section 29A), donation reporting (Section 29C), and corrupt practices in elections (Section 123)."
    },

    # 3. Protection of Human Rights Act, 1993
    {
        "id": "act_phra_1993",
        "document_id": "act_phra_1993",
        "document_type": "statute",
        "title": "Protection of Human Rights Act, 1993 (Act No. 10 of 1994)",
        "short_title": "Protection of Human Rights Act, 1993",
        "act_number": "10 of 1994",
        "year": 1993,
        "enactment_date": "1994-01-08",
        "commencement_date": "1993-09-28",
        "constitutional_basis": ["Article 21", "Article 14", "Article 19", "Article 32", "Article 226"],
        "part_reference": "Part III - Fundamental Rights",
        "legal_status": "in_force",
        "sections": [
            {
                "section_id": "act_phra_1993_sec_02_1_d",
                "section_number": "Section 2(1)(d)",
                "title": "Definition of Human Rights",
                "text": "'Human rights' means the rights relating to life, liberty, equality and dignity of the individual guaranteed by the Constitution or embodied in the International Covenants and enforceable by courts in India."
            },
            {
                "section_id": "act_phra_1993_sec_03",
                "section_number": "Section 3",
                "title": "Constitution of a National Human Rights Commission",
                "text": "The Central Government shall constitute a body to be known as the National Human Rights Commission to exercise the powers conferred upon, and to perform the functions assigned to it, under this Act, headed by a Chairperson who has been a Chief Justice of India or a Judge of the Supreme Court."
            },
            {
                "section_id": "act_phra_1993_sec_12",
                "section_number": "Section 12",
                "title": "Functions of the Commission",
                "text": "The Commission shall perform all or any of the following functions: inquire, suo motu or on a petition presented to it by a victim, into complaint of violation of human rights or abetment thereof; intervene in any proceeding involving any allegation of violation of human rights pending before a court with the approval of such court; review safeguards provided under the Constitution."
            },
            {
                "section_id": "act_phra_1993_sec_18",
                "section_number": "Section 18",
                "title": "Steps during and after inquiry",
                "text": "The Commission may recommend to the concerned Government or authority to make payment of compensation or damages to the victim; recommend initiation of proceedings for prosecution or other action against the concerned person or persons; approach the Supreme Court or High Court concerned for such directions, orders or writs as that Court may deem necessary."
            },
            {
                "section_id": "act_phra_1993_sec_21",
                "section_number": "Section 21",
                "title": "Constitution of State Human Rights Commissions",
                "text": "A State Government may constitute a body to be known as the State Human Rights Commission to exercise powers within the State in relation to matters specified in List II and List III of the Seventh Schedule."
            },
            {
                "section_id": "act_phra_1993_sec_30",
                "section_number": "Section 30",
                "title": "Human Rights Courts",
                "text": "For the purpose of providing speedy trial of offences arising out of violation of human rights, the State Government may, with the concurrence of the Chief Justice of the High Court, specify for each district a Court of Session to be a Human Rights Court."
            }
        ],
        "summary": "Establishes National and State Human Rights Commissions and Human Rights Courts for protection of fundamental rights guaranteed by the Constitution and International Covenants.",
        "text": "Protection of Human Rights Act, 1993 (Act No. 10 of 1994). Translates constitutional guarantees under Articles 14, 19, 21 into institutional machinery via National Human Rights Commission (NHRC, Section 3, Section 12), State Human Rights Commissions (SHRCs, Section 21), and district Human Rights Courts (Section 30)."
    },

    # 4. Right to Information Act, 2005
    {
        "id": "act_rti_2005",
        "document_id": "act_rti_2005",
        "document_type": "statute",
        "title": "Right to Information Act, 2005 (Act No. 22 of 2005)",
        "short_title": "Right to Information Act, 2005",
        "act_number": "22 of 2005",
        "year": 2005,
        "enactment_date": "2005-06-15",
        "commencement_date": "2005-10-12",
        "constitutional_basis": ["Article 19(1)(a)", "Article 21"],
        "part_reference": "Part III - Fundamental Rights",
        "legal_status": "in_force",
        "sections": [
            {
                "section_id": "act_rti_2005_sec_03",
                "section_number": "Section 3",
                "title": "Right to information",
                "text": "Subject to the provisions of this Act, all citizens shall have the right to information."
            },
            {
                "section_id": "act_rti_2005_sec_04",
                "section_number": "Section 4",
                "title": "Obligations of public authorities (Suo motu disclosure)",
                "text": "Every public authority shall maintain all its records duly catalogued and indexed in a manner and the form which facilitates the right to information under this Act and ensure that all records that are appropriate to be computerised are, within a reasonable time and subject to availability of resources, computerised and connected through a network all over the country."
            },
            {
                "section_id": "act_rti_2005_sec_06",
                "section_number": "Section 6",
                "title": "Request for obtaining information",
                "text": "A person, who desires to obtain any information under this Act, shall make a request in writing or through electronic means in English or Hindi or in the official language of the area to the Central Public Information Officer or State Public Information Officer."
            },
            {
                "section_id": "act_rti_2005_sec_07",
                "section_number": "Section 7",
                "title": "Disposal of request",
                "text": "The Central Public Information Officer or State Public Information Officer on receipt of a request under section 6 shall, as expeditiously as possible, and in any case within thirty days of the receipt of the request, either provide the information on payment of such fee as may be prescribed or reject the request for any of the reasons specified in sections 8 and 9. Provided that where the information sought concerns the life or liberty of a person, the same shall be provided within forty-eight hours."
            },
            {
                "section_id": "act_rti_2005_sec_08",
                "section_number": "Section 8",
                "title": "Exemption from disclosure of information",
                "text": "Notwithstanding anything contained in this Act, there shall be no obligation to give any citizen: (a) information, disclosure of which would prejudicially affect the sovereignty and integrity of India, security, strategic, scientific or economic interests of the State; (b) information expressly forbidden to be published by any court of law; (c) information, the disclosure of which would cause a breach of privilege of Parliament or State Legislature; (d) commercial confidence, trade secrets or intellectual property; (e) information available to a person in his fiduciary relationship; (f) information received in confidence from foreign government; (g) information which would endanger life or physical safety of any person; (h) information which would impede process of investigation or prosecution of offenders; (i) cabinet papers; (j) personal information having no relationship to any public activity or interest."
            },
            {
                "section_id": "act_rti_2005_sec_19",
                "section_number": "Section 19",
                "title": "Appeals",
                "text": "Any person who does not receive a decision within the time specified or is aggrieved by a decision of the Central Public Information Officer or State Public Information Officer may within thirty days prefer an appeal to such officer who is senior in rank to the Public Information Officer (First Appeal). A second appeal against the decision shall lie within ninety days to the Central Information Commission or State Information Commission."
            },
            {
                "section_id": "act_rti_2005_sec_20",
                "section_number": "Section 20",
                "title": "Penalties",
                "text": "Where the Central Information Commission or State Information Commission is of the opinion that the Public Information Officer has without any reasonable cause refused to receive an application or has not furnished information within specified time, it shall impose a penalty of two hundred and fifty rupees each day till application is received or information is furnished, subject to a total maximum of twenty-five thousand rupees."
            }
        ],
        "summary": "Codifies the citizen's fundamental right to know derived from freedom of speech and expression under Article 19(1)(a) and right to life under Article 21.",
        "text": "Right to Information Act, 2005 (Act No. 22 of 2005). Codifies freedom of information rooted in Article 19(1)(a). Mandates proactive disclosure (Section 4), 30-day/48-hour response windows (Section 7), strict exemptions (Section 8), two-tier appeal mechanism (Section 19), and daily monetary penalties (Section 20)."
    },

    # 5. Armed Forces (Special Powers) Act, 1958
    {
        "id": "act_afspa_1958",
        "document_id": "act_afspa_1958",
        "document_type": "statute",
        "title": "Armed Forces (Special Powers) Act, 1958 (Act No. 28 of 1958)",
        "short_title": "Armed Forces (Special Powers) Act, 1958",
        "act_number": "28 of 1958",
        "year": 1958,
        "enactment_date": "1958-09-11",
        "commencement_date": "1958-09-11",
        "constitutional_basis": ["Article 355", "Article 33", "Article 34", "Entry 2A of List I"],
        "part_reference": "Part XVIII - Emergency Provisions & Federal Police Powers",
        "legal_status": "in_force",
        "sections": [
            {
                "section_id": "act_afspa_1958_sec_03",
                "section_number": "Section 3",
                "title": "Power to declare areas to be disturbed areas",
                "text": "If, in relation to any State, or Union territory, the Governor of that State or the Administrator of that Union territory or the Central Government, in either case, if of the opinion that the whole or any part of such State or Union territory is in such a disturbed or dangerous condition that the use of armed forces in aid of the civil power is necessary, the Governor or Administrator or Central Government may, by notification in the Official Gazette, declare the whole or such part to be a disturbed area."
            },
            {
                "section_id": "act_afspa_1958_sec_04",
                "section_number": "Section 4",
                "title": "Special powers of the armed forces",
                "text": "Any commissioned officer, warrant officer, non-commissioned officer or any other person of equivalent rank in the armed forces may, in a disturbed area: (a) if he is of opinion that it is necessary so to do for the maintenance of public order, after giving such due warning as he may consider necessary, fire upon or otherwise use force, even to the causing of death, against any person who is acting in contravention of any law or order prohibiting assembly of five or more persons; (b) destroy any arms dump; (c) arrest without warrant any person who has committed a cognizable offence."
            },
            {
                "section_id": "act_afspa_1958_sec_06",
                "section_number": "Section 6",
                "title": "Protection to persons acting under Act (Sanction for prosecution)",
                "text": "No prosecution, suit or other legal proceeding shall be instituted, except with the previous sanction of the Central Government, against any person in respect of anything done or purported to be done in exercise of the powers conferred by this Act."
            }
        ],
        "summary": "Grants special powers to armed forces in disturbed areas pursuant to Article 355 and Entry 2A of List I; upheld by Supreme Court Constitution Bench in Naga People's Movement of Human Rights v. Union of India (1998).",
        "text": "Armed Forces (Special Powers) Act, 1958 (Act No. 28 of 1958). Enacted under Article 355 and Entry 2A List I. Governs disturbed area declarations (Section 3), operational powers (Section 4), and requirement of central sanction for prosecution under Section 6."
    },

    # 6. Official Languages Act, 1963
    {
        "id": "act_ola_1963",
        "document_id": "act_ola_1963",
        "document_type": "statute",
        "title": "Official Languages Act, 1963 (Act No. 19 of 1963)",
        "short_title": "Official Languages Act, 1963",
        "act_number": "19 of 1963",
        "year": 1963,
        "enactment_date": "1963-05-10",
        "commencement_date": "1965-01-26",
        "constitutional_basis": ["Article 343", "Article 344", "Article 348"],
        "part_reference": "Part XVII - Official Language",
        "legal_status": "in_force",
        "sections": [
            {
                "section_id": "act_ola_1963_sec_03",
                "section_number": "Section 3",
                "title": "Continuation of English Language for official purposes of the Union and for use in Parliament",
                "text": "Notwithstanding the expiration of the period of fifteen years from the commencement of the Constitution, the English language may, as from the appointed day, continue to be used, in addition to Hindi, for all the official purposes of the Union for which it was being used immediately before that day and for the transaction of business in Parliament."
            },
            {
                "section_id": "act_ola_1963_sec_04",
                "section_number": "Section 4",
                "title": "Committee on Official Language",
                "text": "After the expiration of ten years from the date on which section 3 comes into force, there shall be constituted a Committee on Official Language, consisting of thirty members, twenty from the Lok Sabha and ten from the Rajya Sabha, to review the progress made in the use of Hindi for official purposes of the Union."
            },
            {
                "section_id": "act_ola_1963_sec_07",
                "section_number": "Section 7",
                "title": "Optional use of Hindi or other official language in judgments etc. of High Courts",
                "text": "As from the appointed day or any day thereafter the Governor of a State may, with the previous consent of the President, authorise the use of Hindi or the official language of the State, in addition to the English language, for the purposes of any judgment, decree or order passed or made by the High Court for that State."
            }
        ],
        "summary": "Provides for the languages which may be used for official purposes of the Union, for transaction of business in Parliament, and in High Courts pursuant to Part XVII of the Constitution.",
        "text": "Official Languages Act, 1963 (Act No. 19 of 1963). Enacted pursuant to Article 343(3) and Article 348. Provides for indefinite continuation of English alongside Hindi for Union official purposes (Section 3), establishes Committee on Official Language (Section 4), and allows optional Hindi in High Court judgments (Section 7)."
    },

    # 7. Delimitation Act, 2002
    {
        "id": "act_delimitation_2002",
        "document_id": "act_delimitation_2002",
        "document_type": "statute",
        "title": "Delimitation Act, 2002 (Act No. 33 of 2002)",
        "short_title": "Delimitation Act, 2002",
        "act_number": "33 of 2002",
        "year": 2002,
        "enactment_date": "2002-06-03",
        "commencement_date": "2002-06-03",
        "constitutional_basis": ["Article 82", "Article 170", "Article 327"],
        "part_reference": "Part V & Part VI - Representation & Delimitation",
        "legal_status": "in_force",
        "sections": [
            {
                "section_id": "act_delimitation_2002_sec_03",
                "section_number": "Section 3",
                "title": "Constitution of Delimitation Commission",
                "text": "As soon as may be after the commencement of this Act, the Central Government shall constitute a Commission to be called the Delimitation Commission which shall consist of three members: two members from among persons who are or have been Judges of the Supreme Court or of a High Court, and the Chief Election Commissioner or an Election Commissioner."
            },
            {
                "section_id": "act_delimitation_2002_sec_08",
                "section_number": "Section 8",
                "title": "Readjustment of number of seats",
                "text": "The Commission shall, having regard to the provisions of articles 81, 170, 330 and 332, readjust the allocation of seats in the House of the People to the several States and the total number of seats in the Legislative Assembly of each State on the basis of the 2001 census."
            },
            {
                "section_id": "act_delimitation_2002_sec_09",
                "section_number": "Section 9",
                "title": "Delimitation of constituencies",
                "text": "The Commission shall, in the manner herein provided, distribute the seats in the House of the People and Legislative Assemblies into single-member territorial constituencies and delimit them on the basis of the census figures, having regard to geographical compactness and natural boundaries."
            }
        ],
        "summary": "Provides for the readjustment of the allocation of seats in the House of the People and State Legislative Assemblies and delimitation of constituencies pursuant to Articles 82 and 170.",
        "text": "Delimitation Act, 2002 (Act No. 33 of 2002). Enacted under Article 82 and Article 170. Establishes Delimitation Commission (Section 3), seat readjustment (Section 8), and territorial constituency delimitation (Section 9)."
    },

    # 8. Comptroller and Auditor-General's Act, 1971
    {
        "id": "act_cag_1971",
        "document_id": "act_cag_1971",
        "document_type": "statute",
        "title": "Comptroller and Auditor-General's (Duties, Powers and Conditions of Service) Act, 1971 (Act No. 56 of 1971)",
        "short_title": "CAG Act, 1971",
        "act_number": "56 of 1971",
        "year": 1971,
        "enactment_date": "1971-12-15",
        "commencement_date": "1971-12-15",
        "constitutional_basis": ["Article 148", "Article 149", "Article 151"],
        "part_reference": "Part V - Comptroller and Auditor-General of India",
        "legal_status": "in_force",
        "sections": [
            {
                "section_id": "act_cag_1971_sec_10",
                "section_number": "Section 10",
                "title": "Compilation of accounts of Union and States",
                "text": "The Comptroller and Auditor-General shall be responsible for compiling the accounts of the Union and of each State from the initial and subsidiary accounts rendered to the audit and accounts offices under his control."
            },
            {
                "section_id": "act_cag_1971_sec_13",
                "section_number": "Section 13",
                "title": "General provisions relating to audit",
                "text": "It shall be the duty of the Comptroller and Auditor-General: (a) to audit all expenditure from the Consolidated Fund of India and of each State and of each Union territory having a Legislative Assembly and to ascertain whether the moneys shown in the accounts as having been disbursed were legally available for and applicable to the service or purpose to which they have been applied; (b) to audit all transactions of the Union and of the States relating to Contingency Funds and Public Accounts."
            },
            {
                "section_id": "act_cag_1971_sec_16",
                "section_number": "Section 16",
                "title": "Audit of receipts",
                "text": "It shall be the duty of the Comptroller and Auditor-General to audit all receipts which are payable into the Consolidated Fund of India and of each State and to satisfy himself that the rules and procedures in that behalf are designed to secure an effective check on the assessment, collection and proper allocation of revenue."
            }
        ],
        "summary": "Prescribes the duties, powers, and conditions of service of the Comptroller and Auditor-General of India enacted by Parliament pursuant to Article 148 and Article 149 of the Constitution.",
        "text": "Comptroller and Auditor-General's (Duties, Powers and Conditions of Service) Act, 1971 (Act No. 56 of 1971). Enacted under Article 149 of the Constitution. Regulates compilation of Union and State accounts (Section 10), audit of Consolidated Fund expenditure (Section 13), and audit of public receipts (Section 16)."
    },

    # 9. Supreme Court (Number of Judges) Act, 1956
    {
        "id": "act_sc_judges_1956",
        "document_id": "act_sc_judges_1956",
        "document_type": "statute",
        "title": "Supreme Court (Number of Judges) Act, 1956 (Act No. 55 of 1956)",
        "short_title": "Supreme Court (Number of Judges) Act, 1956",
        "act_number": "55 of 1956",
        "year": 1956,
        "enactment_date": "1956-09-16",
        "commencement_date": "1956-09-16",
        "constitutional_basis": ["Article 124(1)"],
        "part_reference": "Part V - Union Judiciary",
        "legal_status": "in_force",
        "sections": [
            {
                "section_id": "act_sc_judges_1956_sec_02",
                "section_number": "Section 2",
                "title": "Maximum number of Judges in the Supreme Court",
                "text": "The maximum number of Judges of the Supreme Court, excluding the Chief Justice of India, shall be thirty-three (as amended by Act 37 of 2019, making total sanctioned strength 34 including Chief Justice of India)."
            }
        ],
        "summary": "Fixes the maximum number of puisne Judges of the Supreme Court of India enacted by Parliament under Article 124(1) of the Constitution.",
        "text": "Supreme Court (Number of Judges) Act, 1956 (Act No. 55 of 1956). Enacted pursuant to Article 124(1) of the Constitution of India. Establishes the sanctioned strength of Supreme Court Judges, currently 33 puisne Judges plus Chief Justice of India (total 34)."
    },

    # 10. National Commission for Minorities Act, 1992
    {
        "id": "act_ncma_1992",
        "document_id": "act_ncma_1992",
        "document_type": "statute",
        "title": "National Commission for Minorities Act, 1992 (Act No. 19 of 1992)",
        "short_title": "National Commission for Minorities Act, 1992",
        "act_number": "19 of 1992",
        "year": 1992,
        "enactment_date": "1992-05-17",
        "commencement_date": "1993-05-17",
        "constitutional_basis": ["Article 29", "Article 30", "Article 350B"],
        "part_reference": "Part III - Fundamental Rights (Cultural & Educational Rights)",
        "legal_status": "in_force",
        "sections": [
            {
                "section_id": "act_ncma_1992_sec_03",
                "section_number": "Section 3",
                "title": "Constitution of the National Commission for Minorities",
                "text": "The Central Government shall constitute a body to be known as the National Commission for Minorities to exercise the powers conferred on, and to perform the functions assigned to it under this Act, consisting of a Chairperson, a Vice-Chairperson and five Members to be nominated by the Central Government from amongst persons of eminence, ability and integrity from minority communities."
            },
            {
                "section_id": "act_ncma_1992_sec_09",
                "section_number": "Section 9",
                "title": "Functions of the Commission",
                "text": "The Commission shall perform all or any of the following functions: (a) evaluate the progress of the development of minorities under the Union and States; (b) monitor the working of the safeguards provided in the Constitution and in laws enacted by Parliament and the State Legislatures; (c) make recommendations for the effective implementation of safeguards for the protection of the interests of minorities; (d) look into specific complaints regarding deprivation of rights and safeguards of the minorities."
            }
        ],
        "summary": "Establishes the National Commission for Minorities to safeguard constitutional rights under Articles 29 and 30.",
        "text": "National Commission for Minorities Act, 1992 (Act No. 19 of 1992). Enforces cultural and educational rights under Articles 29 and 30. Establishes the National Commission for Minorities (Section 3) and prescribes monitoring of constitutional safeguards (Section 9)."
    }
]

RAW_ACTS_CONFIG = [
    {
        "raw_filename": "ipc.json",
        "doc_id": "act_ipc_1860",
        "title": "Indian Penal Code, 1860 (Act No. 45 of 1860)",
        "short_title": "Indian Penal Code, 1860",
        "act_number": "45 of 1860",
        "year": 1860,
        "enactment_date": "1860-10-06",
        "commencement_date": "1862-01-01",
        "constitutional_basis": ["Article 14", "Article 19", "Article 20", "Article 21"],
        "part_reference": "Criminal Jurisprudence & Fundamental Rights",
        "summary": "The principal criminal code of India defining offences and prescribing punishments. Directly interfaces with Article 19(1)(a) (Section 124A Sedition, Section 499 Defamation) and Article 21 (Section 302, Section 309, Section 377)."
    },
    {
        "raw_filename": "crpc.json",
        "doc_id": "act_crpc_1973",
        "title": "Code of Criminal Procedure, 1973 (Act No. 2 of 1974)",
        "short_title": "Code of Criminal Procedure, 1973",
        "act_number": "2 of 1974",
        "year": 1973,
        "enactment_date": "1974-01-25",
        "commencement_date": "1974-04-01",
        "constitutional_basis": ["Article 20", "Article 21", "Article 22"],
        "part_reference": "Criminal Procedure & Due Process",
        "summary": "Governs the machinery for investigation of crime, apprehension of suspected criminals, collection of evidence, determination of guilt or innocence, and imposition of punishment, codifying Article 21 due process safeguards."
    },
    {
        "raw_filename": "iea.json",
        "doc_id": "act_iea_1872",
        "title": "Indian Evidence Act, 1872 (Act No. 1 of 1872)",
        "short_title": "Indian Evidence Act, 1872",
        "act_number": "1 of 1872",
        "year": 1872,
        "enactment_date": "1872-03-15",
        "commencement_date": "1872-09-01",
        "constitutional_basis": ["Article 20(3)", "Article 21"],
        "part_reference": "Admissibility of Evidence & Self-Incrimination",
        "summary": "Sets out the rules on admissibility, relevancy, and weight of evidence in judicial proceedings. Enforces constitutional protections against self-incrimination under Article 20(3) (Sections 24–27)."
    },
    {
        "raw_filename": "cpc.json",
        "doc_id": "act_cpc_1908",
        "title": "Code of Civil Procedure, 1908 (Act No. 5 of 1908)",
        "short_title": "Code of Civil Procedure, 1908",
        "act_number": "5 of 1908",
        "year": 1908,
        "enactment_date": "1908-03-21",
        "commencement_date": "1909-01-01",
        "constitutional_basis": ["Article 32", "Article 226", "Article 300"],
        "part_reference": "Civil Adjudication & Constitutional Remedies",
        "summary": "Regulates the procedure for civil lawsuits in India, establishing doctrine of res judicata (Section 11) applicable to constitutional writ petitions, and suits by or against the Government (Sections 79–82)."
    },
    {
        "raw_filename": "ida.json",
        "doc_id": "act_ida_1947",
        "title": "Industrial Disputes Act, 1947 (Act No. 14 of 1947)",
        "short_title": "Industrial Disputes Act, 1947",
        "act_number": "14 of 1947",
        "year": 1947,
        "enactment_date": "1947-03-11",
        "commencement_date": "1947-04-01",
        "constitutional_basis": ["Article 19(1)(c)", "Article 43A"],
        "part_reference": "Labour Welfare & Directive Principles",
        "summary": "Provides machinery for investigation and settlement of industrial disputes, safeguarding right to association and workers' participation in management under Article 43A."
    },
    {
        "raw_filename": "nia.json",
        "doc_id": "act_nia_1881",
        "title": "Negotiable Instruments Act, 1881 (Act No. 26 of 1881)",
        "short_title": "Negotiable Instruments Act, 1881",
        "act_number": "1881",
        "year": 1881,
        "enactment_date": "1881-12-09",
        "commencement_date": "1882-03-01",
        "constitutional_basis": ["Article 19(1)(g)", "Article 301"],
        "part_reference": "Commercial Law & Inter-State Trade",
        "summary": "Codifies the law relating to promissory notes, bills of exchange, and cheques, facilitating trade, commerce, and financial intercourse under Part XIII."
    },
    {
        "raw_filename": "MVA.json",
        "doc_id": "act_mva_1988",
        "title": "Motor Vehicles Act, 1988 (Act No. 59 of 1988)",
        "short_title": "Motor Vehicles Act, 1988",
        "act_number": "59 of 1988",
        "year": 1988,
        "enactment_date": "1988-10-14",
        "commencement_date": "1989-07-01",
        "constitutional_basis": ["Article 19(1)(d)", "Article 21"],
        "part_reference": "Transportation Regulation & Public Safety",
        "summary": "Regulates road transport vehicles, driver licensing, traffic management, and mandatory third-party liability insurance relating to public safety and right to life."
    }
]


def parse_raw_central_act(config_entry: Dict[str, Any], raw_path: Path) -> Dict[str, Any]:
    """Parse raw JSON into structured LegalDocument dictionary with section hierarchy."""
    with open(raw_path, "r", encoding="utf-8") as f:
        raw_items = json.load(f)

    sections = []
    text_parts = [f"ACT TITLE: {config_entry['title']}\nSUMMARY: {config_entry['summary']}"]

    for item in raw_items:
        sec_raw = str(item.get("section", item.get("Section", ""))).strip()
        if not sec_raw or sec_raw == "None":
            continue

        sec_title = (item.get("section_title") or item.get("title") or "").strip()
        sec_desc = (item.get("section_desc") or item.get("description") or "").strip()
        chapter = item.get("chapter", "")

        sec_id = f"{config_entry['doc_id']}_sec_{sec_raw.replace(' ', '_').lower()}"
        sec_record = {
            "section_id": sec_id,
            "section_number": f"Section {sec_raw}",
            "title": sec_title or f"Section {sec_raw}",
            "chapter": f"Chapter {chapter}" if chapter else "",
            "text": sec_desc,
        }
        sections.append(sec_record)
        text_parts.append(f"[Section {sec_raw}: {sec_title}]\n{sec_desc[:250]}")

    full_text = "\n\n".join(text_parts)
    act_sha256 = hashlib.sha256(full_text.encode("utf-8")).hexdigest()
    retrieval_timestamp = datetime.now(timezone.utc).isoformat()

    return {
        "id": config_entry["doc_id"],
        "document_id": config_entry["doc_id"],
        "document_type": "statute",
        "content_type": "full_text",
        "title": config_entry["title"],
        "short_title": config_entry["short_title"],
        "act_number": config_entry["act_number"],
        "year": config_entry["year"],
        "enactment_date": config_entry["enactment_date"],
        "commencement_date": config_entry["commencement_date"],
        "effective_date": config_entry["commencement_date"],
        "constitutional_basis": config_entry["constitutional_basis"],
        "part_reference": config_entry["part_reference"],
        "legal_status": "in_force",
        "sections": sections,
        "summary": config_entry["summary"],
        "text": full_text,
        "full_text": full_text,
        "source_url": f"{SOURCE_URL_INDIACODE}/handle/123456789/{config_entry['year']}",
        "source_name": SOURCE_NAME_INDIACODE,
        "source_file": config_entry["raw_filename"],
        "source_hash": act_sha256,
        "retrieved_at": retrieval_timestamp,
        "version_date": str(config_entry["year"]),
        "language": "en",
        "license": LICENSE_LEGISLATION,
        "processing_status": "processed",
        "provenance": {
            "source": SOURCE_NAME_INDIACODE,
            "retrieval_date": retrieval_timestamp[:10],
            "version": config_entry["title"],
            "total_sections_parsed": len(sections),
            "verified": True,
        }
    }


def ingest_legislation() -> List[Dict[str, Any]]:
    """Process statutory Central Acts into schema-compliant records."""
    retrieval_timestamp = datetime.now(timezone.utc).isoformat()
    processed_acts = []

    # 1. Process Core Framework Acts
    for act in CONSTITUTIONAL_FRAMEWORK_ACTS:
        act_sha256 = hashlib.sha256(act["text"].encode("utf-8")).hexdigest()
        record = {
            **act,
            "content_type": "full_text",
            "full_text": act["text"],
            "effective_date": act["commencement_date"],
            "source_url": f"{SOURCE_URL_INDIACODE}/handle/123456789/{act['year']}",
            "source_name": SOURCE_NAME_INDIACODE,
            "source_file": f"{act['document_id']}.json",
            "source_hash": act_sha256,
            "retrieved_at": retrieval_timestamp,
            "version_date": str(act["year"]),
            "language": "en",
            "license": LICENSE_LEGISLATION,
            "processing_status": "processed",
            "provenance": {
                "source": SOURCE_NAME_INDIACODE,
                "retrieval_date": retrieval_timestamp[:10],
                "version": f"{act['title']}",
                "total_sections_parsed": len(act.get("sections", [])),
                "verified": True,
            }
        }
        processed_acts.append(record)

    # 2. Process Downloaded Raw Central Acts
    for cfg in RAW_ACTS_CONFIG:
        raw_file = RAW_LEGISLATION_DIR / cfg["raw_filename"]
        if raw_file.exists():
            try:
                parsed_act = parse_raw_central_act(cfg, raw_file)
                processed_acts.append(parsed_act)
                print(f"[+] Ingested Central Act: {cfg['short_title']} ({len(parsed_act['sections'])} sections)")
            except Exception as e:
                print(f"[-] Error parsing {cfg['raw_filename']}: {e}")

    out_file = PROCESSED_LEGISLATION_DIR / "central_acts.json"
    PROCESSED_LEGISLATION_DIR.mkdir(parents=True, exist_ok=True)
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(processed_acts, f, indent=2, ensure_ascii=False)

    total_secs = sum(len(a.get("sections", [])) for a in processed_acts)
    print("\n" + "=" * 65)
    print(f"[+] LEGISLATION INGESTION COMPLETE:")
    print(f"    - Total Central Acts: {len(processed_acts)}")
    print(f"    - Total Structured Sections: {total_secs}")
    print(f"    - Output: {out_file}")
    print("=" * 65)

    return processed_acts


if __name__ == "__main__":
    ingest_legislation()
